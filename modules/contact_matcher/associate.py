import pandas as pd
import logging
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

    logging.debug(f"[📋 Tabela de contatos] {len(contatos_dict)} entradas no dicionário.")

    for tx in transactions:
        chave = extrair_digitos(tx.get("cpf_cnpj_parcial", "") or "")
        tx["contato"] = {}
        logging.debug(f"[🔍 Transação] buscando contato para chave parcial: {chave}")

        # Match exato
        if chave in contatos_dict:
            tx["contato"] = contatos_dict[chave]
            logging.debug(f"[✅ Match exato] {chave} -> {tx['contato']['nome']}")
            continue

        # Match parcial com 'in'
        if chave and len(chave) >= 3:
            for full_cpf, contato in contatos_dict.items():
                if chave in full_cpf:
                    tx["contato"] = contato
                    logging.debug(f"[🟡 Match parcial via 'in'] {chave} ∈ {full_cpf} -> {contato['nome']}")
                    break

        # Fallback com possiveis_contatos
        if not tx["contato"] and "possiveis_contatos" in tx:
            for possivel in tx["possiveis_contatos"]:
                cpf_possivel = extrair_digitos(possivel.get("cpf_cnpj", ""))
                if cpf_possivel in contatos_dict:
                    tx["contato"] = contatos_dict[cpf_possivel]
                    logging.debug(f"[🔁 Fallback] {cpf_possivel} via possiveis_contatos -> {tx['contato']['nome']}")
                    break

        if not tx["contato"]:
            logging.debug(f"[❌ Sem match] Nenhum contato encontrado para: {chave}")

    return transactions
