import json
import os
import logging
from modules.cnpj_api.consultar import load_cache, normalize_cnpj
from modules.io.utils import write_json

def salvar_cnpj_consultado(path_cache: str, resultado: dict):
    """
    Salva os dados de um único CNPJ no cache consolidado (arquivo JSON).
    """
    cnpj = normalize_cnpj(resultado.get("cnpj", ""))
    if not cnpj:
        logging.warning("Tentativa de salvar resultado de CNPJ inválido.")
        return

    try:
        cache = load_cache(path_cache)
    except Exception as e:
        logging.error("Erro ao carregar cache antes de salvar: %s", e)
        cache = {}

    cache[cnpj] = resultado

    try:
        write_json(cache, path_cache, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error("Erro ao salvar cache (%s): %s", path_cache, e)
