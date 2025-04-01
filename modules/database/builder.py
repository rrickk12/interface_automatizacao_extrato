import os
import logging
from modules.database.categories import load_categories
from modules.database.bank_accounts import load_bank_accounts
from modules.database.contacts import load_contacts, update_contacts_with_csv
from modules.io.utils import write_json

def save_database(db_data: dict, output_filepath: str):
    """
    Salva a base de dados (db_data) em um arquivo JSON.
    """
    logging.info(f"Salvando base de dados em {output_filepath}")
    try:
        write_json(db_data, output_filepath, ensure_ascii=False, indent=4)
        logging.info("Base de dados salva com sucesso.")
    except Exception as e:
        logging.exception(f"Erro ao salvar a base de dados: {e}")

def build_database(entity_folder: str, db_output: str) -> dict:
    """
    Constrói a base de dados lendo os arquivos dos contatos, categorias e contas bancárias
    que estão na pasta 'entity'. Atualiza os contatos com o CSV de CPFs e salva o resultado
    no arquivo JSON especificado.
    """
    categorias_file = os.path.join(entity_folder, "Categorias-Procfy-26-03-2025 15-43-46.xlsx")
    contas_file = os.path.join(entity_folder, "Contas Bancarias-Procfy-26-03-2025 15-45-03.xlsx")
    contatos_file = os.path.join(entity_folder, "Contatos-Procfy-26-03-2025 15-45-20.xlsx")
    cpf_csv_file = os.path.join(entity_folder, "pessoas_cpf_MMG25.csv")
    
    logging.info("Iniciando construção da base de dados")
    categorias = load_categories(categorias_file)
    contas = load_bank_accounts(contas_file)
    contatos = load_contacts(contatos_file)
    contatos = update_contacts_with_csv(contatos, cpf_csv_file)
    
    db_data = {
        "categorias": categorias,
        "contas_bancarias": contas,
        "contatos": contatos
    }
    
    save_database(db_data, db_output)
    return db_data
