import logging
import re
import json
from modules.classificador.classificador import classificar_por_descricao
from modules.parser.descricao_parser import parse_detalhes_descricao

def classificar_valor(valor: float) -> str:
    """
    Retorna o tipo da transação baseado no valor.
    """
    if valor > 0:
        return "Crédito"
    elif valor < 0:
        return "Débito"
    else:
        return "Indefinido"

def classificar_documento(documento: str) -> str:
    """
    Determina se o documento é numérico ou textual.
    """
    doc = documento.strip()
    return "numérico" if doc.isdigit() else "texto"

def extract_detalhes_adicionais(descricao: str) -> dict:
    """
    Extrai informações adicionais da descrição usando expressões regulares.
    - Verifica se a transação é interna (presença de "mesma tit").
    - Tenta extrair um nome de favorecido após "REM.:".
    - Extrai um CNPJ, se presente, usando um padrão simples.
    - Em transferências PIX, tenta extrair o nome da instituição.
    """
    detalhes = {}
    
    # Transferência interna
    if re.search(r'\bmesma tit\b', descricao, flags=re.IGNORECASE):
        detalhes['transferencia_interna'] = True
    else:
        detalhes['transferencia_interna'] = False

    # Extrai favorecido após "REM.:"
    match_fav = re.search(r'REM\.?:\s*([^-\n]+)', descricao, flags=re.IGNORECASE)
    if match_fav:
        detalhes['favorecido_extraido'] = match_fav.group(1).strip()

    # Extrai um CNPJ (padrão simples: 00.000.000/0000-00)
    match_cnpj = re.search(r'(\d{2}\.\d{3}\.\d{3}\/\d{4}-\d{2})', descricao)
    if match_cnpj:
        detalhes['cnpj_extraido'] = match_cnpj.group(1).strip()

    # Em transferências PIX, tenta extrair a instituição (texto logo após "pix")
    if "pix" in descricao.lower():
        match_inst = re.search(r'pix\s*[-:]?\s*(.*?)\s*(?:\n|$)', descricao, flags=re.IGNORECASE)
        if match_inst:
            detalhes['instituicao'] = match_inst.group(1).strip()
    
    return detalhes

def merge_detalhes(d1: dict, d2: dict) -> dict:
    """
    Mescla dois dicionários de detalhes, com d2 sobrescrevendo d1 em caso de conflito.
    """
    merged = d1.copy()
    merged.update(d2)
    return merged

def parse_lancamento(lanc: dict) -> dict:
    """
    Processa e enriquece um lançamento específico do extrato Sicoob.
    
    Além de extrair as informações básicas, a função:
      - Extrai detalhes da descrição usando a função original e uma camada adicional.
      - Se a transação for identificada como transferência interna (ex.: "mesma tit"),
        ajusta a categoria para "Transferência Interna" e, se necessário, preenche o campo 'favorecido'.
      - Adiciona campos extras (como 'transferencia_interna', 'instituicao' e 'cnpj_extraido') para
        facilitar análises futuras.
    """
    try:
        valor = float(lanc.get("valor", 0))
    except Exception:
        valor = 0.0

    documento = str(lanc.get("documento", "")).strip()
    descricao = str(lanc.get("descricao", "")).strip()

    # Extrai os detalhes existentes e os adicionais
    detalhes_base = parse_detalhes_descricao(descricao)  # Função já existente
    detalhes_adic = extract_detalhes_adicionais(descricao)
    detalhes = merge_detalhes(detalhes_base, detalhes_adic)

    # Define a categoria inicialmente a partir da descrição
    categoria = classificar_por_descricao(descricao)
    # Ajuste para transferências internas
    if detalhes.get("transferencia_interna"):
        categoria = "Transferência Interna"
        # Se o favorecido estiver vazio, preenche com o valor extraído ou um texto padrão
        if not detalhes.get("favorecido", "").strip():
            detalhes["favorecido"] = detalhes.get("favorecido_extraido", "Transferência Interna")

    lanc_enriquecido = {
        "data": lanc.get("data", "").strip(),
        "documento": documento,
        "doc_tipo": classificar_documento(documento),
        "descricao": descricao,
        "valor": valor,
        "valor_absoluto": abs(valor),
        "tipo_transacao": classificar_valor(valor),
        "categoria": categoria,
        "favorecido": detalhes.get("favorecido", ""),
        "cpf_cnpj_parcial": detalhes.get("cpf_cnpj_parcial", ""),
        "cod_ted": detalhes.get("cod_ted", ""),
        "observacao": detalhes.get("observacao", "")
    }
    
    # Acrescenta campos extras para análise
    lanc_enriquecido.update({
        "transferencia_interna": detalhes.get("transferencia_interna", False),
        "instituicao": detalhes.get("instituicao", ""),
        "cnpj_extraido": detalhes.get("cnpj_extraido", "")
    })
    
    return lanc_enriquecido

def parse_lancamentos_sicoob(lancamentos: list) -> list:
    """
    Processa uma lista de lançamentos do extrato Sicoob, retornando os lançamentos enriquecidos.
    """
    logging.debug("Iniciando o processamento dos lançamentos do extrato Sicoob.")
    return [parse_lancamento(lanc) for lanc in lancamentos]
