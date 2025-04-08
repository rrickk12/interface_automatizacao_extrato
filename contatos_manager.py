import pandas as pd
import re
import os
import logging

# Configura o logging
logging.basicConfig(level=logging.INFO)

CSV_EXISTENTE_PATH = "entity/contatos_atualizados.csv"
CSV_NOVOS_PATH = "./contatos.csv"
CSV_SAIDA = "entity/contatos_integrado.csv"

MAIN_COLS = ["cpf_cnpj", "nome", "razao_social", "nome_fantasia", "socios"]

def normalizar_documento(doc):
    digitos = re.sub(r"\D", "", str(doc))
    if len(digitos) <= 11:
        return digitos.zfill(11)
    return digitos.zfill(14)

def carregar_csv(path, sep=";"):
    if os.path.exists(path):
        df = pd.read_csv(path, sep=sep, dtype=str).fillna("")
        if "cpf_cnpj" in df.columns:
            df["cpf_cnpj"] = df["cpf_cnpj"].apply(normalizar_documento)
        return df
    else:
        logging.warning(f"⚠️ Arquivo não encontrado: {path}")
        return pd.DataFrame(columns=MAIN_COLS)

def garantir_colunas(df):
    for col in MAIN_COLS:
        if col not in df.columns:
            df[col] = ""
    ordered = MAIN_COLS + [c for c in df.columns if c not in MAIN_COLS]
    return df[ordered]

def integrar_contatos():
    df_existente = carregar_csv(CSV_EXISTENTE_PATH)
    df_novos = carregar_csv(CSV_NOVOS_PATH)

    logging.info(f"📄 Existentes: {len(df_existente)} contatos")
    logging.info(f"📄 Novos: {len(df_novos)} contatos")

    df_total = pd.concat([df_existente, df_novos], ignore_index=True)

    # Verificação de duplicatas com nomes conflitantes
    duplicatas = df_total[df_total.duplicated("cpf_cnpj", keep=False)]
    conflitos = duplicatas.groupby("cpf_cnpj").filter(lambda x: len(x["nome"].unique()) > 1)
    if not conflitos.empty:
        logging.warning("⚠️ Conflitos de duplicidade encontrados com nomes diferentes:")
        logging.warning(conflitos[["cpf_cnpj", "nome"]].drop_duplicates().to_string(index=False))

    # Remove duplicatas mantendo o primeiro
    df_total.drop_duplicates(subset=["cpf_cnpj"], keep="first", inplace=True)

    df_total = garantir_colunas(df_total)

    os.makedirs(os.path.dirname(CSV_SAIDA), exist_ok=True)
    df_total.to_csv(CSV_SAIDA, sep=";", index=False, encoding="utf-8-sig", quoting=1)

    logging.info(f"✅ Contatos integrados salvos em: {CSV_SAIDA}")
    logging.info(f"📊 Total final: {len(df_total)} contatos")

if __name__ == "__main__":
    integrar_contatos()
