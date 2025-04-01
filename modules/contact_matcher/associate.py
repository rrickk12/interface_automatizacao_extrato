# modules/contact_matcher/associate.py
import pandas as pd
from modules.reconciler.utils import extrair_digitos

def associate_transactions_with_contacts(transactions, contatos_df):
    contatos_dict = {
        extrair_digitos(str(row['cpf_cnpj'])): {
            "cpf_cnpj": extrair_digitos(str(row['cpf_cnpj'])),
            "nome": row.get("nome", ""),
            "razao_social": row.get("razao_social", ""),
            "nome_fantasia": row.get("nome_fantasia", ""),
            "socios": row.get("socios", "")
        }
        for _, row in contatos_df.iterrows()
        if pd.notnull(row['cpf_cnpj'])
    }

    for tx in transactions:
        chave = extrair_digitos(tx.get("cpf_cnpj_parcial", ""))
        if chave in contatos_dict:
            tx["contato"] = contatos_dict[chave]
        else:
            tx["contato"] = {}
    return transactions
