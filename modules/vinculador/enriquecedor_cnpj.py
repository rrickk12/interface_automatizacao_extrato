import os
import json
import logging
import pandas as pd
from modules.io.utils import read_csv, write_csv, read_json, write_json

def enriquecer_contato_com_dados_do_cnpj(cnpj_dados, contatos_df):
    """
    Se o CNPJ já existe no banco de contatos, atualiza o contato com razão social, nome fantasia e sócios.
    Se não existe, cria um novo contato com essas informações.
    Essa função modifica o DataFrame in-place e retorna o DataFrame atualizado.
    """
    # Converte o valor para string e garante que tenha 14 dígitos
    cnpj = str(cnpj_dados.get("cnpj", "")).zfill(14)
    razao = cnpj_dados.get("razao_social", "")
    fantasia = cnpj_dados.get("nome_fantasia", "")
    socios = cnpj_dados.get("qsa", [])

    # Padroniza os nomes das colunas e garante que a coluna de documento esteja presente
    contatos_df.columns = contatos_df.columns.str.strip().str.lower()
    if "cpf_cnpj" not in contatos_df.columns:
        contatos_df["cpf_cnpj"] = ""
    contatos_df["cpf_cnpj"] = contatos_df["cpf_cnpj"].fillna("").astype(str)

    # Converte os dados de sócios para string JSON
    socios_str = json.dumps(socios, ensure_ascii=False, indent=4) if socios else ""

    # Verifica se já existe um contato cujo "cpf_cnpj" contenha o CNPJ
    existe = contatos_df["cpf_cnpj"].apply(lambda x: cnpj in x).any()

    if existe:
        logging.info(f"✅ CNPJ {cnpj} já está no banco de contatos. Enriquecendo...")
        contatos_df.loc[contatos_df["cpf_cnpj"] == cnpj, "razao_social"] = razao
        contatos_df.loc[contatos_df["cpf_cnpj"] == cnpj, "nome_fantasia"] = fantasia
        contatos_df.loc[contatos_df["cpf_cnpj"] == cnpj, "socios"] = socios_str
    else:
        logging.info(f"➕ Adicionando novo contato para CNPJ {cnpj}")
        novo_contato = {
            "nome": razao or fantasia or "Desconhecido",
            "cpf_cnpj": cnpj,
            "razao_social": razao,
            "nome_fantasia": fantasia,
            "socios": socios_str
        }
        contatos_df = pd.concat([contatos_df, pd.DataFrame([novo_contato])], ignore_index=True)

    return contatos_df

def processar_enriquecimento_contatos(caminho_cnpj_cache: str, caminho_contatos_csv: str):
    """
    Carrega o cache de CNPJs e o arquivo de contatos.
    Para cada CNPJ no cache, se o contato já existir, atualiza os campos de
    razão_social, nome_fantasia e sócios; caso contrário, adiciona um novo contato.
    Salva o arquivo de contatos atualizado.
    """
    if not os.path.isfile(caminho_cnpj_cache):
        logging.error("Arquivo de cache de CNPJ não encontrado: %s", caminho_cnpj_cache)
        return

    # Chama a função read_json passando o caminho (string) e não um file handle
    cache = read_json(caminho_cnpj_cache)

    if not os.path.isfile(caminho_contatos_csv):
        logging.info("Arquivo de contatos não encontrado, criando novo.")
        # Cria um DataFrame vazio com as colunas esperadas
        df_contatos = pd.DataFrame(columns=["cpf_cnpj", "nome", "razao_social", "nome_fantasia", "socios"])
    else:
        df_contatos = read_csv(caminho_contatos_csv, sep=";", json_columns=["socios"])

        
    df_contatos.columns = df_contatos.columns.str.strip().str.lower()

    for cnpj, cnpj_dados in cache.items():
        df_contatos = enriquecer_contato_com_dados_do_cnpj(cnpj_dados, df_contatos)

    write_csv(df_contatos, caminho_contatos_csv, sep=";", encoding="utf-8-sig", json_columns=["socios"])
    logging.info("Contatos atualizados com dados dos CNPJs salvos em: %s", caminho_contatos_csv)
