# modules/parser/__init__.py
from modules.parser.banks.sicoob import SicoobParser
# from modules.parser.banks.other_bank import OtherBankParser  # Exemplo para outro banco

def get_bank_parser(bank_name: str):
    """
    Retorna a instância do parser apropriado para o banco especificado.
    """
    bank_name_lower = bank_name.lower()
    if bank_name_lower == "sicoob":
        return SicoobParser()
    # elif bank_name_lower == "other_bank":
    #     return OtherBankParser()
    else:
        raise ValueError(f"Parser for bank '{bank_name}' is not implemented.")
