# modules/contact_matcher/enrich.py
import os
import json
import logging
import pandas as pd
from modules.io.utils import read_csv, write_csv, read_json

def enrich_contact_with_cnpj_data(cnpj_data, contacts_df):
    """
    If the CNPJ already exists in the contacts database, update the contact with corporate name,
    trade name, and partners. Otherwise, create a new contact with these details.
    Modifies the DataFrame in-place and returns the updated DataFrame.
    """
    cnpj = str(cnpj_data.get("cnpj", "")).zfill(14)
    corporate_name = cnpj_data.get("razao_social", "")
    trade_name = cnpj_data.get("nome_fantasia", "")
    partners = cnpj_data.get("qsa", [])

    contacts_df.columns = contacts_df.columns.str.strip().str.lower()
    if "cpf_cnpj" not in contacts_df.columns:
        contacts_df["cpf_cnpj"] = ""
    contacts_df["cpf_cnpj"] = contacts_df["cpf_cnpj"].fillna("").astype(str)

    partners_str = json.dumps(partners, ensure_ascii=False, indent=4) if partners else ""

    exists = contacts_df["cpf_cnpj"].apply(lambda x: cnpj in x).any()

    if exists:
        logging.info(f"✅ CNPJ {cnpj} already exists in the contacts database. Enriching...")
        contacts_df.loc[contacts_df["cpf_cnpj"] == cnpj, "razao_social"] = corporate_name
        contacts_df.loc[contacts_df["cpf_cnpj"] == cnpj, "nome_fantasia"] = trade_name
        contacts_df.loc[contacts_df["cpf_cnpj"] == cnpj, "socios"] = partners_str
    else:
        logging.info(f"➕ Adding new contact for CNPJ {cnpj}")
        new_contact = {
            "nome": corporate_name or trade_name or "Unknown",
            "cpf_cnpj": cnpj,
            "razao_social": corporate_name,
            "nome_fantasia": trade_name,
            "socios": partners_str
        }
        contacts_df = pd.concat([contacts_df, pd.DataFrame([new_contact])], ignore_index=True)

    return contacts_df

def process_contact_enrichment(cnpj_cache_path: str, contacts_csv_path: str):
    """
    Loads the CNPJ cache and the contacts file.
    For each CNPJ in the cache, if the contact exists, update the fields;
    otherwise, add a new contact. Saves the updated contacts file.
    """
    if not os.path.isfile(cnpj_cache_path):
        logging.error("CNPJ cache file not found: %s", cnpj_cache_path)
        return

    cache = read_json(cnpj_cache_path)

    if not os.path.isfile(contacts_csv_path):
        logging.info("Contacts file not found, creating a new one.")
        df_contacts = pd.DataFrame(columns=["cpf_cnpj", "nome", "razao_social", "nome_fantasia", "socios"])
    else:
        df_contacts = read_csv(contacts_csv_path, sep=";", json_columns=["socios"])

    df_contacts.columns = df_contacts.columns.str.strip().str.lower()

    for cnpj, cnpj_data in cache.items():
        df_contacts = enrich_contact_with_cnpj_data(cnpj_data, df_contacts)

    write_csv(df_contacts, contacts_csv_path, sep=";", encoding="utf-8-sig", json_columns=["socios"])
    logging.info("Contacts updated with CNPJ data saved in: %s", contacts_csv_path)
