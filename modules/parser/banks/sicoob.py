import re
from bs4 import BeautifulSoup
import logging
from modules.parser.base_parser import BankParser
from modules.reconciler.utils import extrair_digitos

class SicoobParser(BankParser):

    def parse_transactions(self, statement_data: dict) -> list:
        """
        Processa os lançamentos, adicionando tipo de transação e extraindo CPF/CNPJ parcial.
        Para CNPJ, extrai o número completo (14 dígitos). Para CPF mascarado (***.xxx.xxx-**),
        extrai os últimos 6 dígitos.
        """
        transactions = statement_data.get("transactions", [])
        enriched = []

        for tx in transactions:
            try:
                amount = float(tx.get("amount", 0))
            except Exception:
                amount = 0.0

            tx["transaction_type"] = "Débito" if amount < 0 else "Crédito"

            desc = tx.get("description", "")
            cpf_cnpj_parcial = ""

            # Tenta extrair CPF completo (sem máscara) – retorna apenas os últimos 6 dígitos
            match_cpf = re.search(r"\d{3}[.\s]?\d{3}[.\s]?\d{3}-?\d{2}", desc)
            if match_cpf:
                cpf_cnpj_parcial = extrair_digitos(match_cpf.group(0))[-6:]

            # Tenta extrair CPF mascarado (ex: ***.985.678-**)
            if not cpf_cnpj_parcial:
                match_mascarado = re.search(r"\*{3}[.\s]?(\d{3})[.\s]?(\d{3})-\*{2}", desc)
                if match_mascarado:
                    cpf_cnpj_parcial = match_mascarado.group(1) + match_mascarado.group(2)

            # Tenta extrair CNPJ completo – agora retorna o número completo (14 dígitos)
            if not cpf_cnpj_parcial:
                match_cnpj = re.search(r"\d{2}[.\s]?\d{3}[.\s]?\d{3}[\/\s]?\d{4}-?\d{2}", desc)
                if match_cnpj:
                    cnpj = extrair_digitos(match_cnpj.group(0))
                    if len(cnpj) == 14:
                        cpf_cnpj_parcial = cnpj
                    else:
                        cpf_cnpj_parcial = cnpj[-6:]

            # Fallback: últimos 6 dígitos de qualquer número longo
            if not cpf_cnpj_parcial:
                numeros = re.findall(r"\d{6,}", desc)
                if numeros:
                    cpf_cnpj_parcial = numeros[-1][-6:]

            tx["cpf_cnpj_parcial"] = cpf_cnpj_parcial
            enriched.append(tx)

        return enriched

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

                    # Se a descrição contiver "SALDO DO DIA", pula essa linha
                    if "SALDO DO DIA" in description.upper():
                        continue

                    transactions.append({
                        "date": date,
                        "document": document,
                        "description": description,
                        "amount": amount
                    })

        # Exclui as duas últimas transações (presumindo que são sempre "SALDO BLOQUEADO ANTERIOR"
        # e "SALDO ANTERIOR")
        if len(transactions) >= 2:
            transactions = transactions[:-2]

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
