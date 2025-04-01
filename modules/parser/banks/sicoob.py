# modules/parser/banks/sicoob.py
import re
from bs4 import BeautifulSoup
import logging
from modules.parser.base_parser import BankParser

class SicoobParser(BankParser):
    def parse_statement(self) -> dict:
        """
        Faz o parse do extrato Sicoob em HTML e retorna um dicionário com cabeçalho,
        lançamentos e resumo.
        """
        logging.debug(f"Lendo extrato do arquivo: {self.file_path}")
        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
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
                header["issue_date"] = cells[0].get_text(strip=True)
                header["statement_type"] = cells[1].get_text(strip=True)
                header["time"] = cells[2].get_text(strip=True)
            else:
                header["issue_date"] = header["statement_type"] = header["time"] = ""
        else:
            header["issue_date"] = header["statement_type"] = header["time"] = ""

        cooperative_table = soup.find("table", class_="border-botton-export-html ng-star-inserted")
        cooperative = ""
        account = ""
        if cooperative_table:
            rows = cooperative_table.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).replace(":", "").lower()
                    value = cells[1].get_text(strip=True)
                    if label == "cooperativa":
                        cooperative = value
                    elif label == "conta":
                        account = value
        header["cooperative"] = cooperative
        header["account"] = account
        result["header"] = header

        # --- Lançamentos ---
        transactions = []
        trans_table = soup.find("table", class_="home-extrato-exportar-table-html")
        if trans_table:
            tbody = trans_table.find("tbody")
            if tbody:
                rows = tbody.find_all("tr")
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) < 4:
                        continue

                    date = cells[0].get_text(strip=True)
                    document = cells[1].get_text(strip=True)
                    description = cells[2].get_text(separator=" ", strip=True)
                    value_text = cells[3].get_text(strip=True)
                    
                    amount = self._parse_amount(value_text)
                    
                    # Ignora lançamentos de saldo
                    if "SALDO DO DIA" in description.upper():
                        continue

                    transactions.append({
                        "date": date,
                        "document": document,
                        "description": description,
                        "amount": amount
                    })
        result["transactions"] = transactions

        # --- Resumo ---
        summary = {}
        summary_table = soup.find("table", class_="home-extrato-exportar-table-html ng-star-inserted")
        if summary_table:
            rows = summary_table.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True).replace(":", "")
                    value_str = cells[1].get_text(strip=True)
                    try:
                        value = float(value_str.replace(".", "").replace(",", "."))
                    except Exception:
                        value = value_str
                    summary[key] = value
        result["summary"] = summary

        logging.debug("Parse do extrato Sicoob concluído.")
        return result


    def parse_transactions(self, statement_data: dict) -> list:
        """
        Processa os lançamentos, adicionando tipo de transação e extraindo CPF/CNPJ parcial.
        """
        import re

        transactions = statement_data.get("transactions", [])
        enriched = []

        for tx in transactions:
            try:
                amount = float(tx.get("amount", 0))
            except Exception:
                amount = 0.0

            tx["transaction_type"] = "Débito" if amount < 0 else "Crédito"

            desc = tx.get("description", "")

            cpf_match = re.search(r"(\*{3}\.\d{3}\.\d{3}-\*{2}|\d{3}\.\d{3}\.\d{3}-\d{2})", desc)
            cnpj_match = re.search(r"(\d{2}[.\s]?\d{3}[.\s]?\d{3}[\/\s]?\d{4}[-\s]?\d{2}|\d{14})", desc)

            if cpf_match:
                tx["cpf_cnpj_parcial"] = cpf_match.group(1)
            elif cnpj_match:
                tx["cpf_cnpj_parcial"] = cnpj_match.group(1)
            else:
                tx["cpf_cnpj_parcial"] = ""

            enriched.append(tx)

        return enriched

    def _parse_amount(self, amount_text: str) -> float:
        """
        Processa o texto do valor, removendo formatações e convertendo para float.
        """
        match = re.search(r"([\d\.,]+)\s*([CD])", amount_text)
        if match:
            value_str = match.group(1).replace(".", "").replace(",", ".")
            try:
                value = float(value_str)
            except Exception:
                value = 0.0
            if match.group(2).upper() == "D":
                value = -value
            return value
        return 0.0
