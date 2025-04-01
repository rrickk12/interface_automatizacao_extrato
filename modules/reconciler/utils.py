# modules/reconciler/utils.py
import re
import unicodedata
import os
import pandas as pd
from modules.io.utils import read_csv, read_json

def extrair_digitos(text: str) -> str:
    """Remove tudo que não for dígito."""
    return re.sub(r"[^0-9]", "", text or "")

def normalize_string(text: str) -> str:
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    text = re.sub(r'[^\w\s]', '', text)
    return text.lower().strip()

def extract_tokens(name: str, min_length: int = 2) -> set:
    tokens = normalize_string(name).split()
    return {token for token in tokens if len(token) > min_length}

def match_nomes(nome1: str, nome2: str, tipo: str = "pessoa") -> bool:
    tokens1 = extract_tokens(nome1)
    tokens2 = extract_tokens(nome2)
    intersecao = tokens1 & tokens2
    if tipo == "pessoa":
        return len(intersecao) >= 2
    elif tipo == "empresa":
        return len(intersecao) >= 2
    return False

def carregar_contatos_csv(caminho_contatos_csv: str) -> pd.DataFrame:
    header = "CPF/CNPJ;Nome;Tipo de pessoa;Tipo do contato;Email;Telefone\n"
    if not os.path.isfile(caminho_contatos_csv) or os.stat(caminho_contatos_csv).st_size == 0:
        with open(caminho_contatos_csv, "w", newline="", encoding="utf-8") as f:
            f.write(header)
    return read_csv(caminho_contatos_csv, sep=";")

def carregar_contatos_json(caminho_json: str) -> pd.DataFrame:
    data = read_json(caminho_json)
    contatos = data.get("contatos", [])
    return pd.DataFrame(contatos).fillna("")
