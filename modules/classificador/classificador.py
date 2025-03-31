def classificar_por_descricao(descricao: str) -> str:
    """
    Atribui uma categoria à transação com base em palavras-chave na descrição.
    """
    desc_up = descricao.upper()
    if "JUROS" in desc_up:
        return "Receita Financeira"
    elif "TARIFA" in desc_up or "TAXA" in desc_up:
        return "Despesa Financeira"
    elif "PIX EMITIDO" in desc_up:
        return "Pagamento Pix"
    elif "PIX RECEBIDO" in desc_up:
        return "Recebimento Pix"
    elif "TRANSF.REALIZADA PIX" in desc_up:
        return "Transferência Interna"
    elif "DB.AUT.CRT" in desc_up or "DEBITO AUTOMATICO" in desc_up:
        return "Pagamento Cartão"
    elif "ESTORNO" in desc_up:
        return "Estorno"
    elif "CRÉD.TED" in desc_up or "TED" in desc_up:
        return "Recebimento TED"
    elif "DÉB.CONV" in desc_up:
        return "Pagamento Convênio"
    elif "SALDO ANTERIOR" in desc_up or "SALDO BLOQUEADO" in desc_up:
        return "Saldo/Informativo"
    return "Não classificado"
