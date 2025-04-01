# modules/reconciler/reconciliation.py
import logging
from modules.reconciler.utils import extrair_digitos, match_nomes, extract_tokens
from modules.io.utils import read_csv
from modules.reconciler.utils import carregar_contatos_csv

def conciliar_extrato_contatos(lancamentos: list, caminho_contatos_csv: str) -> list:
    """
    Para cada lançamento do extrato:
      - Se o campo "cpf_cnpj_parcial" for de CPF (contém '*' ou 11 dígitos), busca no CSV de contatos
        comparando os dígitos e utilizando a comparação dos nomes para confirmar.
      - Se for CNPJ (14 dígitos), busca no CSV e adiciona possíveis contatos.
      - Adiciona o campo 'possiveis_contatos' em cada lançamento.
    """
    df_contatos = carregar_contatos_csv(caminho_contatos_csv)
    for lanc in lancamentos:
        doc_parcial = lanc.get("cpf_cnpj_parcial", "")
        lanc["possiveis_contatos"] = []
        if not doc_parcial:
            continue

        apenas_numeros = extrair_digitos(doc_parcial)
        if "*" in doc_parcial or len(apenas_numeros) == 11:
            matches = []
            for _, row in df_contatos.iterrows():
                cpf_contato = str(row.get("CPF/CNPJ", row.get("CPF", "")))
                if extrair_digitos(cpf_contato).find(extrair_digitos(doc_parcial)) != -1:
                    if lanc.get("favorecido", ""):
                        if match_nomes(row.get("Nome", ""), lanc.get("favorecido", ""), tipo="pessoa"):
                            matches.append(row.to_dict())
                    else:
                        matches.append(row.to_dict())
            lanc["possiveis_contatos"] = matches

        elif len(apenas_numeros) == 14:
            matches = []
            for _, row in df_contatos.iterrows():
                cnpj_contato = str(
                    row.get("cpf_cnpj") or 
                    row.get("CPF/CNPJ") or 
                    row.get("CNPJ") or ""
                )
                if extrair_digitos(cnpj_contato).find(apenas_numeros) != -1:
                    if lanc.get("favorecido", ""):
                        tipo = "empresa" if len(extract_tokens(row.get("Nome", ""))) > 2 else "pessoa"
                        if match_nomes(row.get("Nome", ""), lanc.get("favorecido", ""), tipo=tipo):
                            matches.append(row.to_dict())
                    else:
                        matches.append(row.to_dict())
            lanc["possiveis_contatos"] = matches

    return lancamentos
