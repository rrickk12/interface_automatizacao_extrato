# __init__.py para o módulo
from .enrich import enrich_contact_with_cnpj_data, process_contact_enrichment
from .link import link_full_cnpj_to_contacts, save_links_csv
from .associate import associate_transactions_with_contacts
from .aliases import integrate_contact_aliases
from .aliases import integrate_aliases

__all__ = [
    "enrich_contact_with_cnpj_data",
    "process_contact_enrichment",
    "link_full_cnpj_to_contacts",
    "save_links_csv",
    "associate_transactions_with_contacts",
    "integrate_contact_aliases",
    "integrate_aliases"
]
