# modules/contact_matcher/link.py
import pandas as pd
import logging
from modules.reconciler.utils import normalize_string, extract_tokens
from modules.io.utils import write_csv

def normalize_name(name: str) -> set:
    normalized = normalize_string(name)
    return extract_tokens(normalized)

def link_full_cnpj_to_contacts(cnpj_data: dict, contacts_df: pd.DataFrame, min_tokens: int = 2) -> list:
    """
    Attempts to link the corporate name, trade name, and partners of a CNPJ to known contacts.
    """
    contacts_df.columns = contacts_df.columns.str.strip().str.lower()
    cnpj = cnpj_data.get("cnpj", "")
    corporate_name = cnpj_data.get("razao_social", "")
    trade_name = cnpj_data.get("nome_fantasia", "")
    partners = cnpj_data.get("qsa", [])

    links = []

    def search_by_name(target_name, link_type):
        target_tokens = normalize_name(target_name)
        for _, contact in contacts_df.iterrows():
            contact_name = contact.get("nome", "")
            if not contact_name:
                continue
            contact_tokens = normalize_name(contact_name)
            intersection = target_tokens.intersection(contact_tokens)
            if len(intersection) >= min_tokens:
                link = contact.to_dict()
                link.update({
                    "link_type": link_type,
                    "source_name": target_name,
                    "link_strength": len(intersection),
                    "cnpj_source": cnpj,
                    "company_source": corporate_name or trade_name
                })
                links.append(link)

    if corporate_name:
        search_by_name(corporate_name, "corporate_name")
    if trade_name:
        search_by_name(trade_name, "trade_name")

    for partner in partners:
        partner_name = partner.get("nome_socio") or partner.get("nome", "")
        if partner_name:
            search_by_name(partner_name, "partner")

    return links

def save_links_csv(links: list, csv_path: str):
    """
    Saves the identified links to a CSV file for manual verification.
    Creates the target folder if needed.
    """
    if not links:
        logging.info("⚠️ No links to save.")
        return

    df = pd.DataFrame(links)
    write_csv(df, csv_path, sep=";", encoding="utf-8-sig")
