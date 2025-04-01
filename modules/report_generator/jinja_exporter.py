import os
import json
from jinja2 import Environment, FileSystemLoader

def load_category_config(json_path: str) -> dict:
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)

def export_jinja_report(data: list, config_path: str, output_file: str):
    config = load_category_config(config_path)
    
    # Esta é a correção definitiva:
    # Pegue os tipos exatamente como o exportador original (sem inversão!)
    tipos = sorted({tipo for tipos_list in config["tipos_por_transacao"].values() for tipo in tipos_list})
    
    env = Environment(loader=FileSystemLoader('templates'), autoescape=True)
    template = env.get_template("report.html")
    
    rendered_html = template.render(
        data=data, 
        config_json=json.dumps(config, ensure_ascii=False),
        tipos=tipos
    )
    # print(f"[DEBUG] Total de transações recebidas: {len(data)}")
    # print("[DEBUG] Primeira entrada:", data[0] if data else "Vazio")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    print(f"✅ Relatório exportado com sucesso para '{output_file}'")
