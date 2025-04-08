import pandas as pd
import logging
from modules.reconciler.utils import normalize_string, extract_tokens
from modules.io.utils import write_csv

def normalize_cpf_cnpj(valor):
    """
    Normaliza o valor de CPF/CNPJ:
      - Se tiver 11 dígitos (após remoção de caracteres não numéricos), assume CPF e retorna com 11 dígitos.
      - Caso contrário, assume CNPJ e retorna com 14 dígitos.
    """
    # Remove tudo que não for dígito
    digitos = "".join(filter(str.isdigit, str(valor)))
    if len(digitos) == 11:
        return digitos.zfill(11)
    return digitos.zfill(14)

def normalize_name(name: str) -> set:
    normalized = normalize_string(name)
    return extract_tokens(normalized)

def link_full_cnpj_to_contacts(cnpj_data: dict, contacts_df: pd.DataFrame, min_tokens: int = 2) -> list:
    """
    Tenta vincular a razão social, nome fantasia e parceiros de um CNPJ aos contatos conhecidos.
    Garante que:
      - O campo "cnpj_source" seja normalizado de acordo com CNPJ (14 dígitos, exceto se for CPF, 11 dígitos)
      - O campo "cpf_cnpj" dos contatos seja normalizado adequadamente.
    """
    contacts_df.columns = contacts_df.columns.str.strip().str.lower()
    # Normaliza o valor do campo "cnpj" do dicionário
    cnpj = normalize_cpf_cnpj(cnpj_data.get("cnpj", ""))
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
                # Normaliza o CPF/CNPJ do contato adequadamente (11 para CPF, 14 para CNPJ)
                link["cpf_cnpj"] = normalize_cpf_cnpj(link.get("cpf_cnpj", ""))
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
    Salva os vínculos identificados em um arquivo CSV para verificação manual.
    Cria a pasta de destino, se necessário.
    """
    if not links:
        logging.info("⚠️ No links to save.")
        return

    df = pd.DataFrame(links)
    write_csv(df, csv_path, sep=";", encoding="utf-8-sig")
