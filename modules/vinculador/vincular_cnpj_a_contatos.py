#vincular_cnpj_a_contatos.py
import pandas as pd
import os
from modules.conciliador.utils import normalize_string, extract_tokens
import logging
from modules.io.utils import write_json, write_csv
def normalizar_nome(nome: str) -> set:
    nome_normalizado = normalize_string(nome)
    return extract_tokens(nome_normalizado)

def vincular_cnpj_completo_a_contatos(cnpj_dados: dict, contatos_df: pd.DataFrame, min_tokens: int = 2) -> list:
    """
    Tenta vincular razão social, nome fantasia e sócios de um CNPJ a contatos conhecidos.
    """
    contatos_df.columns = contatos_df.columns.str.strip().str.lower()
    cnpj = cnpj_dados.get("cnpj", "")
    razao_social = cnpj_dados.get("razao_social", "")
    nome_fantasia = cnpj_dados.get("nome_fantasia", "")
    socios = cnpj_dados.get("qsa", [])

    todos_vinculos = []

    def procurar_por_nome(nome_alvo, tipo_vinculo):
        tokens_alvo = normalizar_nome(nome_alvo)
        for _, contato in contatos_df.iterrows():
            nome_contato = contato.get("nome", "")
            if not nome_contato:
                continue
            tokens_contato = normalizar_nome(nome_contato)
            intersecao = tokens_alvo.intersection(tokens_contato)
            if len(intersecao) >= min_tokens:
                vinculo = contato.to_dict()
                vinculo.update({
                    "tipo_vinculo": tipo_vinculo,
                    "nome_origem": nome_alvo,
                    "forca_vinculo": len(intersecao),
                    "cnpj_origem": cnpj,
                    "empresa_origem": razao_social or nome_fantasia
                })
                todos_vinculos.append(vinculo)

    # Verifica razão social e nome fantasia
    if razao_social:
        procurar_por_nome(razao_social, "razao_social")
    if nome_fantasia:
        procurar_por_nome(nome_fantasia, "nome_fantasia")

    # Verifica os sócios
    for socio in socios:
        nome_socio = socio.get("nome_socio") or socio.get("nome", "")
        if nome_socio:
            procurar_por_nome(nome_socio, "socio")

    return todos_vinculos

def salvar_vinculos_csv(vinculos: list, caminho_csv: str):
    """
    Salva os vínculos encontrados em um arquivo CSV para verificação manual.
    Cria a pasta de destino se necessário.
    """
    if not vinculos:
        logging.info("⚠️ Nenhum vínculo para salvar.")
        return

    df = pd.DataFrame(vinculos)
    write_csv(df, caminho_csv, sep=";", encoding="utf-8-sig")