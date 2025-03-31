import os
import re

def substituir_prints_por_logging(caminho_arquivo):
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        linhas = f.readlines()

    alterado = False
    novas_linhas = []
    for linha in linhas:
        nova_linha = linha
        match = re.match(r'(\s*)print\((.*)\)', linha)
        if match:
            indentacao, conteudo = match.groups()
            # Decide entre info e debug
            nivel = "debug" if "🔤" in conteudo or "Comparando" in conteudo else "info"
            nova_linha = f"{indentacao}logging.{nivel}({conteudo})\n"
            alterado = True
        novas_linhas.append(nova_linha)

    if alterado:
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            f.writelines(novas_linhas)
        print(f"✅ Modificado: {caminho_arquivo}")

def varrer_pasta(base_path):
    for dirpath, _, filenames in os.walk(base_path):
        for file in filenames:
            if file.endswith(".py"):
                caminho = os.path.join(dirpath, file)
                substituir_prints_por_logging(caminho)

if __name__ == "__main__":
    pasta_alvo = "modules"  # ou "." para o projeto todo
    varrer_pasta(pasta_alvo)
