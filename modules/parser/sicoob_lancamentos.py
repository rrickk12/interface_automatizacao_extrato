def parse_transactions_sicoob(transactions: list) -> list:
    """
    Processa e enriquece uma lista de lançamentos do extrato Sicoob.
    """
    enriched = []
    for tx in transactions:
        try:
            amount = float(tx.get("amount", 0))
        except Exception:
            amount = 0.0
        tx["transaction_type"] = "Débito" if amount < 0 else "Crédito"
        enriched.append(tx)
    return enriched
