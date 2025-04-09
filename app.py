from flask import Flask, request, jsonify, render_template, send_file,send_from_directory
import os, json, logging
from modules.io.utils import read_json, write_json, read_csv, write_csv
from modules.reconciler.reconciliation import conciliar_extrato_contatos
from modules.reconciler.consultation import consultar_cnpjs_em_massa
from modules.contact_matcher.link import link_full_cnpj_to_contacts, save_links_csv
from modules.contact_matcher.aliases import integrate_contact_aliases
from modules.contact_matcher.enrich import process_contact_enrichment
from modules.contact_matcher.associate import associate_transactions_with_contacts
import time

app = Flask(__name__)
app.config['DEBUG'] = False
@app.after_request
def add_csp_headers(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self';"
    )
    return response


# Configuração de logging
def setup_logging():
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=log_format, filename='app.log', filemode='a')
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(logging.Formatter(log_format))
    logging.getLogger('').addHandler(console)

setup_logging()

# Paths e configurações
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Caminho padrão para extrato HTML (Sicoob)
PATH_EXTRATO_HTML = os.path.join(BASE_DIR, "receipt", "extrato_sicoob3.html")
# Caminho padrão para extrato OFX (BB)
PATH_EXTRATO_OFX = os.path.join(BASE_DIR, "receipt", "extrato_bb.ofx")
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

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []  # Pode ser substituído por dados de teste

    if len(data) >= 2:
        # data_sem_saldo = data[:-2]
        # saldos = data[-2:]
        
        data_sem_saldo = data
        saldos = data
    else:
        data_sem_saldo = data
        saldos = []

    tipos = sorted({
        tipo 
        for tipos_list in config_json.get("tipos_por_transacao", {}).values() 
        for tipo in tipos_list
    })

    return render_template(
        "dashboard.html",
        config_json=config_json,
        regras_json=regras_json,
        data=data_sem_saldo,
        tipos=tipos,
        saldos=saldos,
        version=int(time.time())
    )
# Rota para disparar o pipeline
@app.route('/process', methods=['POST'])
def process_pipeline():
    try:
        logging.info("Iniciando pipeline de processamento...")

        # Etapa 1: Integração de aliases usando a interface do módulo de IO
        if os.path.exists(PATH_ALIAS_CSV):
            # Tenta ler o CSV de contatos usando a interface do IO; se não existir, a função deve retornar uma estrutura vazia
            contatos_df = read_csv(PATH_CONTATOS_CSV, sep=";", json_columns=["socios"]) if os.path.exists(PATH_CONTATOS_CSV) else None
            # Caso não haja contatos lidos, inicializa com uma estrutura vazia (a interface do IO deve cuidar disso)
            if contatos_df is None:
                contatos_df = []
            contatos_df = integrate_contact_aliases(PATH_ALIAS_CSV, contatos_df)
            write_csv(contatos_df, PATH_CONTATOS_CSV, sep=";", encoding="utf-8-sig", json_columns=["socios"])
            logging.info("Contatos atualizados com aliases integrados.")
        else:
            logging.info("Arquivo de aliases não encontrado; integração não realizada.")

        # Etapa 2: Parsing do extrato bancário
        banco = request.form.get("banco", "sicoob")
        if banco == "bb":
            caminho_arquivo = PATH_EXTRATO_OFX
            if not os.path.exists(caminho_arquivo):
                raise FileNotFoundError(f"Arquivo OFX não encontrado em {caminho_arquivo}")
            from modules.parser.banks.bb import BBParser
            parser = BBParser(caminho_arquivo)
        elif banco == "sicoob":
            caminho_arquivo = PATH_EXTRATO_HTML
            from modules.parser.banks.sicoob import SicoobParser
            parser = SicoobParser(caminho_arquivo)
        else:
            raise ValueError(f"Banco '{banco}' não suportado.")

        extrato = parser.parse_statement()
        extrato_path = os.path.join(PATH_TEMP_FOLDER, f"parsed_extrato_{banco}.json")
        write_json(extrato, extrato_path, indent=4)
        logging.info("Extrato parseado com sucesso.")

        # Etapa 3: Enriquecimento dos lançamentos (utilize somente o objeto 'parser')
        enriched_transactions = parser.parse_transactions(extrato)
        extrato["enriched_transactions"] = enriched_transactions
        enriched_path = os.path.join(PATH_TEMP_FOLDER, f"parsed_extrato_{banco}_enriched.json")
        write_json(extrato, enriched_path, indent=4)
        logging.info("Lançamentos enriquecidos.")

        # Etapa 4: Conciliação com contatos
        conciliated = conciliar_extrato_contatos(enriched_transactions, caminho_contatos_csv=PATH_CONTATOS_CSV)
        extrato["conciliated_transactions"] = conciliated
        conciliated_path = os.path.join(PATH_TEMP_FOLDER, f"parsed_extrato_{banco}_conciliated.json")
        write_json(extrato, conciliated_path, indent=4)
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
        candidate_links_path = os.path.join(PATH_TEMP_FOLDER, "candidate_links.json")
        write_json(candidate_links, candidate_links_path, indent=4)
        save_links_csv(candidate_links, os.path.join(PATH_TEMP_FOLDER, "candidate_links.csv"))
        logging.info("Vínculos candidatos gerados e exportados.")

        # Etapa 7: Enriquecimento dos contatos com dados dos CNPJs
        process_contact_enrichment(PATH_CNPJ_CACHE, PATH_CONTATOS_CSV)
        logging.info("Contatos enriquecidos com dados dos CNPJs.")

        # Etapa 8: Associação de transações aos contatos
        contatos_df = read_csv(PATH_CONTATOS_CSV, sep=";", json_columns=["socios"])
        associated_transactions = associate_transactions_with_contacts(conciliated, contatos_df)
        extrato["associated_transactions"] = associated_transactions
        associated_path = os.path.join(PATH_TEMP_FOLDER, "extrato_conciliated_with_contacts.json")
        write_json(associated_transactions, associated_path, indent=4)
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

