import re

def parse_detalhes_descricao(descricao: str) -> dict:
    """
    Extrai detalhes específicos da descrição, como:
      - favorecido
      - cpf_cnpj_parcial
      - cod_ted
      - observacao
    """
    dados = {
        "favorecido": "",
        "cpf_cnpj_parcial": "",
        "cod_ted": "",
        "observacao": ""
    }
    desc_up = descricao.upper()

    # Extração do favorecido usando padrão "FAV.: <nome>"
    match_fav = re.search(r"FAV\.\:\s*(.*?)(\s+Transfer|$)", descricao, flags=re.IGNORECASE)
    if match_fav:
        dados["favorecido"] = match_fav.group(1).strip()

    # Extração de nome após "Recebimento Pix" ou "Pagamento Pix"
    match_pix = re.search(
        r"(Recebimento Pix|Pagamento Pix)\s+(.*?)(\s+[0-9\*]{2,3}\.|$)",
        descricao,
        flags=re.IGNORECASE
    )
    if match_pix and not dados["favorecido"]:
        dados["favorecido"] = match_pix.group(2).strip()

    # Captura de CPF (mascarado ou completo)
    match_cpf = re.search(r"[0-9\*]{3}\.[0-9\*]{3}\.[0-9\*]{3}-[0-9\*]{2}", descricao)
    if match_cpf:
        dados["cpf_cnpj_parcial"] = match_cpf.group(0).strip()
    else:
        # Captura de CNPJ
        match_cnpj = re.search(r"([\*0-9]{2,3}\.[\*0-9]{3}\.[\*0-9]{3}\s?[\*0-9]{4}-[\*0-9]{2})", descricao)
        if match_cnpj:
            dados["cpf_cnpj_parcial"] = match_cnpj.group(1).strip()

    # Captura de código TED
    match_ted = re.search(r"CODIGO TED:\s*([A-Za-z0-9]+)", desc_up)
    if match_ted:
        original_match = re.search(r"CODIGO TED:\s*([A-Za-z0-9]+)", descricao)
        if original_match:
            dados["cod_ted"] = original_match.group(1).strip()

    # Extração de observações extras
    if "ULTRAFORMER" in desc_up:
        dados["observacao"] += "ultraformer; "
    if "DEBITO AUTOMATICO CARTAO" in desc_up:
        dados["observacao"] += "DebitoAutomaticoCartao; "

    dados["observacao"] = dados["observacao"].strip().rstrip(";")
    return dados
