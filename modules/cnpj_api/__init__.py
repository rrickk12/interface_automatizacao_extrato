from .consultar import consultar_cnpj
from .salvar import salvar_cnpj_consultado
from .cache import load_cache, normalize_cnpj

__all__ = [
    "consultar_cnpj",
    "salvar_cnpj_consultado",
    "load_cache",
    "normalize_cnpj"
]
