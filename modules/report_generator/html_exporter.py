import os
import json

def load_category_config(json_path: str) -> dict:
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)

def generate_html_header(js_config: dict) -> str:
    js = json.dumps(js_config, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang=\"pt-BR\">
<head>
  <meta charset=\"UTF-8\">
  <title>Relatório de Transações</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f7f7f7; font-size: 14px; }}
    h1 {{ text-align: center; }}
    table {{ border-collapse: collapse; width: 100%; background-color: #fff; box-shadow: 0 0 5px rgba(0,0,0,0.1); table-layout: fixed; }}
    table, th, td {{ border: 1px solid #ccc; }}
    th, td {{ padding: 8px; text-align: left; vertical-align: top; word-wrap: break-word; white-space: normal; }}
    th {{ background-color: #e2e2e2; }}
    tr.pending {{ background-color: #fff9c4; }}
    tr.validated {{ background-color: #d0f0c0; }}
    tr.canceled {{ background-color: #ffcccb; }}
    .contato-alert {{ background-color: #ffcccc; }}
    .contato-info {{ font-size: 0.9em; line-height: 1.3em; }}
    select {{ width: 100%; padding: 4px; }}
    .status-btn {{ padding: 6px 12px; margin: 2px; cursor: pointer; font-size: 16px; }}
    .btn-valid {{ background-color: #d0f0c0; border: 1px solid #8bc34a; }}
    .btn-cancel {{ background-color: #ffcccb; border: 1px solid #f44336; }}
    .prefixo {{ font-weight: bold; margin-right: 4px; color: #d32f2f; }}
  </style>
  <script>
    const configCategorias = {js};

    function atualizarCategorias(select) {{
      const row = select.closest('tr');
      const tipoTransacao = row.getAttribute('data-tipo-transacao');
      const tipoSelecionado = select.value;
      const categoriaSelect = row.querySelector('select[name="categoria_nome"]');

      categoriaSelect.innerHTML = '<option value="">Selecione</option>';
      if (configCategorias[tipoTransacao] && configCategorias[tipoTransacao][tipoSelecionado]) {{
        configCategorias[tipoTransacao][tipoSelecionado].forEach(cat => {{
          categoriaSelect.innerHTML += `<option value="${{cat}}">${{cat}}</option>`;
        }});
      }}
    }}

    function carregarAlteracoes() {{}}
    function aplicarPreselecao() {{}}
    function setStatus(btn, status) {{
      const row = btn.closest('tr');
      row.classList.remove('pending', 'validated', 'canceled');
      row.classList.add(status);
    }}
  </script>
</head>
<body>
  <h1>Relatório de Transações</h1>
  <table>
    <thead>
      <tr>
        <th>Data</th>
        <th class=\"descricao\">Descrição</th>
        <th>Valor</th>
        <th>Tipo Transação</th>
        <th>Favorecido</th>
        <th>CPF/CNPJ Parcial</th>
        <th>Tipo Documento</th>
        <th>Contato</th>
        <th>Tipo</th>
        <th>Nome da Categoria</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>"""

def generate_table_row(item: dict, tipos: list) -> str:
    contato = item.get("contact") or {}
    contato_info = (
        f"<strong>CPF/CNPJ:</strong> {contato.get('cpf_cnpj', '')}<br>"
        f"<strong>Nome:</strong> {contato.get('nome', '')}<br>"
        f"<strong>Razão Social:</strong> {contato.get('razao_social', '')}<br>"
        f"<strong>Nome Fantasia:</strong> {contato.get('nome_fantasia', '')}"
    )
    contato_class = "contato-info"
    if item.get("tipo_documento") == "CPF" and not contato.get("cpf_cnpj"):
        contato_class += " contato-alert"

    prefixo_span = '<span class="prefixo"></span>'
    select_tipo = (
        '<select name="categoria_tipo" onchange="atualizarCategorias(this)">' +
        '<option value="">Selecione</option>' +
        ''.join([f'<option value="{tipo}">{tipo}</option>' for tipo in tipos]) +
        '</select>'
    )
    select_nome = '<select name="categoria_nome"><option value="">Selecione</option></select>'
    btn_status = (
        '<button class="status-btn btn-valid" onclick="setStatus(this, \"validated\")">✅</button>'
        '<button class="status-btn btn-cancel" onclick="setStatus(this, \"canceled\")">❌</button>'
    )

    return f"""
      <tr data-id="{item.get('id', '')}" data-contato-cpf="{contato.get('cpf_cnpj', '')}" data-tipo-transacao="{item.get('tipo_transacao', '')}" data-contato-nome="{(contato.get('nome') or '').strip().lower()}" class="pending">
        <td>{item.get('data', '')}</td>
        <td class="descricao">{item.get('descricao', '')}</td>
        <td>{item.get('valor_absoluto', '')}</td>
        <td>{item.get('tipo_transacao', '')}</td>
        <td>{item.get('favorecido', '')}</td>
        <td>{item.get('cpf_cnpj_parcial', '')}</td>
        <td>{item.get('tipo_documento', '')}</td>
        <td class="{contato_class}">{contato_info}</td>
        <td>{select_tipo}</td>
        <td>{prefixo_span}{select_nome}</td>
        <td>{btn_status}</td>
      </tr>"""

def generate_html_footer() -> str:
    return """
    </tbody>
  </table>
  <p>As alterações são salvas automaticamente no seu navegador (LocalStorage).</p>
</body>
</html>"""

def export_report(data: list, config_path: str, output_file: str):
    config = load_category_config(config_path)
    tipos = sorted(set(t for v in config.values() for t in v))

    html_parts = [generate_html_header(config)]
    for item in data:
        html_parts.append(generate_table_row(item, tipos))
    html_parts.append(generate_html_footer())

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html_parts))
    print(f"Relatório exportado com sucesso para '{output_file}'")