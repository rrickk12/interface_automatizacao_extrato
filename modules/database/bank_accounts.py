import logging
import pandas as pd
from modules.database.utils import normalize_text

def load_bank_accounts(filepath: str) -> list:
    """
    Lê o arquivo Excel de contas bancárias e retorna uma lista de dicionários com os campos:
      - id, nome, tipo_de_conta, numero_da_conta e saldo_inicial.
    """
    logging.info(f"Lendo contas bancárias de {filepath}")
    try:
        df = pd.read_excel(filepath)
        df['Nome'] = df['Nome'].apply(normalize_text)
        df['Tipo de conta'] = df['Tipo de conta'].apply(normalize_text)
        bank_accounts = []
        for idx, row in df.iterrows():
            record = {
                "id": idx + 1,
                "nome": row['Nome'],
                "tipo_de_conta": row['Tipo de conta'],
                "numero_da_conta": row['Número da conta'],
                "saldo_inicial": row['Saldo inicial']
            }
            bank_accounts.append(record)
        logging.info(f"{len(bank_accounts)} contas bancárias carregadas com sucesso.")
        return bank_accounts
    except Exception as e:
        logging.exception(f"Erro ao ler contas bancárias: {e}")
        return []
