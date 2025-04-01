import time
import logging

from modules.cnpj_api.consultar import consultar_cnpj
from modules.reconciler.utils import extrair_digitos
from modules.cnpj_api.salvar import salvar_cnpj_consultado


def consultar_cnpjs_em_massa(
    lancamentos: list,
    caminho_cnpj_api_csv: str,
    wait_time: float = 2.0,
    fonte: str = "cnpja"
) -> None:
    """
    Varre os lançamentos para identificar CNPJs (14 dígitos) sem dados válidos nos contatos conciliados,
    remove duplicatas e consulta cada CNPJ na API.
    """
    unique_cnpjs = set()

    for lanc in lancamentos:
        doc = lanc.get("cpf_cnpj_parcial", "")
        digitos = extrair_digitos(doc)

        contatos = lanc.get("possiveis_contatos", [])
        ja_tem_dados_validos = any(
            contato.get("razao_social") and contato.get("razao_social") != "Exemplo Ltda"
            for contato in contatos
        )

        if len(digitos) == 14 and not ja_tem_dados_validos:
            unique_cnpjs.add(digitos)

    unique_cnpjs = sorted(unique_cnpjs)
    total = len(unique_cnpjs)
    logging.info(f"🔍 Consultando {total} CNPJs não conciliados...")

    for i, cnpj in enumerate(unique_cnpjs, start=1):
        logging.info(f"[{i}/{total}] Consultando CNPJ: {cnpj} ...")
        resultado_api = consultar_cnpj(cnpj, cache_path=caminho_cnpj_api_csv, fonte=fonte)

        if resultado_api.get("erro"):
            logging.warning(f"Erro: {resultado_api.get('erro')}")
        else:
            logging.info("✅ OK")

        salvar_cnpj_consultado(caminho_cnpj_api_csv, resultado_api)
        time.sleep(wait_time)
