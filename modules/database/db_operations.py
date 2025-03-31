import os
import json
import unicodedata
import logging
import pandas as pd
from modules.io.utils import read_csv, write_csv, read_json, write_json

def normalize_text(text: str) -> str:
    """
    Remove acentos, espaços extras e converte o texto para minúsculas.
    """
    if not isinstance(text, str):
        return text
    # Remove acentos
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    # Remove espaços extras e converte para minúsculas
    return text.strip().lower()

def load_categories(filepath: str) -> list:
    """
    Lê o arquivo Excel de categorias e retorna uma lista de dicionários com os campos:
      - id (sequencial)
      - nome
      - tipo
      - descricao

    Os textos são normalizados para facilitar o parsing.
    """
    logging.info(f"Lendo categorias de {filepath}")
    try:
        df = pd.read_excel(filepath)
        # Normaliza os campos necessários
        df['Nome'] = df['Nome'].apply(normalize_text)
        df['Tipo'] = df['Tipo'].apply(normalize_text)
        df['Descricao'] = df['Descricao'].apply(normalize_text)
        
        categories = []
        for idx, row in df.iterrows():
            record = {
                "id": idx + 1,
                "nome": row['Nome'],
                "tipo": row['Tipo'],
                "descricao": row['Descricao']
            }
            categories.append(record)
        logging.info(f"{len(categories)} categorias carregadas com sucesso.")
        return categories
    except Exception as e:
        logging.exception(f"Erro ao ler categorias: {e}")
        return []

def load_bank_accounts(filepath: str) -> list:
    """
    Lê o arquivo Excel de contas bancárias e retorna uma lista de dicionários com os campos:
      - id (sequencial)
      - nome
      - tipo_de_conta
      - numero_da_conta
      - saldo_inicial
    """
    logging.info(f"Lendo contas bancárias de {filepath}")
    try:
        df = pd.read_excel(filepath)
        df['Nome'] = df['Nome'].apply(normalize_text)
        df['Tipo de conta'] = df['Tipo de conta'].apply(normalize_text)
        
        bank_accounts = []
        for idx, row in df.iterrows():
            record = {
                "id": idx + 1,
                "nome": row['Nome'],
                "tipo_de_conta": row['Tipo de conta'],
                "numero_da_conta": row['Número da conta'],
                "saldo_inicial": row['Saldo inicial']
            }
            bank_accounts.append(record)
        logging.info(f"{len(bank_accounts)} contas bancárias carregadas com sucesso.")
        return bank_accounts
    except Exception as e:
        logging.exception(f"Erro ao ler contas bancárias: {e}")
        return []

def load_contacts(filepath: str) -> list:
    """
    Lê o arquivo Excel de contatos e retorna uma lista de dicionários com os campos:
      - id (sequencial)
      - nome
      - tipo_de_pessoa
      - tipo_do_contato
      - cpf_cnpj
      - rg_inscricao_estadual
      - email
      - telefone
      - celular
      - endereco
      - complemento
      - bairro
      - cep
      - estado
      - cidade
      - observacoes
    """
    logging.info(f"Lendo contatos de {filepath}")
    try:
        df = pd.read_excel(filepath)
        # Normaliza o campo Nome para facilitar futuras comparações
        df['Nome'] = df['Nome'].apply(normalize_text)
        
        contacts = []
        for idx, row in df.iterrows():
            record = {
                "id": idx + 1,
                "nome": row.get('Nome', ''),
                "tipo_de_pessoa": row.get('Tipo de pessoa', ''),
                "tipo_do_contato": row.get('Tipo do contato', ''),
                "cpf_cnpj": row.get('CPF/CNPJ', ''),
                "rg_inscricao_estadual": row.get('RG/Inscrição estadual', ''),
                "email": row.get('Email', ''),
                "telefone": row.get('Telefone', ''),
                "celular": row.get('Celular', ''),
                "endereco": row.get('Endereço', ''),
                "complemento": row.get('Complemento', ''),
                "bairro": row.get('Bairro', ''),
                "cep": row.get('CEP', ''),
                "estado": row.get('Estado', ''),
                "cidade": row.get('Cidade', ''),
                "observacoes": row.get('Observações', '')
            }
            contacts.append(record)
        logging.info(f"{len(contacts)} contatos carregados com sucesso.")
        return contacts
    except Exception as e:
        logging.exception(f"Erro ao ler contatos: {e}")
        return []

def update_contacts_with_csv(contacts: list, csv_filepath: str) -> list:
    """
    Atualiza os contatos usando os dados do CSV (pessoas_cpf_MMG25.csv).
    Para cada registro no CSV, se o nome corresponder a um contato, o campo 'cpf_cnpj' é atualizado.
    """
    logging.info(f"Atualizando contatos com dados do CSV: {csv_filepath}")
    try:
        df_csv = read_csv(csv_filepath, sep=";")
        # Normaliza os nomes do CSV para facilitar a comparação
        df_csv['Nome'] = df_csv['Nome'].apply(normalize_text)
        cpf_mapping = dict(zip(df_csv['Nome'], df_csv['CPF']))
        
        for contact in contacts:
            nome_normalized = normalize_text(contact.get('nome', ''))
            if nome_normalized in cpf_mapping:
                old_value = contact.get('cpf_cnpj', '')
                new_value = cpf_mapping[nome_normalized]
                contact['cpf_cnpj'] = new_value
                logging.debug(f"Contato '{contact['nome']}' atualizado: CPF de '{old_value}' para '{new_value}'")
        logging.info("Atualização de CPFs concluída.")
        return contacts
    except Exception as e:
        logging.exception(f"Erro ao atualizar contatos com CSV: {e}")
        return contacts

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
    
    Parâmetros:
      - entity_folder: caminho para a pasta onde estão os arquivos de entrada.
      - db_output: caminho completo para o arquivo JSON de saída.
    
    Retorna:
      - dicionário contendo as três "tabelas": categorias, contas_bancarias e contatos.
    """
    # Define os caminhos dos arquivos
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

if __name__ == "__main__":
    # Configuração básica de logging para debug
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Supondo que a estrutura do projeto esteja organizada com 'entity' e 'db' na raiz,
    # definimos os caminhos relativos.
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Sobe um nível para pegar a raiz do projeto
    entity_folder = os.path.join(base_dir, "entity")
    db_folder = os.path.join(base_dir, "db")
    os.makedirs(db_folder, exist_ok=True)
    db_output = os.path.join(db_folder, "db.json")
    
    # Constrói e salva a base de dados
    db_data = build_database(entity_folder, db_output)
    logging.info("Processo de construção da base de dados concluído.")
