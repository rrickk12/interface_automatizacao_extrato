import os
import re
import unicodedata
import pandas as pd
from modules.io.utils import read_csv, write_json, write_csv, read_json

def normalize_text(text: str) -> str:
    """
    Remove acentos, espaços extras e converte o texto para minúsculas.
    """
    if not isinstance(text, str):
        return text
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    return text.strip().lower()
