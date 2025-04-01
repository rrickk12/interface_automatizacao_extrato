def classify_description(description: str, keyword_mapping: dict = None) -> str:
    """
    Classifies a transaction description into a category using a dictionary mapping.

    The default mapping is as follows (keys are tuples of keywords, values are categories):
      - ("JUROS",) -> "Receita Financeira"
      - ("TARIFA", "TAXA") -> "Despesa Financeira"
      - ("PIX EMITIDO",) -> "Pagamento Pix"
      - ("PIX RECEBIDO",) -> "Recebimento Pix"
      - ("TRANSF.REALIZADA PIX",) -> "Transferência Interna"
      - ("DB.AUT.CRT", "DEBITO AUTOMATICO") -> "Pagamento Cartão"
      - ("ESTORNO",) -> "Estorno"
      - ("CRÉD.TED", "TED") -> "Recebimento TED"
      - ("DÉB.CONV",) -> "Pagamento Convênio"
      - ("SALDO ANTERIOR", "SALDO BLOQUEADO") -> "Saldo/Informativo"

    If no keyword is found, returns "Não classificado".

    Parâmetros:
      - description: A descrição da transação.
      - keyword_mapping: (Opcional) Um dicionário customizado para mapear palavras-chave às categorias.

    Retorna:
      - Uma string com a categoria determinada.
    """
    desc_up = description.upper()
    
    if keyword_mapping is None:
        keyword_mapping = {
            ("JUROS",): "Receita Financeira",
            ("TARIFA", "TAXA"): "Despesa Financeira",
            ("PIX EMITIDO",): "Pagamento Pix",
            ("PIX RECEBIDO",): "Recebimento Pix",
            ("TRANSF.REALIZADA PIX",): "Transferência Interna",
            ("DB.AUT.CRT", "DEBITO AUTOMATICO"): "Pagamento Cartão",
            ("ESTORNO",): "Estorno",
            ("CRÉD.TED", "TED"): "Recebimento TED",
            ("DÉB.CONV",): "Pagamento Convênio",
            ("SALDO ANTERIOR", "SALDO BLOQUEADO"): "Saldo/Informativo"
        }
    
    for keywords, category in keyword_mapping.items():
        # Para cada grupo de palavras-chave, se qualquer uma estiver presente na descrição, retorna a categoria
        if any(kw in desc_up for kw in keywords):
            return category

    return "Não classificado"
