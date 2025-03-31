import os
import logging
import pandas as pd
from modules.io.utils import read_csv

def integrar_aliases_contatos(path_aliases: str, contatos_df: pd.DataFrame) -> pd.DataFrame:
    """
    Carrega um arquivo auxiliar CSV contendo aliases (com colunas "nome" e "cpf")
    e integra esses contatos ao DataFrame de contatos atualizados.
    Se o contato (baseado no CPF) já existir, ignora; caso contrário, adiciona-o.
    """
    if not os.path.exists(path_aliases):
        logging.info("Arquivo de aliases não encontrado. Pulando integração de aliases.")
        return contatos_df

    try:
        # Supondo que o arquivo de aliases utiliza vírgula como separador
        df_aliases = read_csv(path_aliases, sep=",")
        logging.info("Arquivo de aliases carregado com sucesso.")
    except Exception as e:
        logging.error("Erro ao carregar o arquivo de aliases: %s", e)
        return contatos_df

    # Padroniza os nomes das colunas para minúsculo e sem espaços em branco
    df_aliases.columns = df_aliases.columns.str.strip().str.lower()
    if "nome" not in df_aliases.columns or "cpf" not in df_aliases.columns:
        logging.error("O arquivo de aliases deve conter as colunas 'nome' e 'cpf'.")
        return contatos_df

    # Para cada alias, verifica se o CPF já está presente no DataFrame de contatos
    for _, row in df_aliases.iterrows():
        alias_nome = row["nome"]
        alias_cpf = str(row["cpf"]).strip()
        # Compara de forma exata para evitar falsos positivos (não usar substring)
        if not (contatos_df["cpf_cnpj"].astype(str).str.strip() == alias_cpf).any():
            logging.info("Adicionando alias '%s' com CPF %s", alias_nome, alias_cpf)
            novo_contato = {
                "cpf_cnpj": alias_cpf,
                "nome": alias_nome,
                "razao_social": alias_nome,
                "nome_fantasia": "",
                "socios": ""  # ou pode ser inicializado como '{}'
            }
            # Adiciona o novo contato ao DataFrame
            contatos_df = pd.concat([contatos_df, pd.DataFrame([novo_contato])], ignore_index=True)
        else:
            logging.debug("Alias '%s' com CPF %s já existe no banco de contatos.", alias_nome, alias_cpf)
    return contatos_df