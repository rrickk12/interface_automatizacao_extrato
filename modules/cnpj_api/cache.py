import logging
import os
import time
from modules.cnpj_api.api import consultar_cnpj_api  # correta
from modules.io.utils import read_json, write_json
from modules.cnpj_api.utils import normalize_cnpj

def load_cache(cache_path: str) -> dict:
    if os.path.isfile(cache_path):
        return read_json(cache_path)
    return {}

def save_cache(cache_path: str, cnpj: str, resultado: dict):
    try:
        cache = load_cache(cache_path)
    except Exception as e:
        logging.error(f"Erro ao carregar o cache: {e}")
        cache = {}

    cnpj_norm = normalize_cnpj(cnpj)
    cache[cnpj_norm] = resultado

    try:
        write_json(cache, cache_path, indent=2, ensure_ascii=False)
        logging.info(f"Cache atualizado com CNPJ {cnpj_norm}.")
    except Exception as e:
        logging.error(f"Erro ao salvar o cache em {cache_path}: {e}")

def consultar_cnpj(cnpj: str, cache_path: str = "db/cnpj_cache.json", max_retries: int = 5, wait_time: int = 5, fonte: str = "cnpja") -> dict:
    cnpj_normalizado = normalize_cnpj(cnpj)
    cache = load_cache(cache_path)

    if cnpj_normalizado in cache:
        logging.info("CNPJ %s encontrado no cache.", cnpj_normalizado)
        return cache[cnpj_normalizado]

    attempt = 0
    resultado = {}
    while attempt < max_retries:
        resultado = consultar_cnpj_api(cnpj_normalizado, fonte=fonte)
        if not resultado.get("erro"):
            logging.info("Consulta ao CNPJ %s bem-sucedida.", cnpj_normalizado)
            save_cache(cache_path, cnpj_normalizado, resultado)
            return resultado

        attempt += 1
        logging.warning("Tentativa %d para consultar CNPJ %s falhou. Retentando em %d segundos...",
                        attempt, cnpj_normalizado, wait_time)
        time.sleep(wait_time)

    logging.error("Erro ao consultar CNPJ %s após %d tentativas: %s",
                  cnpj_normalizado, max_retries, resultado.get("erro"))
    return {"cnpj": cnpj_normalizado, "erro": resultado.get("erro", "Erro desconhecido")}
