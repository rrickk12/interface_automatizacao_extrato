import os
import json
import logging
import pandas as pd
import csv

def read_json(file_path: str) -> dict:
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
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
        logging.info(f"Dados salvos em JSON com sucesso: {file_path}")
    except Exception as e:
        logging.error(f"Erro ao salvar JSON em {file_path}: {e}")

def deserialize_json_columns(df: pd.DataFrame, json_columns: list) -> pd.DataFrame:
    for col in json_columns:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: json.loads(x) if isinstance(x, str) and x.strip() != "" else x
            )
    return df

def serialize_json_columns(df: pd.DataFrame, json_columns: list) -> pd.DataFrame:
    for col in json_columns:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (list, dict)) else x
            )
    return df

def read_csv(file_path: str, sep: str = ";", json_columns: list = None) -> pd.DataFrame:
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

def write_csv(
    df: pd.DataFrame,
    file_path: str,
    sep: str = ";",
    encoding: str = "utf-8-sig",
    index: bool = False,
    json_columns: list = None
) -> None:
    try:
        if json_columns:
            df = serialize_json_columns(df, json_columns)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        main_cols = ["cpf_cnpj", "nome", "razao_social", "nome_fantasia", "socios"]
        for col in main_cols:
            if col not in df.columns:
                df[col] = ""
        ordered_cols = main_cols + [col for col in df.columns if col not in main_cols]
        df = df[ordered_cols]

        df.to_csv(
            file_path,
            sep=sep,
            encoding=encoding,
            index=index,
            quoting=csv.QUOTE_NONNUMERIC,
            lineterminator='\n'
        )
        logging.info(f"CSV salvo com sucesso: {file_path}")
    except Exception as e:
        logging.error(f"Erro ao salvar CSV em {file_path}: {e}")