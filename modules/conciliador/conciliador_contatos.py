import csv
import re
import os
import time
import logging
import pandas as pd
import unicodedata
from modules.cnpj_api.consultar import consultar_cnpj
from modules.cnpj_api.salvar import salvar_cnpj_consultado
from modules.conciliador.utils import (
    extrair_digitos,
    match_nomes,
    extract_tokens,
    normalize_string
)
from modules.conciliador.vinculo_socios import vincular_socios_a_contatos 
from modules.conciliador.utils import carregar_contatos_json
from modules.conciliador.utils import carregar_contatos_csv
from modules.io.utils import read_csv, write_csv, read_json, write_json

def consultar_cnpjs_em_massa(lancamentos: list, caminho_cnpj_api_csv: str, caminho_contatos_csv: str, wait_time: float = 1.0) -> None:
    """
    Varre os lançamentos para identificar CNPJs (14 dígitos) sem contatos conciliados,
    remove duplicatas e consulta cada CNPJ, aguardando wait_time segundos entre as consultas.
    Os resultados são salvos no cache JSON e, se necessário, atualizam a base de contatos.
    """
    unique_cnpjs = set()
    for lanc in lancamentos:
        doc = lanc.get("cpf_cnpj_parcial", "")
        digitos = extrair_digitos(doc)
        if len(digitos) == 14 and not lanc.get("possiveis_contatos"):
            unique_cnpjs.add(digitos)

    unique_cnpjs = list(unique_cnpjs)
    total = len(unique_cnpjs)
    logging.info(f"Consultando {total} CNPJs não conciliados...")

    for i, cnpj in enumerate(unique_cnpjs, start=1):
        logging.info(f"[{i}/{total}] Consultando CNPJ: {cnpj} ...")
        resultado_api = consultar_cnpj(cnpj, cache_path=caminho_cnpj_api_csv)
        if resultado_api.get("erro"):
            logging.info(f"Erro: {resultado_api.get('erro')}")
        else:
            logging.info("OK")

        # Salva apenas no cache JSON
        salvar_cnpj_consultado(caminho_cnpj_api_csv, resultado_api)
        
        # Se for necessário atualizar os contatos, faça isso separadamente:
        # df_contatos = read_csv(caminho_contatos_csv, sep=";", json_columns=["socios"])
        # df_contatos = atualizar_contatos(df_contatos, resultado_api)  # Função que atualiza ou insere o contato
        # write_csv(df_contatos, caminho_contatos_csv, sep=";", encoding="utf-8-sig", json_columns=["socios"])
        
        # 🔍 Tenta encontrar sócios nos contatos (utilizando um arquivo adequado, se necessário)
        df_contatos = carregar_contatos_json("db/db.json")  # Verifique se esse arquivo é o correto para essa operação
        vinculos = vincular_socios_a_contatos(resultado_api, df_contatos)
        for vinculo in vinculos:
            logging.info(f"🔗 Vínculo encontrado: {vinculo['nome']} → {resultado_api['razao_social']} ({resultado_api['cnpj']})")

        time.sleep(wait_time)


def conciliar_extrato_contatos(lancamentos: list, caminho_contatos_csv: str, caminho_cnpj_api_csv: str) -> list:
    """
    Para cada lançamento do extrato:
      - Se o campo "cpf_cnpj_parcial" for do tipo CPF (contém '*' ou 11 dígitos), busca no CSV de contatos
        comparando os dígitos e utilizando a comparação dos nomes (match_nomes) para confirmar.
      - Se for CNPJ (14 dígitos), busca no CSV; se não encontrar, consulta a API e atualiza o CSV.
      - Adiciona o campo 'possiveis_contatos' (lista com os contatos que batem) no lançamento.
    """
    # Garante que o arquivo de contatos exista (cria com cabeçalho se necessário)
    df_contatos = carregar_contatos_csv(caminho_contatos_csv)



    df = read_csv(caminho_contatos_csv, sep=";")
    print(df.head())

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
                cnpj_contato = str(row.get("CPF/CNPJ", row.get("CNPJ", "")))
                if extrair_digitos(cnpj_contato).find(apenas_numeros) != -1:
                    if lanc.get("favorecido", ""):
                        tipo = "empresa" if len(extract_tokens(row.get("Nome", ""))) > 2 else "pessoa"
                        if match_nomes(row.get("Nome", ""), lanc.get("favorecido", ""), tipo=tipo):
                            matches.append(row.to_dict())
                    else:
                        matches.append(row.to_dict())
            lanc["possiveis_contatos"] = matches

    return lancamentos
