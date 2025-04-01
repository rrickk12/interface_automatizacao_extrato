def normalize_cnpj(cnpj: str) -> str:
    return "".join(filter(str.isdigit, cnpj)).zfill(14)
