import os
import json
import logging
import pandas as pd

from modules.parser.sicoob_parser import parse_extrato_sicoob
from modules.parser.sicoob_lancamentos import parse_lancamentos_sicoob
from modules.conciliador.conciliador_contatos import (
    conciliar_extrato_contatos,
    consultar_cnpjs_em_massa
)
from modules.vinculador.vinculo_candidatos import rodar_vinculos
from modules.vinculador.vincular_cnpj_a_contatos import salvar_vinculos_csv
from modules.vinculador.enriquecedor_cnpj import processar_enriquecimento_contatos
from modules.io.utils import read_json, write_json, read_csv, write_csv
from modules.vinculador.vinculo_transacoes_contato import associar_transacoes_contatos

def setup_logging():
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        filename='app.log',  # Salva as mensagens em um arquivo
        filemode='a'         # 'a' para append; 'w' para sobrescrever
    )
    # Handler para imprimir também no console:
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(logging.Formatter(log_format))
    logging.getLogger('').addHandler(console)

def main():
    setup_logging()
    logging.info("📄 Iniciando o parsing do extrato Sicoob.")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    path_extrato_html = os.path.join(base_dir, "receipt", "extrato_sicoob3.html")
    path_temp_folder = os.path.join(base_dir, "db", "temp")
    path_cnpj_cache = os.path.join(base_dir, "db", "cnpj_cache.json")
    path_contatos_csv = os.path.join(base_dir, "entity", "contatos_atualizados.csv")
    # Arquivo auxiliar de aliases (contém os aliases de contatos)
    path_alias_csv = os.path.join(base_dir, "entity", "pessoas_cpf_MMG25.csv")

    os.makedirs(path_temp_folder, exist_ok=True)

    # Integrar aliases o mais cedo possível
    from modules.contatos.integrar_aliases import integrar_aliases_contatos
    if os.path.exists(path_alias_csv):
        if os.path.exists(path_contatos_csv):
            contatos_df = read_csv(path_contatos_csv, sep=";", json_columns=["socios"])
        else:
            # Cria um DataFrame vazio com as colunas esperadas
            contatos_df = pd.DataFrame(columns=["cpf_cnpj", "nome", "razao_social", "nome_fantasia", "socios"])
        contatos_df = integrar_aliases_contatos(path_alias_csv, contatos_df)
        write_csv(contatos_df, path_contatos_csv, sep=";", encoding="utf-8-sig", json_columns=["socios"])
        logging.info("Contatos atualizados com aliases integrados (pré-processamento).")
    else:
        logging.info("Arquivo de aliases não encontrado; pulando integração de aliases.")

    # Etapa 1: Parse do HTML do extrato
    logging.debug(f"📥 Lendo arquivo: {path_extrato_html}")
    extrato = parse_extrato_sicoob(path_extrato_html)
    logging.debug("✅ Parse do extrato concluído.")

    path_raw = os.path.join(path_temp_folder, "parsed_extrato_sicoob.json")
    write_json(extrato, path_raw, ensure_ascii=False, indent=4)
    logging.info(f"💾 Extrato salvo em: {path_raw}")

    # Etapa 2: Enriquecimento dos lançamentos
    logging.debug("🧪 Enriquecendo lançamentos do extrato.")
    lancamentos_enriquecidos = parse_lancamentos_sicoob(extrato.get("lancamentos", []))
    extrato["lancamentos_enriquecidos"] = lancamentos_enriquecidos

    path_enriched = os.path.join(path_temp_folder, "parsed_extrato_sicoob_enriched.json")
    write_json(extrato, path_enriched, ensure_ascii=False, indent=4)
    logging.info(f"💾 Lançamentos enriquecidos salvos em: {path_enriched}")

    # Etapa 3: Conciliação com contatos
    logging.info("🔍 Conciliando lançamentos com contatos.")
    conciliados = conciliar_extrato_contatos(
        extrato["lancamentos_enriquecidos"],
        caminho_contatos_csv=path_contatos_csv,
        caminho_cnpj_api_csv=path_cnpj_cache
    )
    extrato["lancamentos_conciliados"] = conciliados

    path_final = os.path.join(path_temp_folder, "parsed_extrato_sicoob_conciliado.json")
    write_json(extrato, path_final, ensure_ascii=False, indent=4)
    logging.info(f"💾 Lançamentos conciliados salvos em: {path_final}")

    # Etapa 4: Consulta de CNPJs ainda não conciliados
    logging.info("🌍 Consultando CNPJs ainda não conciliados.")
    consultar_cnpjs_em_massa(
        conciliados,
        caminho_cnpj_api_csv=path_cnpj_cache,
        caminho_contatos_csv=path_contatos_csv,
        wait_time=2
    )

    # Etapa 5: Vinculação de sócios e CPFs parciais a contatos
    logging.info("🧬 Tentando vincular sócios e CPFs parciais a contatos.")
    possiveis_vinculos = rodar_vinculos(
        caminho_cache_cnpj=path_cnpj_cache,
        caminho_contatos=path_contatos_csv,
        lancamentos=conciliados
    )
    path_vinculos_json = os.path.join(path_temp_folder, "possiveis_vinculos_completos.json")
    write_json(possiveis_vinculos, path_vinculos_json, ensure_ascii=False, indent=4)
    logging.info(f"💾 Todos os possíveis vínculos salvos em: {path_vinculos_json}")

    # Etapa extra: Exportar vínculos para CSV para verificação manual
    path_vinculos_csv = os.path.join(path_temp_folder, "possiveis_vinculos_completos.csv")
    salvar_vinculos_csv(possiveis_vinculos, path_vinculos_csv)

    # Etapa 6: Enriquecer contatos com dados dos CNPJs
    logging.info("🔄 Atualizando contatos com dados dos CNPJs.")
    processar_enriquecimento_contatos(path_cnpj_cache, path_contatos_csv)

    # Etapa 7: Associar transações aos contatos
    logging.info("🔗 Associando transações aos contatos.")
    extrato_conciliado = read_json(path_final)  # path_final é o arquivo conciliado anterior
    contatos_df = read_csv(path_contatos_csv, sep=";", json_columns=["socios"])
    transacoes = extrato_conciliado.get("lancamentos_conciliados", [])
    transacoes_com_contatos = associar_transacoes_contatos(transacoes, contatos_df)
    path_transacoes_contatos = os.path.join(path_temp_folder, "extrato_conciliado_com_contatos.json")
    write_json(transacoes_com_contatos, path_transacoes_contatos, ensure_ascii=False, indent=4)
    logging.info(f"💾 Extrato conciliado com contatos salvo em: {path_transacoes_contatos}")

    # Etapa 8: Exportar o extrato conciliado com contatos para HTML
    from modules.vinculador.vinculo_transacoes_contato import export_to_html
    path_html = os.path.join(path_temp_folder, "extrato_conciliado_com_contatos.html")
    export_to_html(transacoes_com_contatos, path_html)
    logging.info(f"💾 Extrato conciliado exportado para HTML em: {path_html}")

if __name__ == "__main__":
    main()
