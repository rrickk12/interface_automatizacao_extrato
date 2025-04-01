import requests
import logging
from modules.cnpj_api.utils import normalize_cnpj

# --- Chave da API CNPJa ---
CNPJA_API_KEY = "d12f6d8b-38b0-4a48-8d7b-cc1777e64b70-12a23afa-7155-48f7-9c54-7753adee310c"

def consultar_cnpj_api(cnpj: str, fonte: str = "cnpja") -> dict:
    """
    Consulta um CNPJ na fonte especificada ("cnpja" ou "brasilapi") e retorna um dicionário com dados padronizados.
    """
    cnpj = normalize_cnpj(cnpj)
    
    if fonte == "cnpja":
        try:
            url = f"https://api.cnpja.com/office/{cnpj}"
            headers = {"Authorization": CNPJA_API_KEY}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return parse_cnpja_response(response.json())
        except Exception as e:
            logging.error(f"Erro na consulta à CNPJa para {cnpj}: {e}")
            return {"erro": str(e)}

    elif fonte == "brasilapi":
        try:
            url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()  # Se desejar: parse_brasilapi_response()
        except Exception as e:
            logging.error(f"Erro na consulta à BrasilAPI para {cnpj}: {e}")
            return {"erro": str(e)}
    
    else:
        erro_msg = f"Fonte de dados desconhecida: {fonte}"
        logging.error(erro_msg)
        return {"erro": erro_msg}


def parse_cnpja_response(data: dict) -> dict:
    """
    Transforma a resposta da CNPJa em um formato padronizado, compatível com o restante do sistema.
    """
    company = data.get("company", {})
    members = company.get("members", [])
    socios = []

    for member in members:
        person = member.get("person", {})
        if person.get("name"):
            socios.append({
                "nome_socio": person["name"],
                "tipo": person.get("type"),
                "faixa_etaria": person.get("age"),
                "tax_id": person.get("taxId", "")
            })

    return {
        "cnpj": data.get("taxId", ""),
        "razao_social": company.get("name"),
        "nome_fantasia": data.get("alias") or "",
        "qsa": socios
    }
