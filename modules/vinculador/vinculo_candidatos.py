# modules/vinculador/vinculo_candidatos.py

import pandas as pd
import logging
from modules.conciliador.utils import extract_tokens, normalize_string, extrair_digitos
from modules.cnpj_api.consultar import load_cache
from modules.io.utils import read_csv, write_csv, read_json, write_json
def normalizar_nome(nome: str) -> set:
    nome_normalizado = normalize_string(nome)
    tokens = extract_tokens(nome_normalizado)
    logging.debug(f"🔤 Nome original: '{nome}' → Normalizado: '{nome_normalizado}' → Tokens: {tokens}")
    return tokens

def vincular_socios_por_nome(cnpj_dados: dict, contatos_df: pd.DataFrame, min_tokens: int = 2) -> list:
    """
    Vincula os sócios (do QSA) de um CNPJ com contatos (baseados no nome).
    """
    socios = cnpj_dados.get("qsa", [])
    cnpj = cnpj_dados.get("cnpj")
    vinculos = []
    
    for socio in socios:
        # Usa o campo "nome_socio" ou "nome"; se não existir, considera string vazia
        nome_socio = (socio.get("nome_socio") or socio.get("nome", "")).strip()
        if not nome_socio:
            logging.warning(f"❗ Sócio sem nome identificado no CNPJ {cnpj}")
            continue
        
        tokens_socio = normalizar_nome(nome_socio)
        if not tokens_socio:
            continue
        
        for _, contato in contatos_df.iterrows():
            # Tenta obter o nome do contato (primeiro em minúsculas, se não, tenta "Nome")
            nome_contato = (str(contato.get("nome", "")) or str(contato.get("Nome", ""))).strip()
            if not nome_contato:
                continue
            tokens_contato = normalizar_nome(nome_contato)
            intersecao = tokens_socio.intersection(tokens_contato)
            logging.debug(f"Comparando sócio '{nome_socio}' com contato '{nome_contato}' → Interseção: {intersecao}")
            if len(intersecao) >= min_tokens:
                vinculos.append({
                    "tipo": "socio_nome",
                    "socio": nome_socio,
                    "contato": contato.to_dict(),
                    "forca": len(intersecao),
                    "empresa_cnpj": cnpj
                })
    return vinculos


def vincular_por_cnpj(cache: dict, contatos_df: pd.DataFrame) -> list:
    """
    Compara os CNPJs do cache com os contatos que possuem o mesmo CPF/CNPJ.
    """
    vinculos = []
    for cnpj, dados in cache.items():
        for _, contato in contatos_df.iterrows():
            # Usa "cpf_cnpj" em vez de "cpf/cnpj"
            contato_doc = extrair_digitos(str(contato.get("cpf_cnpj", "")))
            if contato_doc == cnpj:
                vinculos.append({
                    "tipo": "empresa_cnpj",
                    "cnpj": cnpj,
                    "empresa": dados.get("razao_social"),
                    "contato": contato.to_dict()
                })
    return vinculos

def vincular_por_cpf_parcial(lancamentos: list, contatos_df: pd.DataFrame) -> list:
    """
    Tenta vincular CPFs mascarados do extrato com os contatos.
    """
    vinculos = []
    for lanc in lancamentos:
        doc = lanc.get("cpf_cnpj_parcial", "")
        if "*" not in doc or len(doc) < 14:
            continue
        sufixo = extrair_digitos(doc)[-6:-2]
        for _, contato in contatos_df.iterrows():
            # Usa "cpf_cnpj" em vez de "cpf/cnpj"
            cpf = extrair_digitos(str(contato.get("cpf_cnpj", "")))
            if cpf.endswith(sufixo):
                vinculos.append({
                    "tipo": "cpf_parcial",
                    "cpf_parcial": doc,
                    "contato": contato.to_dict(),
                    "lancamento": lanc
                })
    return vinculos

def rodar_vinculos(caminho_cache_cnpj: str, caminho_contatos: str, lancamentos: list) -> list:
    """
    Carrega o cache de CNPJs e os contatos, aplica os vínculos (por sócios, por CNPJ e por CPF parcial)
    e retorna uma lista com todos os possíveis vínculos encontrados.
    """
    cache = load_cache(caminho_cache_cnpj)
    df_contatos = read_csv(caminho_contatos, sep=";", json_columns=["socios"])


    resultados = []
    # Para aplicar em todos os CNPJs do cache:
    for cnpj, dados in cache.items():
        resultados += vincular_socios_por_nome(dados, df_contatos)
    resultados += vincular_por_cnpj(cache, df_contatos)
    resultados += vincular_por_cpf_parcial(lancamentos, df_contatos)

    logging.info("🔎 Total de possíveis vínculos encontrados: %d", len(resultados))
    return resultados

def salvar_vinculos(vinculos: list, caminho_saida: str):
    """Salva os vínculos encontrados em um arquivo JSON."""
    import json
    write_json(vinculos, caminho_saida, ensure_ascii=False, indent=4)
