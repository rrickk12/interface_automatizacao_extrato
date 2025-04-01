import logging
import os
import pandas as pd
from modules.database.utils import normalize_text
from modules.io.utils import read_csv

def load_contacts(filepath: str) -> list:
    """
    Lê o arquivo Excel de contatos e retorna uma lista de dicionários com os campos:
      - id, nome, tipo_de_pessoa, tipo_do_contato, cpf_cnpj, rg_inscricao_estadual,
        email, telefone, celular, endereco, complemento, bairro, cep, estado, cidade e observacoes.
    """
    logging.info(f"Lendo contatos de {filepath}")
    try:
        df = pd.read_excel(filepath)
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
    Atualiza os contatos usando os dados do CSV (ex.: pessoas_cpf_MMG25.csv).
    Para cada registro no CSV, se o nome corresponder a um contato, o campo 'cpf_cnpj' é atualizado.
    """
    logging.info(f"Atualizando contatos com dados do CSV: {csv_filepath}")
    try:
        df_csv = read_csv(csv_filepath, sep=";")
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
