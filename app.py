from flask import Flask, request, jsonify, render_template, send_file
import os, json, logging
from modules.io.utils import read_json, write_json, read_csv, write_csv
from modules.parser.banks.sicoob import SicoobParser
from modules.reconciler.reconciliation import conciliar_extrato_contatos
from modules.reconciler.consultation import consultar_cnpjs_em_massa
from modules.contact_matcher.link import link_full_cnpj_to_contacts, save_links_csv
from modules.contact_matcher.aliases import integrate_contact_aliases
from modules.contact_matcher.enrich import process_contact_enrichment
from modules.contact_matcher.associate import associate_transactions_with_contacts

app = Flask(__name__)
app.config['DEBUG'] = False

# Configuração de logging
def setup_logging():
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_format, filename='app.log', filemode='a')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(log_format))
    logging.getLogger('').addHandler(console)

setup_logging()

# Paths e configurações
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PATH_EXTRATO_HTML = os.path.join(BASE_DIR, "receipt", "extrato_sicoob3.html")
PATH_TEMP_FOLDER = os.path.join(BASE_DIR, "db", "temp")
PATH_CNPJ_CACHE = os.path.join(BASE_DIR, "db", "cnpj_cache.json")
PATH_CONTATOS_CSV = os.path.join(BASE_DIR, "entity", "contatos_atualizados.csv")
PATH_ALIAS_CSV = os.path.join(BASE_DIR, "entity", "pessoas_cpf_MMG25_corrigido.csv")
CONFIG_PATH = os.path.join(BASE_DIR, "config", "categorias_por_tipo.json")
RULES_PATH = os.path.join(BASE_DIR, "config", "rules.json")
DATA_FILE = os.path.join(PATH_TEMP_FOLDER, "extrato_conciliated_with_contacts.json")

os.makedirs(PATH_TEMP_FOLDER, exist_ok=True)

# Rota para renderizar o relatório dinamicamente
@app.route('/')
def index():
    # Carrega configuração e regras
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, encoding="utf-8") as f:
            config_json = json.load(f)
    else:
        config_json = {}

    if os.path.exists(RULES_PATH):
        with open(RULES_PATH, encoding="utf-8") as f:
            regras_json = json.load(f)
    else:
        regras_json = []

    # Carrega os dados do relatório (JSON gerado pelo pipeline)
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []  # Pode ser substituído por dados de teste

    # Extrai os tipos para os selects a partir da configuração
    tipos = sorted({
        tipo 
        for tipos_list in config_json.get("tipos_por_transacao", {}).values() 
        for tipo in tipos_list
    })

    return render_template("dashboard.html", config_json=config_json, regras_json=regras_json, data=data, tipos=tipos)


