import pandas as pd
from modules.conciliador.utils import normalize_string, extract_tokens
import os
import logging
def normalizar_nome(nome: str) -> set:
    """
    Normaliza o nome e extrai tokens únicos (sem acento, minúsculo, sem símbolos).
    """
    nome_normalizado = normalize_string(nome)
    tokens = extract_tokens(nome_normalizado)
    logging.debug(f"🔤 Nome original: '{nome}' → Normalizado: '{nome_normalizado}' → Tokens: {tokens}")
    return tokens

def vincular_socios_a_contatos(cnpj_dados: dict, contatos_df: pd.DataFrame, min_tokens: int = 2) -> list:
    """
    Tenta vincular sócios do CNPJ a contatos conhecidos, comparando tokens normalizados.
    """
    contatos_df.columns = contatos_df.columns.str.strip().str.lower()

    socios = cnpj_dados.get("qsa", [])
    cnpj = cnpj_dados.get("cnpj")
    possiveis_vinculos = []

    logging.info(f"🔍 Verificando {len(socios)} sócios para o CNPJ {cnpj}")

    for socio in socios:
        nome_socio = socio.get("nome_socio") or socio.get("nome", "")
        nome_socio = nome_socio.strip()

        if not nome_socio:
            logging.info("⚠️ Sócio sem nome, ignorado.")
            continue

        tokens_socio = normalizar_nome(nome_socio)
        if not tokens_socio:
            logging.info(f"⚠️ Tokens vazios para sócio '{nome_socio}', ignorando.")
            continue

        encontrou = False
        for _, contato in contatos_df.iterrows():
            nome_contato = contato.get("nome", "").strip()
            if not nome_contato:
                continue

            tokens_contato = normalizar_nome(nome_contato)
            intersecao = tokens_socio.intersection(tokens_contato)

            logging.debug(f"Comparando sócio '{nome_socio}' com contato '{nome_contato}' → Interseção: {intersecao}")

            if len(intersecao) >= min_tokens:
                vinculo = contato.to_dict()
                vinculo.update({
                    "possivel_vinculo_cnpj": cnpj,
                    "via_qsa_nome": nome_socio,
                    "forca_vinculo": len(intersecao)
                })
                possiveis_vinculos.append(vinculo)
                logging.info(f"✅ Vínculo identificado: {nome_socio} → {nome_contato} (força {len(intersecao)})")
                encontrou = True

        if not encontrou:
            logging.info(f"❌ Nenhum vínculo encontrado para sócio '{nome_socio}'.")

    logging.info(f"🔗 Total de vínculos encontrados: {len(possiveis_vinculos)}")
    return possiveis_vinculos

def salvar_vinculos_csv(vinculos: list, caminho_csv: str):
    """
    Salva os vínculos encontrados em um arquivo CSV para verificação manual.
    Cria a pasta de destino se necessário.
    """
    if not vinculos:
        logging.info("⚠️ Nenhum vínculo para salvar.")
        return

    os.makedirs(os.path.dirname(caminho_csv), exist_ok=True)
    df = pd.DataFrame(vinculos)
    df.to_csv(caminho_csv, index=False, sep=";", encoding="utf-8-sig")
    logging.info(f"💾 Vínculos salvos em: {caminho_csv}")