import json

@app.route('/rules_state/save', methods=['POST'])
def save_rules_state():
    rules_data = request.get_json()
    temp_path = RULES_PATH
    with open(temp_path, "w") as f:
        json.dump(rules_data, f, indent=2)
    return jsonify({"status": "ok", "message": "Estado das regras salvo com sucesso"})

@app.route('/rules_state/load', methods=['GET'])
def load_rules_state():
    temp_path = os.path.join(RULES_PATH, "rules.json")
    if not os.path.exists(temp_path):
        return jsonify({"error": "Estado das regras não encontrado"}), 404
    return read_json(temp_path)

@app.route('/rules_state/clean', methods=['POST'])
def clean_rules_state():
    temp_path = os.path.join(RULES_PATH, "saved_rules.json")
    if os.path.exists(temp_path):
        os.remove(temp_path)
    return jsonify({"status": "ok", "message": "Estado das regras limpo com sucesso"})

@app.route('/data', methods=['GET'])
def get_data():
    if os.path.exists(DATA_FILE):
        return read_json(DATA_FILE)
    else:
        return jsonify([]), 404

@app.route("/upload_html", methods=["POST"])
def upload_html():
    file = request.files.get("extrato_file")
    banco = request.form.get("banco")

    if not file or not banco:
        return jsonify({"status": "erro", "message": "Arquivo ou banco não enviado."}), 400

    filename = "extrato." + file.filename.split('.')[-1]
    path = os.path.join(PATH_TEMP_FOLDER, filename)
    file.save(path)

    if banco == "sicoob":
        global PATH_EXTRATO_HTML
        PATH_EXTRATO_HTML = path
    elif banco == "bb":
        global PATH_EXTRATO_OFX
        PATH_EXTRATO_OFX = path

    return jsonify({"status": "sucesso", "message": f"Arquivo para {banco} salvo com sucesso."})

# Rota para servir arquivos do diretório "entity"
@app.route('/entity/<path:filename>')
def entity_files(filename):
    return send_from_directory('entity', filename)

@app.route('/api/save-contacts', methods=['POST'])
def save_contacts():
    try:
        # Obtém o CSV enviado (em texto)
        csv_data = request.data.decode('utf-8')
        
        # Salva o conteúdo no arquivo de contatos
        with open(PATH_CONTATOS_CSV, 'w', encoding='utf-8-sig') as f:
            f.write(csv_data)
        
        app.logger.info("Contatos salvos com sucesso no arquivo %s", PATH_CONTATOS_CSV)
        return "Contatos salvos com sucesso", 200
    except Exception as e:
        app.logger.exception("Erro ao salvar contatos:")
        return str(e), 500
    
@app.route('/static/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('static/js', filename, mimetype='application/javascript')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010, debug=True)
