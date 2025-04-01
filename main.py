import os
import logging
import pandas as pd

# Funções de I/O
from modules.io.utils import read_json, write_json, read_csv, write_csv

# Parser bancário
from modules.parser.banks.sicoob import SicoobParser

# Conciliação e consulta CNPJ
from modules.reconciler.reconciliation import conciliar_extrato_contatos
from modules.reconciler.consultation import consultar_cnpjs_em_massa

# Vinculação e enriquecimento
from modules.contact_matcher.link import link_full_cnpj_to_contacts, save_links_csv
from modules.contact_matcher.aliases import integrate_contact_aliases
from modules.contact_matcher.enrich import process_contact_enrichment
from modules.contact_matcher.associate import associate_transactions_with_contacts

# Geração de relatório via Jinja2
from modules.report_generator.jinja_exporter import export_jinja_report
def setup_logging():
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=log_format, filename='app.log', filemode='a')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(log_format))
    logging.getLogger('').addHandler(console)

def main():
    setup_logging()
    logging.info("Iniciando pipeline de processamento...")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    path_extrato_html = os.path.join(base_dir, "receipt", "extrato_sicoob3.html")
    path_temp_folder = os.path.join(base_dir, "db", "temp")
    path_cnpj_cache = os.path.join(base_dir, "db", "cnpj_cache.json")
    path_contatos_csv = os.path.join(base_dir, "entity", "contatos_atualizados.csv")
    path_alias_csv = os.path.join(base_dir, "entity", "pessoas_cpf_MMG25_corrigido.csv")
    config_path = os.path.join(base_dir, "config", "categorias_por_tipo.json")

    os.makedirs(path_temp_folder, exist_ok=True)

    # --- Etapa 1: Integração de aliases ---
    if os.path.exists(path_alias_csv):
        contatos_df = (read_csv(path_contatos_csv, sep=";", json_columns=["socios"])
                       if os.path.exists(path_contatos_csv)
                       else pd.DataFrame(columns=["cpf_cnpj", "nome", "razao_social", "nome_fantasia", "socios"]))
        contatos_df = integrate_contact_aliases(path_alias_csv, contatos_df)
        write_csv(contatos_df, path_contatos_csv, sep=";", encoding="utf-8-sig", json_columns=["socios"])
        logging.info("Contatos atualizados com aliases integrados.")
    else:
        logging.info("Arquivo de aliases não encontrado; integração não realizada.")

    # --- Etapa 2: Parsing do extrato bancário ---
    sicoob_parser = SicoobParser(path_extrato_html)
    extrato = sicoob_parser.parse_statement()
    write_json(extrato, os.path.join(path_temp_folder, "parsed_extrato_sicoob.json"), indent=4)
    logging.info("Extrato parseado com sucesso.")

    # --- Etapa 3: Enriquecimento dos lançamentos ---
    enriched_transactions = sicoob_parser.parse_transactions(extrato)
    extrato["enriched_transactions"] = enriched_transactions
    write_json(extrato, os.path.join(path_temp_folder, "parsed_extrato_sicoob_enriched.json"), indent=4)
    logging.info("Lançamentos enriquecidos.")

    # --- Etapa 4: Conciliação com contatos ---
    conciliated = conciliar_extrato_contatos(enriched_transactions, caminho_contatos_csv=path_contatos_csv)
    extrato["conciliated_transactions"] = conciliated
    write_json(extrato, os.path.join(path_temp_folder, "parsed_extrato_sicoob_conciliated.json"), indent=4)
    logging.info("Lançamentos conciliados com contatos.")

    # --- Etapa 5: Consulta de CNPJs em massa ---
    consultar_cnpjs_em_massa(conciliated, caminho_cnpj_api_csv=path_cnpj_cache, wait_time=2)
    logging.info("Consulta massiva de CNPJs concluída.")

    # --- Etapa 6: Vinculação usando nome fantasia, razão social e sócios ---
    cnpj_cache = read_json(path_cnpj_cache)
    contatos_df = read_csv(path_contatos_csv, sep=";", json_columns=["socios"])
    candidate_links = []
    for cnpj, data in cnpj_cache.items():
        if isinstance(data, dict):
            candidate_links.extend(link_full_cnpj_to_contacts(data, contatos_df))
    write_json(candidate_links, os.path.join(path_temp_folder, "candidate_links.json"), indent=4)
    save_links_csv(candidate_links, os.path.join(path_temp_folder, "candidate_links.csv"))
    logging.info("Vínculos candidatos gerados e exportados.")

    # --- Etapa 7: Enriquecimento dos contatos com dados dos CNPJs ---
    process_contact_enrichment(path_cnpj_cache, path_contatos_csv)
    logging.info("Contatos enriquecidos com dados dos CNPJs.")

    # --- Etapa 8: Associação de transações aos contatos ---
    contatos_df = read_csv(path_contatos_csv, sep=";", json_columns=["socios"])
    associated_transactions = associate_transactions_with_contacts(conciliated, contatos_df)
    extrato["associated_transactions"] = associated_transactions
    write_json(associated_transactions, os.path.join(path_temp_folder, "extrato_conciliated_with_contacts.json"), indent=4)
    logging.info("Transações associadas a contatos.")

    # --- Etapa 9: Geração do relatório HTML com Jinja2 ---
    # Aqui, classificamos os dados conforme sua necessidade (certifique-se de que 'classified_data' esteja definido)
    # Etapa 9: Geração do relatório HTML com Jinja2
    classified_data = associate_transactions_with_contacts(conciliated, contatos_df)
    export_jinja_report(classified_data, config_path, os.path.join(path_temp_folder, "relatorio_transacoes_com_categorias_status.html"))
    logging.info("Relatório HTML gerado com sucesso.")

if __name__ == "__main__":
    main()
