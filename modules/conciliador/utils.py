import re
import unicodedata
import pandas as pd
import os
from modules.io.utils import read_csv, write_csv, read_json, write_json

def extrair_digitos(parcial: str) -> str:
    """Remove tudo que não for dígito (0-9)."""
    return re.sub(r"[^0-9]", "", parcial or "")

def normalize_string(text: str) -> str:
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    text = re.sub(r'[^\w\s]', '', text)
    return text.lower().strip()

def extract_tokens(name: str, min_length: int = 2) -> set:
    tokens = normalize_string(name).split()
    return {token for token in tokens if len(token) > min_length}

def match_nomes(contato_nome: str, candidate_nome: str, tipo: str = "pessoa") -> bool:
    """
    Verifica se os nomes coincidem, com regras diferentes para pessoa e empresa:
    - Pessoa: precisa de pelo menos 2 tokens em comum.
    - Empresa: se tiver <=2 tokens, exige match exato ou subconjunto; senão, >= 3 tokens em comum.
    """
    tokens_contato = extract_tokens(contato_nome)
    tokens_candidate = extract_tokens(candidate_nome)
    intersecao = tokens_contato & tokens_candidate

    if tipo == "pessoa":
        return len(intersecao) >= 2
    elif tipo == "empresa":
        # if len(tokens_candidate) <= 1:
            # return tokens_candidate == tokens_contato or tokens_candidate.issubset(tokens_contato)
        # else:
        return len(intersecao) >= 2
    return False

def carregar_contatos_csv(caminho_contatos_csv: str) -> pd.DataFrame:
    """
    Garante que o arquivo de contatos exista e retorna o DataFrame de contatos.
    Usa vírgula como separador padrão.
    """
    header = "CPF/CNPJ;Nome;Tipo de pessoa;Tipo do contato;Email;Telefone\n"
    if not os.path.isfile(caminho_contatos_csv) or os.stat(caminho_contatos_csv).st_size == 0:
        with open(caminho_contatos_csv, "w", newline="", encoding="utf-8") as f:
            f.write(header)
    
    return read_csv(caminho_contatos_csv, sep=";")

import json

def carregar_contatos_json(caminho_json: str) -> pd.DataFrame:
    data = read_json(caminho_json)
    contatos = data.get("contatos", [])
    return pd.DataFrame(contatos).fillna("")
