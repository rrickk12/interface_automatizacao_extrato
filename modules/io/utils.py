import os
import json
import logging
import pandas as pd

def read_json(file_path: str) -> dict:
    """
    Lê um arquivo JSON a partir do caminho informado.
    Se o arquivo não existir ou estiver vazio, retorna {}.
    """
    if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
        logging.warning(f"Arquivo JSON não encontrado ou vazio: {file_path}")
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Erro ao ler JSON em {file_path}: {e}")
        return {}

def write_json(data: dict, file_path: str, indent: int = 4, ensure_ascii: bool = False) -> None:
    """
    Salva o dicionário 'data' em um arquivo JSON no caminho 'file_path'.
    Cria o diretório se necessário.
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
        logging.info(f"Dados salvos em JSON com sucesso: {file_path}")
    except Exception as e:
        logging.error(f"Erro ao salvar JSON em {file_path}: {e}")

def deserialize_json_columns(df: pd.DataFrame, json_columns: list) -> pd.DataFrame:
    """
    Para cada coluna em 'json_columns' presente no DataFrame, tenta desserializar os valores de string para objeto.
    """
    for col in json_columns:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: json.loads(x) if isinstance(x, str) and x.strip() != "" else x
            )
    return df

def serialize_json_columns(df: pd.DataFrame, json_columns: list) -> pd.DataFrame:
    """
    Para cada coluna em 'json_columns' presente no DataFrame, converte objetos (list/dict) para string JSON.
    """
    for col in json_columns:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (list, dict)) else x
            )
    return df

def read_csv(file_path: str, sep: str = ";", json_columns: list = None) -> pd.DataFrame:
    """
    Lê um arquivo CSV usando o pandas.
    Se o arquivo não existir ou estiver vazio, retorna um DataFrame vazio.
    Caso 'json_columns' seja informado, tenta desserializar essas colunas.
    Usa o engine 'python' para maior flexibilidade.
    """
    if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
        logging.warning(f"Arquivo CSV não encontrado ou vazio: {file_path}")
        return pd.DataFrame()
    try:
        df = pd.read_csv(file_path, sep=sep, engine="python").fillna("")
        logging.info(f"CSV lido com sucesso: {file_path}")
        if json_columns:
            df = deserialize_json_columns(df, json_columns)
        return df
    except Exception as e:
        logging.error(f"Erro ao ler CSV em {file_path}: {e}")
        return pd.DataFrame()

def safe_read_csv(file_path: str, sep=";", json_columns: list = None, **kwargs) -> pd.DataFrame:
    """
    Lê um arquivo CSV de forma segura.
    Se o arquivo não existir ou estiver vazio, retorna um DataFrame vazio com colunas padrão.
    Caso 'json_columns' seja informado, tenta desserializar essas colunas.
    """
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        logging.warning(f"Arquivo CSV vazio ou não encontrado: {file_path}")
        df = pd.DataFrame(columns=["cpf_cnpj", "nome", "razao_social", "nome_fantasia", "socios"])
    else:
        try:
            df = pd.read_csv(file_path, sep=sep, **kwargs)
            logging.info(f"CSV lido com sucesso: {file_path}")
        except Exception as e:
            logging.error(f"Erro ao ler CSV em {file_path}: {e}")
            df = pd.DataFrame(columns=["cpf_cnpj", "nome", "razao_social", "nome_fantasia", "socios"])
    if json_columns:
        df = deserialize_json_columns(df, json_columns)
    return df

def write_csv(df: pd.DataFrame, file_path: str, sep: str = ";", encoding: str = "utf-8-sig", index: bool = False, json_columns: list = None) -> None:
    """
    Salva um DataFrame em um arquivo CSV no caminho especificado.
    Cria o diretório de destino se necessário.
    Caso 'json_columns' seja informado, serializa essas colunas antes de salvar.
    """
    try:
        if json_columns:
            df = serialize_json_columns(df, json_columns)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        df.to_csv(file_path, sep=sep, encoding=encoding, index=index)
        logging.info(f"CSV salvo com sucesso: {file_path}")
    except Exception as e:
        logging.error(f"Erro ao salvar CSV em {file_path}: {e}")
