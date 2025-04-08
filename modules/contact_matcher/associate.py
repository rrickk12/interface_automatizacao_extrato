import pandas as pd
import logging
from modules.reconciler.utils import extrair_digitos
from modules.io.utils import write_csv

def normalizar_cpf_cnpj(valor, is_partial=False):
    """
    Extrai os dígitos do valor e normaliza:
      - Se is_partial=True, retorna os dígitos sem preencher com zeros.
      - Se for um número completo (não parcial) e tiver 11 dígitos ou menos, aplica zfill(11);
      - Caso contrário, aplica zfill(14) para CNPJ.
    """
    digitos = str(extrair_digitos(str(valor)))
    if len(digitos)>11 and len(digitos)<15:
        return digitos.zfill(14)
    elif is_partial:
        return digitos  # Para chaves parciais, não queremos inserir zeros à esquerda.
    elif len(digitos) <= 11:
        return digitos.zfill(11)

def associate_transactions_with_contacts(transactions, contatos_df):
    # Cria um dicionário com os contatos, normalizando o CPF/CNPJ COMPLETO
    contatos_dict = {
        normalizar_cpf_cnpj(row['cpf_cnpj']): {
            "cpf_cnpj": normalizar_cpf_cnpj(row['cpf_cnpj']),
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
        # Para transações, usamos o is_partial=True para não aplicar zfill à chave parcial
        chave = normalizar_cpf_cnpj(tx.get("cpf_cnpj_parcial", ""), is_partial=True)
        tx["contato"] = {}
        logging.debug(f"[🔍 Transação] buscando contato para chave parcial: {chave}")

        # Match exato: verifica se a chave parcial bate com o final do número completo
        for chave_completa, contato in contatos_dict.items():
            if chave_completa.endswith(chave):
                tx["contato"] = contato
                logging.debug(f"[✅ Match exato] {chave} -> {contato['nome']}")
                break

        # Tentativa de match parcial (usando 'in') caso o match exato não seja encontrado
        if not tx["contato"] and chave and len(chave) >= 3:
            for chave_completa, contato in contatos_dict.items():
                if chave in chave_completa:
                    tx["contato"] = contato
                    logging.debug(f"[🟡 Match parcial via 'in'] {chave} ∈ {chave_completa} -> {contato['nome']}")
                    break

        # Fallback usando o campo "possiveis_contatos", se existir
        if not tx["contato"] and "possiveis_contatos" in tx:
            for possivel in tx["possiveis_contatos"]:
                cpf_possivel = normalizar_cpf_cnpj(possivel.get("cpf_cnpj", ""), is_partial=True)
                for chave_completa, contato in contatos_dict.items():
                    if chave_completa.endswith(cpf_possivel):
                        tx["contato"] = contato
                        logging.debug(f"[🔁 Fallback] {cpf_possivel} via possiveis_contatos -> {contato['nome']}")
                        break
                if tx["contato"]:
                    break

        if not tx["contato"]:
            logging.debug(f"[❌ Sem match] Nenhum contato encontrado para: {chave}")

    return transactions
