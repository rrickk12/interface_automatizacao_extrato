import logging
import pandas as pd
from modules.database.utils import normalize_text

def load_categories(filepath: str) -> list:
    """
    Lê o arquivo Excel de categorias e retorna uma lista de dicionários com os campos:
      - id, nome, tipo e descricao.
    """
    logging.info(f"Lendo categorias de {filepath}")
    try:
        df = pd.read_excel(filepath)
        df['Nome'] = df['Nome'].apply(normalize_text)
        df['Tipo'] = df['Tipo'].apply(normalize_text)
        df['Descricao'] = df['Descricao'].apply(normalize_text)
        categories = []
        for idx, row in df.iterrows():
            record = {
                "id": idx + 1,
                "nome": row['Nome'],
                "tipo": row['Tipo'],
                "descricao": row['Descricao']
            }
            categories.append(record)
        logging.info(f"{len(categories)} categorias carregadas com sucesso.")
        return categories
    except Exception as e:
        logging.exception(f"Erro ao ler categorias: {e}")
        return []
