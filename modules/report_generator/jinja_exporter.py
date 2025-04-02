import os
import json
from jinja2 import Environment, FileSystemLoader

def load_category_config(json_path: str) -> dict:
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)

def export_jinja_report(data: list, config_path: str, output_file: str, rules_path: str = "config/rules.json"):
    config = load_category_config(config_path)

    # Verifica se o arquivo de regras existe
    if os.path.exists(rules_path):
        with open(rules_path, encoding="utf-8") as f:
            regras = json.load(f)
    else:
        print("⚠️ Nenhum arquivo de regras encontrado. Usando lista vazia.")
        regras = []

    tipos = sorted({tipo for tipos_list in config["tipos_por_transacao"].values() for tipo in tipos_list})

    env = Environment(loader=FileSystemLoader('templates'), autoescape=True)
    template = env.get_template("report.html")

    rendered_html = template.render(
        data=data,
        config_json=config,         # Usar objeto direto com |tojson
        regras_json=regras,
        tipos=tipos
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    print(f"✅ Relatório exportado com sucesso para '{output_file}'")