# Rota para disparar o pipeline
@app.route('/process', methods=['POST'])
def process_pipeline():
    try:
        logging.info("Iniciando pipeline de processamento...")

        # Etapa 1: Integração de aliases
        if os.path.exists(PATH_ALIAS_CSV):
            if os.path.exists(PATH_CONTATOS_CSV):
                contatos_df = read_csv(PATH_CONTATOS_CSV, sep=";", json_columns=["socios"])
            else:
                import pandas as pd
                contatos_df = pd.DataFrame(columns=["cpf_cnpj", "nome", "razao_social", "nome_fantasia", "socios"])
            contatos_df = integrate_contact_aliases(PATH_ALIAS_CSV, contatos_df)
            write_csv(contatos_df, PATH_CONTATOS_CSV, sep=";", encoding="utf-8-sig", json_columns=["socios"])
            logging.info("Contatos atualizados com aliases integrados.")
        else:
            logging.info("Arquivo de aliases não encontrado; integração não realizada.")

        # Etapa 2: Parsing do extrato bancário
        sicoob_parser = SicoobParser(PATH_EXTRATO_HTML)
        extrato = sicoob_parser.parse_statement()
        write_json(extrato, os.path.join(PATH_TEMP_FOLDER, "parsed_extrato_sicoob.json"), indent=4)
        logging.info("Extrato parseado com sucesso.")

        # Etapa 3: Enriquecimento dos lançamentos
        enriched_transactions = sicoob_parser.parse_transactions(extrato)
        extrato["enriched_transactions"] = enriched_transactions
        write_json(extrato, os.path.join(PATH_TEMP_FOLDER, "parsed_extrato_sicoob_enriched.json"), indent=4)
        logging.info("Lançamentos enriquecidos.")

        # Etapa 4: Conciliação com contatos
        conciliated = conciliar_extrato_contatos(enriched_transactions, caminho_contatos_csv=PATH_CONTATOS_CSV)
        extrato["conciliated_transactions"] = conciliated
        write_json(extrato, os.path.join(PATH_TEMP_FOLDER, "parsed_extrato_sicoob_conciliated.json"), indent=4)
        logging.info("Lançamentos conciliados com contatos.")

        # Etapa 5: Consulta de CNPJs em massa
        consultar_cnpjs_em_massa(conciliated, caminho_cnpj_api_csv=PATH_CNPJ_CACHE, wait_time=2)
        logging.info("Consulta massiva de CNPJs concluída.")

        # Etapa 6: Vinculação usando nome fantasia, razão social e sócios
        cnpj_cache = read_json(PATH_CNPJ_CACHE)
        contatos_df = read_csv(PATH_CONTATOS_CSV, sep=";", json_columns=["socios"])
        candidate_links = []
        for cnpj, data in cnpj_cache.items():
            if isinstance(data, dict):
                candidate_links.extend(link_full_cnpj_to_contacts(data, contatos_df))
        write_json(candidate_links, os.path.join(PATH_TEMP_FOLDER, "candidate_links.json"), indent=4)
        save_links_csv(candidate_links, os.path.join(PATH_TEMP_FOLDER, "candidate_links.csv"))
        logging.info("Vínculos candidatos gerados e exportados.")

        # Etapa 7: Enriquecimento dos contatos com dados dos CNPJs
        process_contact_enrichment(PATH_CNPJ_CACHE, PATH_CONTATOS_CSV)
        logging.info("Contatos enriquecidos com dados dos CNPJs.")

        # Etapa 8: Associação de transações aos contatos
        contatos_df = read_csv(PATH_CONTATOS_CSV, sep=";", json_columns=["socios"])
        associated_transactions = associate_transactions_with_contacts(conciliated, contatos_df)
        extrato["associated_transactions"] = associated_transactions
        write_json(associated_transactions, os.path.join(PATH_TEMP_FOLDER, "extrato_conciliated_with_contacts.json"), indent=4)
        logging.info("Transações associadas a contatos.")

        return jsonify({"status": "sucesso", "message": "Pipeline executado com sucesso."})
    except Exception as e:
        logging.exception("Erro ao processar pipeline.")
        return jsonify({"status": "erro", "message": str(e)}), 500

# Rotas para gerenciamento de regras (CRUD)
@app.route('/rules', methods=['GET', 'POST', 'PUT', 'DELETE'])
def rules():
    if request.method == 'GET':
        if os.path.exists(RULES_PATH):
            with open(RULES_PATH, encoding="utf-8") as f:
                rules_data = f.read()
            return rules_data, 200, {'Content-Type': 'application/json'}
        else:
            return jsonify([])
    elif request.method == 'POST':
        nova_regra = request.get_json()
        rules_list = []
        if os.path.exists(RULES_PATH):
            rules_list = read_json(RULES_PATH)
        rules_list.append(nova_regra)
        write_json(rules_list, RULES_PATH, indent=4)
        return jsonify(nova_regra), 201
    elif request.method == 'PUT':
        regra_atualizada = request.get_json()
        index = regra_atualizada.get("index")
        if index is None:
            return jsonify({"error": "Índice não informado."}), 400
        rules_list = read_json(RULES_PATH)
        if index < 0 or index >= len(rules_list):
            return jsonify({"error": "Índice inválido."}), 400
        rules_list[index] = regra_atualizada
        write_json(rules_list, RULES_PATH, indent=4)
        return jsonify(regra_atualizada), 200
    elif request.method == 'DELETE':
        index = request.args.get("index", type=int)
        if index is None:
            return jsonify({"error": "Índice não informado."}), 400
        rules_list = read_json(RULES_PATH)
        if index < 0 or index >= len(rules_list):
            return jsonify({"error": "Índice inválido."}), 400
        removed = rules_list.pop(index)
        write_json(rules_list, RULES_PATH, indent=4)
        return jsonify(removed), 200

