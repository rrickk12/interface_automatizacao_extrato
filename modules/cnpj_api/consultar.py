import requests
import logging
import time
import json
import os
from datetime import datetime
from threading import Lock
from modules.io.utils import read_json, write_json
cache_lock = Lock()

def normalize_cnpj(cnpj: str) -> str:
    return "".join(ch for ch in cnpj if ch.isdigit())


def load_cache(cache_path: str) -> dict:
    if not os.path.exists(cache_path):
        return {}

    try:
        return read_json(cache_path)
    except json.JSONDecodeError as e:
        logging.error("Erro ao carregar cache (%s): %s", cache_path, e)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{cache_path}.bak_{timestamp}"
        logging.warning("Renomeando cache corrompido para: %s", backup_path)
        os.rename(cache_path, backup_path)
        return {}


def save_cache(cache_path: str, cnpj: str, resultado: dict):
    from .consultar import load_cache, normalize_cnpj
    with cache_lock:
        try:
            cache = load_cache(cache_path)
        except Exception:
            cache = {}

        cnpj_normalizado = normalize_cnpj(cnpj)
        cache[cnpj_normalizado] = resultado

        try:
            write_json(cache, cache_path, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error("Erro ao salvar cache (%s): %s", cache_path, e)


def consultar_cnpj_api(cnpj: str) -> dict:
    cnpj_limpo = normalize_cnpj(cnpj)
    if len(cnpj_limpo) != 14:
        logging.warning("CNPJ inválido: %s", cnpj)
        return {"cnpj": cnpj_limpo, "erro": "CNPJ inválido"}

    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        dados_api = response.json()

        resultado = {
            "cnpj": cnpj_limpo,
            "razao_social": dados_api.get("razao_social", ""),
            "nome_fantasia": dados_api.get("nome_fantasia", ""),
            "situacao": dados_api.get("situacao", ""),
            "data_abertura": dados_api.get("data_abertura", dados_api.get("data_situacao", "")),
            "endereco": "",
            "qsa": dados_api.get("qsa", []),
            "erro": ""
        }

        logradouro = dados_api.get("logradouro", "")
        numero = dados_api.get("numero", "")
        complemento = dados_api.get("complemento", "")
        bairro = dados_api.get("bairro", "")
        municipio = dados_api.get("municipio", "")
        uf = dados_api.get("uf", "")
        cep = dados_api.get("cep", "")

        resultado["endereco"] = f"{logradouro}, {numero} {complemento} - {bairro}, {municipio}/{uf} CEP: {cep}"
        return resultado

    except requests.RequestException as e:
        logging.error("Erro na requisição da API para o CNPJ %s: %s", cnpj_limpo, e)
        return {"cnpj": cnpj_limpo, "erro": str(e)}


def consultar_cnpj(cnpj: str, cache_path: str = "db/cnpj_cache.json", max_retries: int = 3, wait_time: int = 2) -> dict:
    cnpj_normalizado = normalize_cnpj(cnpj)
    cache = load_cache(cache_path)

    if cnpj_normalizado in cache:
        logging.info("CNPJ %s encontrado no cache.", cnpj_normalizado)
        return cache[cnpj_normalizado]

    attempt = 0
    resultado = None
    while attempt < max_retries:
        resultado = consultar_cnpj_api(cnpj)
        if not resultado.get("erro"):
            break
        attempt += 1
        logging.warning("Tentativa %d para consultar CNPJ %s falhou. Retentando em %d segundos...",
                        attempt, cnpj_normalizado, wait_time)
        time.sleep(wait_time)

    save_cache(cache_path, cnpj_normalizado, resultado)
    return resultado
