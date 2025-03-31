import os
import glob
from modules.io.utils import write_json
arquivos = glob.glob("db/cnpj_cache.json*")
for arq in arquivos:
    os.remove(arq)
print("Cache antigo isolado.")
write_json({}, "db/cnpj_cache.json", ensure_ascii=False, indent=4)
print("Cache novo criado.")