# Rota para exportar CSV
@app.route('/export/csv', methods=['GET'])
def export_csv():
    try:
        csv_path = os.path.join(PATH_TEMP_FOLDER, "relatorio_transacoes.csv")
        if os.path.exists(csv_path):
            return send_file(csv_path, as_attachment=True)
        else:
            return jsonify({"error": "Arquivo CSV não encontrado."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Rotas para gerenciamento de estado
@app.route('/state/save', methods=['POST'])
def save_state():
    state_data = request.get_json()
    temp_path = os.path.join(PATH_TEMP_FOLDER, "saved_state.json")
    write_json(state_data, temp_path, indent=2)
    return jsonify({"status": "ok", "message": "Estado salvo com sucesso"})

@app.route('/state/load', methods=['GET'])
def load_state():
    temp_path = os.path.join(PATH_TEMP_FOLDER, "saved_state.json")
    if not os.path.exists(temp_path):
        return jsonify({"error": "Estado não encontrado"}), 404
    return read_json(temp_path)

@app.route('/state/clean', methods=['POST'])
def clean_state():
    temp_path = os.path.join(PATH_TEMP_FOLDER, "saved_state.json")
    if os.path.exists(temp_path):
        os.remove(temp_path)
    return jsonify({"status": "ok", "message": "Estado limpo com sucesso"})

@app.route('/rules_state/save', methods=['POST'])
def save_rules_state():
    rules_data = request.get_json()
    temp_path = os.path.join(PATH_TEMP_FOLDER, "saved_rules.json")
    write_json(rules_data, temp_path, indent=2)
    return jsonify({"status": "ok", "message": "Estado das regras salvo com sucesso"})

@app.route('/rules_state/load', methods=['GET'])
def load_rules_state():
    temp_path = os.path.join(PATH_TEMP_FOLDER, "saved_rules.json")
    if not os.path.exists(temp_path):
        return jsonify({"error": "Estado das regras não encontrado"}), 404
    return read_json(temp_path)

@app.route('/rules_state/clean', methods=['POST'])
def clean_rules_state():
    temp_path = os.path.join(PATH_TEMP_FOLDER, "saved_rules.json")
    if os.path.exists(temp_path):
        os.remove(temp_path)
    return jsonify({"status": "ok", "message": "Estado das regras limpo com sucesso"})

@app.route('/upload_html', methods=['POST'])
def upload_html():
    if 'html_file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado."}), 400
    file = request.files['html_file']
    if file.filename == "":
        return jsonify({"error": "Nome do arquivo vazio."}), 400
    if not file.filename.lower().endswith('.html'):
        return jsonify({"error": "O arquivo deve ser um HTML."}), 400
    # Salva o arquivo no caminho configurado
    file.save(PATH_EXTRATO_HTML)
    return jsonify({"status": "ok", "message": "Arquivo HTML carregado com sucesso."})

@app.route('/data', methods=['GET'])
def get_data():
    if os.path.exists(DATA_FILE):
        return read_json(DATA_FILE)
    else:
        return jsonify([]), 404



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)