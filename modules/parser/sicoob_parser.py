import re
from bs4 import BeautifulSoup
import logging

def parse_extrato_sicoob(html_path: str) -> dict:
    """
    Faz o parse do extrato Sicoob em HTML e retorna um dicionário com:
      - header: informações do cabeçalho (data, hora, cooperativa, conta)
      - lancamentos: lista de lançamentos (data, documento, descrição, valor)
      - resumo: resumo final do extrato
    """
    logging.debug(f"Lendo extrato Sicoob do arquivo: {html_path}")
    try:
        with open(html_path, "r", encoding="utf-8") as file:
            html_content = file.read()
    except Exception as e:
        logging.exception(f"Erro ao ler o arquivo HTML: {e}")
        return {}

    soup = BeautifulSoup(html_content, "html.parser")
    result = {}

    # --- Cabeçalho ---
    header = {}
    header_table = soup.find("table", class_="texto-cabecalho-html mt-2 mb-2")
    if header_table:
        cells = header_table.find_all("td")
        if len(cells) >= 3:
            header["data_emissao"] = cells[0].get_text(strip=True)
            header["tipo_extrato"] = cells[1].get_text(strip=True)
            header["hora"] = cells[2].get_text(strip=True)
        else:
            header["data_emissao"] = header["tipo_extrato"] = header["hora"] = ""
    else:
        header["data_emissao"] = header["tipo_extrato"] = header["hora"] = ""

    cooperativa_table = soup.find("table", class_="border-botton-export-html ng-star-inserted")
    cooperativa = ""
    conta = ""
    if cooperativa_table:
        rows = cooperativa_table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True).replace(":", "").lower()
                value = cells[1].get_text(strip=True)
                if label == "cooperativa":
                    cooperativa = value
                elif label == "conta":
                    conta = value
    header["cooperativa"] = cooperativa
    header["conta"] = conta
    result["header"] = header

    # --- Lançamentos ---
    lancamentos = []
    trans_table = soup.find("table", class_="home-extrato-exportar-table-html")
    if trans_table:
        tbody = trans_table.find("tbody")
        if tbody:
            rows = tbody.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 4:
                    continue

                data = cells[0].get_text(strip=True)
                documento = cells[1].get_text(strip=True)
                descricao = cells[2].get_text(separator=" ", strip=True)
                valor_text = cells[3].get_text(strip=True)
                
                # Processa o valor extraindo o número e o sinal
                valor = 0.0
                match = re.search(r"([\d\.,]+)\s*([CD])", valor_text)
                if match:
                    valor_str = match.group(1).replace(".", "").replace(",", ".")
                    try:
                        valor = float(valor_str)
                    except Exception:
                        valor = 0.0
                    if match.group(2) == "D":
                        valor = -valor

                # Ignora lançamentos que contenham "SALDO DO DIA"
                if "SALDO DO DIA" in descricao.upper():
                    continue

                lancamentos.append({
                    "data": data,
                    "documento": documento,
                    "descricao": descricao,
                    "valor": valor
                })
    result["lancamentos"] = lancamentos

    # --- Resumo ---
    resumo = {}
    resumo_table = soup.find("table", class_="home-extrato-exportar-table-html ng-star-inserted")
    if resumo_table:
        rows = resumo_table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True).replace(":", "")
                value_str = cells[1].get_text(strip=True)
                try:
                    value = float(value_str.replace(".", "").replace(",", "."))
                except Exception:
                    value = value_str
                resumo[key] = value
    result["resumo"] = resumo

    logging.debug("Parse do extrato Sicoob concluído.")
    return result
