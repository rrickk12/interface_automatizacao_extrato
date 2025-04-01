from abc import ABC, abstractmethod

class BankParser(ABC):
    def __init__(self, file_path: str):
        """
        Inicializa o parser com o caminho do arquivo de extrato.
        """
        self.file_path = file_path

    @abstractmethod
    def parse_statement(self) -> dict:
        """
        Faz o parse do extrato bancário e retorna um dicionário contendo:
          - Cabeçalho
          - Lançamentos
          - Resumo
        """
        pass

    @abstractmethod
    def parse_transactions(self, statement_data: dict) -> list:
        """
        A partir dos dados do extrato (já lidos com parse_statement), processa e
        retorna uma lista de transações enriquecidas.
        """
        pass
