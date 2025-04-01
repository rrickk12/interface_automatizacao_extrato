# modules/contact_matcher/aliases.py
import os
import logging
import pandas as pd
from modules.io.utils import read_csv

# Colunas esperadas no DataFrame de contatos
EXPECTED_COLUMNS = ["cpf_cnpj", "nome", "razao_social", "nome_fantasia", "socios"]


def ensure_contact_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Garante que o DataFrame de contatos tenha as colunas esperadas, preenchendo com string vazia se necessário.
    """
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[EXPECTED_COLUMNS + [col for col in df.columns if col not in EXPECTED_COLUMNS]]


def integrate_contact_aliases(aliases_path: str, contacts_df: pd.DataFrame) -> pd.DataFrame:
    """
    Integra contatos do arquivo de aliases ao DataFrame de contatos.
    Garante que cada novo contato siga o formato completo esperado.
    """
    contacts_df = ensure_contact_columns(contacts_df)

    if not os.path.exists(aliases_path):
        logging.info("Aliases file not found. Skipping alias integration.")
        return contacts_df

    try:
        df_aliases = read_csv(aliases_path, sep=";")
        logging.info("Aliases file loaded successfully.")
    except Exception as e:
        logging.error("Error loading aliases file: %s", e)
        return contacts_df

    # Normaliza cabeçalhos para evitar problemas com capitalização e espaços
    df_aliases.columns = df_aliases.columns.str.strip().str.lower()

    if "nome" not in df_aliases.columns or "cpf" not in df_aliases.columns:
        logging.error("Aliases file must contain the columns 'nome' and 'cpf'.")
        return contacts_df

    for _, row in df_aliases.iterrows():
        alias_name = str(row["nome"]).strip()
        alias_cpf = str(row["cpf"]).strip()

        if not alias_cpf:
            continue

        # Verifica se já existe esse CPF no banco de contatos
        already_exists = (contacts_df["cpf_cnpj"].astype(str).str.strip() == alias_cpf).any()

        if not already_exists:
            logging.info("Adding alias '%s' with CPF %s", alias_name, alias_cpf)
            new_contact = {col: "" for col in EXPECTED_COLUMNS}
            new_contact["cpf_cnpj"] = alias_cpf
            new_contact["nome"] = alias_name
            new_contact["razao_social"] = alias_name
            contacts_df = pd.concat([contacts_df, pd.DataFrame([new_contact])], ignore_index=True)
        else:
            logging.debug("Alias '%s' with CPF %s already exists in the contacts database.", alias_name, alias_cpf)

    return ensure_contact_columns(contacts_df)


def integrate_aliases(aliases_path: str, contacts_df: pd.DataFrame) -> pd.DataFrame:
    """
    Atualiza os CPFs de contatos existentes com base em um arquivo auxiliar de aliases.
    Útil para atualizar CPFs a partir de nomes.
    """
    contacts_df = ensure_contact_columns(contacts_df)

    if not os.path.exists(aliases_path):
        logging.info("Arquivo de aliases não encontrado. Pulando integração de aliases.")
        return contacts_df

    try:
        df_aliases = read_csv(aliases_path, sep=";")
        logging.info("Arquivo de aliases carregado com sucesso.")
    except Exception as e:
        logging.error("Erro ao carregar o arquivo de aliases: %s", e)
        return contacts_df

    df_aliases.columns = df_aliases.columns.str.strip().str.lower()

    if "nome" not in df_aliases.columns or "cpf" not in df_aliases.columns:
        logging.error("O arquivo de aliases deve conter as colunas 'nome' e 'cpf'.")
        return contacts_df

    cpf_mapping = dict(zip(
        df_aliases["nome"].str.strip().str.lower(),
        df_aliases["cpf"].astype(str).str.strip()
    ))

    for idx, contact in contacts_df.iterrows():
        contact_name = str(contact.get("nome", "")).strip().lower()
        if contact_name in cpf_mapping:
            old_value = contact.get("cpf_cnpj", "")
            new_value = cpf_mapping[contact_name]
            contacts_df.at[idx, "cpf_cnpj"] = new_value
            logging.debug("Contato '%s' atualizado: CPF de '%s' para '%s'",
                          contact.get("nome", ""), old_value, new_value)

    return ensure_contact_columns(contacts_df)