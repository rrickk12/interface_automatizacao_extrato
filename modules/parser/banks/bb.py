import ofxparse
import re
import logging
from modules.parser.base_parser import BankParser
from modules.reconciler.utils import extrair_digitos

class BBParser(BankParser):
    def parse_statement(self) -> dict:
        # Tenta primeiro usar ofxparse para extrair o extrato
        with open(self.file_path, "r", encoding="latin-1") as f:
            ofx = ofxparse.OfxParser.parse(f)
        
        stmt = None
        if hasattr(ofx, 'statement'):
            stmt = ofx.statement
        elif hasattr(ofx, 'bankmsgsrsv1'):
            stmt = ofx.bankmsgsrsv1.stmttrnrs[0].stmtrs
        elif hasattr(ofx, 'creditmsgsrsv1'):
            stmt = ofx.creditmsgsrsv1.stmttrnrs[0].stmtrs
        elif hasattr(ofx, 'account'):
            stmt = ofx.account
        elif hasattr(ofx, 'accounts') and ofx.accounts:
            stmt = ofx.accounts[0]
        
        # Se os atributos essenciais não estiverem presentes, utiliza o método manual
        if not (hasattr(stmt, "transactions") and hasattr(stmt, "ledger_balance") and hasattr(stmt, "bankacctfrom")):
            logging.warning("Extrato incompleto via ofxparse, utilizando método manual.")
            return self.manual_parse_ofx()
        
        header = {
            "issue_date": stmt.dtend.strftime("%d/%m/%Y") if hasattr(stmt, "dtend") and hasattr(stmt.dtend, "strftime") else stmt.dtend,
            "statement_type": "EXTRATO DE CONTA CORRENTE",
            "time": "",  # OFX geralmente não traz horário
            "cooperative": "BANCO DO BRASIL",
            "account": f"{stmt.bankacctfrom.acctid} / {stmt.bankacctfrom.accttype}"
        }
        
        transactions = []
        for t in stmt.transactions:
            transactions.append({
                "date": t.dtposted.strftime("%d/%m/%Y") if hasattr(t.dtposted, "strftime") else t.dtposted,
                "document": t.fitid if t.fitid else "Pix",
                "description": t.memo.strip() if t.memo else "",
                "amount": float(t.trnamt)
            })
        
        summary = {
            "Saldo em conta corrente": float(stmt.ledger_balance.amount),
            "Saldo disponível": float(stmt.ledger_balance.amount)
        }
        
        result = {
            "header": header,
            "transactions": transactions,
            "summary": summary
        }
        logging.debug("Parse do extrato BB (OFX) concluído via ofxparse.")
        return result

    def manual_parse_ofx(self) -> dict:
        # Método manual para extrair dados do arquivo OFX usando regex, adequado para OFX SGML
        with open(self.file_path, "r", encoding="latin-1") as f:
            content = f.read()
        
        bankacctfrom_match = re.search(
            r"<BANKACCTFROM>\s*<BANKID>(.*?)\s*<ACCTID>(.*?)\s*<ACCTTYPE>(.*?)\s*",
            content,
            re.DOTALL
        )
        if bankacctfrom_match:
            bankid, acctid, accttype = bankacctfrom_match.groups()
        else:
            bankid, acctid, accttype = "", "", ""
        
        dtasof_match = re.search(r"<LEDGERBAL>.*?<DTASOF>(\d+)", content, re.DOTALL)
        dtasof = dtasof_match.group(1) if dtasof_match else ""
        
        ledger_match = re.search(r"<LEDGERBAL>.*?<BALAMT>(-?[\d.,]+)", content, re.DOTALL)
        ledger = float(ledger_match.group(1).replace(",", ".")) if ledger_match else 0.0
        
        transactions = []
        for trn in re.findall(r"<STMTTRN>(.*?)</STMTTRN>", content, re.DOTALL):
            dtposted_match = re.search(r"<DTPOSTED>(\d+)", trn)
            trnamt_match = re.search(r"<TRNAMT>(-?[\d.,]+)", trn)
            fitid_match = re.search(r"<FITID>(.*?)\s", trn)
            # Captura o MEMO até o próximo '<'
            memo_match = re.search(r"<MEMO>([^<]+)", trn)
            dtposted = dtposted_match.group(1) if dtposted_match else ""
            trnamt = trnamt_match.group(1) if trnamt_match else "0.0"
            fitid = fitid_match.group(1).strip() if fitid_match else ""
            memo = memo_match.group(1).strip() if memo_match else ""
            transactions.append({
                "date": dtposted,
                "document": fitid if fitid else "Pix",
                "description": memo,
                "amount": float(trnamt.replace(",", "."))
            })
        
        header = {
            "issue_date": dtasof,
            "statement_type": "EXTRATO DE CONTA CORRENTE",
            "time": "",
            "cooperative": "BANCO DO BRASIL",
            "account": f"{acctid} / {accttype}"
        }
        
        summary = {
            "Saldo em conta corrente": ledger,
            "Saldo disponível": ledger
        }
        
        result = {
            "header": header,
            "transactions": transactions,
            "summary": summary
        }
        logging.debug("Parse manual do extrato BB (OFX) concluído.")
        return result

    def parse_transactions(self, statement_data: dict) -> list:
        txs = statement_data.get("transactions", [])
        enriched = []
        for tx in txs:
            try:
                amount = float(tx.get("amount", 0))
            except Exception:
                amount = 0.0
            tx["transaction_type"] = "Débito" if amount < 0 else "Crédito"
            
            desc = tx.get("description", "")
            cpf_cnpj_parcial = ""
            match_cpf = re.search(r"\d{3}[.\s]?\d{3}[.\s]?\d{3}-?\d{2}", desc)
            if match_cpf:
                cpf_cnpj_parcial = extrair_digitos(match_cpf.group(0))[-6:]
            if not cpf_cnpj_parcial:
                match_mascarado = re.search(r"\*{3}[.\s]?(\d{3})[.\s]?(\d{3})-\*{2}", desc)
                if match_mascarado:
                    cpf_cnpj_parcial = match_mascarado.group(1) + match_mascarado.group(2)
            if not cpf_cnpj_parcial:
                match_cnpj = re.search(r"\d{2}[.\s]?\d{3}[.\s]?\d{3}[\/\s]?\d{4}-?\d{2}", desc)
                if match_cnpj:
                    cpf_cnpj_parcial = extrair_digitos(match_cnpj.group(0))[-6:]
            if not cpf_cnpj_parcial:
                numeros = re.findall(r"\d{6,}", desc)
                if numeros:
                    cpf_cnpj_parcial = numeros[-1][-6:]
            tx["cpf_cnpj_parcial"] = cpf_cnpj_parcial
            enriched.append(tx)
        
        enriched = self._remove_cancelling_transactions(enriched)
        return enriched

    def _normalize_description(self, desc: str) -> str:
        """
        Normaliza a descrição removendo palavras indesejadas e espaços extras.
        """
        words_to_remove = ["ESTORNO", "DÉBITO", "DE", "-"]
        norm = desc.upper()
        for word in words_to_remove:
            norm = norm.replace(word, "")
        return " ".join(norm.split()).strip()

    def _remove_cancelling_transactions(self, transactions: list) -> list:
        """
        Para cada transação de crédito com 'ESTORNO' na descrição, procura uma transação de débito 
        com a mesma data e valor (em módulo) e com descrições normalizadas iguais, removendo ambos.
        """
        to_remove = set()
        for i, tx_credit in enumerate(transactions):
            if tx_credit["transaction_type"].upper() == "CRÉDITO" and "ESTORNO" in tx_credit["description"].upper():
                norm_credit = self._normalize_description(tx_credit["description"])
                for j, tx_debit in enumerate(transactions):
                    if i == j:
                        continue
                    if (tx_debit["transaction_type"].upper() == "DÉBITO" and
                        tx_credit["date"] == tx_debit["date"] and
                        abs(tx_credit["amount"]) == abs(tx_debit["amount"])):
                        norm_debit = self._normalize_description(tx_debit["description"])
                        if norm_credit == norm_debit:
                            to_remove.add(i)
                            to_remove.add(j)
                            logging.info("Removendo transações que se anulam: %s e %s", tx_credit, tx_debit)
                            break
        return [tx for idx, tx in enumerate(transactions) if idx not in to_remove]
