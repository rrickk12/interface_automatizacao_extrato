import json
import re

def identificar_tipo_documento(doc_str: str) -> str:
    """Remove caracteres não numéricos e verifica se é CPF (11 dígitos) ou CNPJ (14 dígitos)."""
    if not doc_str:
        return "Indefinido"
    apenas_digitos = re.sub(r'\D', '', doc_str)
    if len(apenas_digitos) == 11:
        return "CPF"
    elif len(apenas_digitos) == 14:
        return "CNPJ"
    return "Indefinido"

def inferir_pelo_texto(texto: str) -> str:
    """Heurística simples para inferir se é CPF ou CNPJ a partir de um texto."""
    if not texto:
        return "Indefinido"
    texto_limpo = texto.replace('\n', ' ')
    if '0001' in texto_limpo:
        return "CNPJ"
    padrao_cpf_mascarado = re.compile(r'\*{1,3}\.\d{3}\.\d{3}-\*{1,2}')
    if padrao_cpf_mascarado.search(texto_limpo):
        return "CPF"
    return "Indefinido"

# ------------------------------------------------------------
# Carrega e processa os dados do JSON, removendo linhas de saldo
# ------------------------------------------------------------
input_file = "./db/temp/extrato_conciliado_com_contatos.json"
with open(input_file, "r", encoding="utf-8") as f:
    dados = json.load(f)

dados_classificados = []
for i, registro in enumerate(dados):
    descricao = registro.get("descricao", "")
    # Ignora linhas com SALDO BLOQUEADO ANTERIOR ou SALDO ANTERIOR
    if "SALDO BLOQUEADO ANTERIOR" in descricao or "SALDO ANTERIOR" in descricao:
        continue

    entrada = {
        "id": i,  # Índice para identificar a linha
        "data": registro.get("data"),
        "descricao": descricao,
        "valor_absoluto": registro.get("valor_absoluto"),
        "tipo_transacao": registro.get("tipo_transacao"),
        "favorecido": registro.get("favorecido"),
        "cpf_cnpj_parcial": registro.get("cpf_cnpj_parcial")
    }
    contato = registro.get("contato") or {}
    entrada["contato"] = {
        "cpf_cnpj": contato.get("cpf_cnpj"),  # Pode ser None
        "nome": contato.get("nome"),
        "razao_social": contato.get("razao_social"),
        "nome_fantasia": contato.get("nome_fantasia")
    }
    doc_cpf_cnpj = contato.get("cpf_cnpj")
    if doc_cpf_cnpj:
        tipo_documento = identificar_tipo_documento(str(doc_cpf_cnpj))
    else:
        parcial = registro.get("cpf_cnpj_parcial", "") or registro.get("favorecido", "")
        tipo_documento = inferir_pelo_texto(parcial)
    entrada["tipo_documento"] = tipo_documento
    dados_classificados.append(entrada)

# ------------------------------------------------------------
# Dicionário de Categorias (fácil de modificar)
# ------------------------------------------------------------
categorias = [
    {"nome": "Locação de equipamentos", "tipo": "Recebimentos"},
    {"nome": "Despesas financeiras", "tipo": "Não informado"},
    {"nome": "Custos operacionais", "tipo": "Não informado"},
    {"nome": "Despesas administrativas", "tipo": "Não informado"},
    {"nome": "Manutenção de ativos", "tipo": "Não informado"},
    {"nome": "Venda de ativos", "tipo": "Recebimentos"},
    {"nome": "Compra de ativos", "tipo": "Não informado"},
    {"nome": "Marketing", "tipo": "Despesas fixas"},
    {"nome": "Comercial", "tipo": "Pessoas"},
    {"nome": "Empréstimo", "tipo": "Não informado"},
    {"nome": "Locação de equipamento", "tipo": "Não informado"},
    # Entradas para regras
    {"nome": "Transferência interna", "tipo": "Não informado"},
    {"nome": "Pessoas", "tipo": "Pessoas"},
    {"nome": "Recebimentos", "tipo": "Recebimentos"},
    {"nome": "Locacao de maquinas", "tipo": "Locacao de maquinas"},
    {"nome": "Despesas administrativas", "tipo": "Pessoas"},
    {"nome": "Custos operacionais", "tipo": "Despesas fixas"}
]

nomes_categorias = [cat["nome"] for cat in categorias]
tipos_categorias = sorted(list({cat["tipo"] for cat in categorias}))

# ------------------------------------------------------------
# Gera o conteúdo HTML com as alterações e regras solicitadas
# ------------------------------------------------------------
html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>Relatório de Transações</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 20px;
      background-color: #f7f7f7;
      font-size: 14px;
    }}
    h1 {{
      text-align: center;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      background-color: #fff;
      box-shadow: 0 0 5px rgba(0,0,0,0.1);
      table-layout: fixed;
    }}
    table, th, td {{
      border: 1px solid #ccc;
    }}
    th, td {{
      padding: 8px;
      text-align: left;
      vertical-align: top;
      word-wrap: break-word;
      white-space: normal;
    }}
    th {{
      background-color: #e2e2e2;
    }}
    /* Cores pastel para o status */
    tr.pending {{
      background-color: #fff9c4; /* Amarelo pastel */
    }}
    tr.validated {{
      background-color: #d0f0c0; /* Verde pastel */
    }}
    tr.canceled {{
      background-color: #ffcccb; /* Vermelho pastel */
    }}
    /* Destaca o contato em vermelho se o CPF estiver ausente e for CPF */
    .contato-alert {{
      background-color: #ffcccc;
    }}
    .contato-info {{
      font-size: 0.9em;
      line-height: 1.3em;
    }}
    select {{
      width: 100%;
      padding: 4px;
    }}
    /* Botões de status usando emoticons */
    .status-btn {{
      padding: 6px 12px;
      margin: 2px;
      cursor: pointer;
      font-size: 16px;
    }}
    .btn-valid {{
      background-color: #d0f0c0;
      border: 1px solid #8bc34a;
    }}
    .btn-cancel {{
      background-color: #ffcccb;
      border: 1px solid #f44336;
    }}
    /* Espaço para prefixo (ex: !BOLETO!) */
    .prefixo {{
      font-weight: bold;
      margin-right: 4px;
      color: #d32f2f;
    }}
  </style>
  <script>
    /* Dicionário de categorias */
    const categorias = {{
      {", ".join([f'"{cat["nome"]}": "{cat["tipo"]}"' for cat in categorias])}
    }};

    /* Regras de pré-seleção para a descrição.
       Cada regra pode retornar um objeto com:
         - nome: para o dropdown "Nome da Categoria"
         - tipo: para o dropdown "Tipo"
         - prefixo: opcional (ex: "!BOLETO!")
    */
    const regrasDescricao = [
      {{
        regex: /CR\\s+ANTECIPAÇÃO/i,
        suggestion: {{ nome: "Locação de equipamentos", tipo: "Recebimentos" }}
      }},
      {{
        regex: /CRED\\.TRANSF\\.CONTAS/i,
        suggestion: {{ nome: "Locação de equipamentos", tipo: "Recebimentos" }}
      }},
      {{
        regex: /^PIX\\s+EMITIDO/i,
        process: function(descricao) {{
          let tokens = descricao.split(" ");
          if(tokens.length < 3) return null;
          let ultimo = tokens[tokens.length - 1];
          if(ultimo.includes("***")) {{
            return {{ nome: "Comercial", tipo: "Pessoas" }};
          }}
          return null;
        }}
      }},
      {{
        regex: /DÉB\\.TIT\\.COMPE/i,
        suggestion: {{ prefixo: "!BOLETO!" }}
      }}
      // Outras regras podem ser adicionadas aqui
    ];

    /* Aplica as regras de pré-seleção com base na descrição */
    function aplicarRegrasDescricao(descricao) {{
      for(let regra of regrasDescricao) {{
        if(regra.regex && regra.regex.test(descricao)) {{
          if(regra.process) {{
            let sugestao = regra.process(descricao);
            if(sugestao) return sugestao;
          }} else if(regra.suggestion) {{
            return regra.suggestion;
          }}
        }}
      }}
      return null;
    }}

    /* Atualiza o "Tipo" quando o "Nome" é alterado */
    function atualizarTipo(selectNome) {{
      const row = selectNome.closest('tr');
      const selectTipo = row.querySelector('select[name="categoria_tipo"]');
      const nomeSelecionado = selectNome.value;
      if(nomeSelecionado && categorias[nomeSelecionado]) {{
        selectTipo.value = categorias[nomeSelecionado];
      }} else {{
        selectTipo.value = "";
      }}
      salvarLinha(row);
    }}

    /* Define o status usando os botões: 'validated' (✅) ou 'canceled' (❌) */
    function setStatus(btn, status) {{
      const row = btn.closest('tr');
      row.classList.remove('pending', 'validated', 'canceled');
      row.classList.add(status);
      salvarLinha(row, status);
    }}

    /* Salva os dados da linha no localStorage */
    function salvarLinha(row, statusFromButton) {{
      const id = row.getAttribute('data-id');
      let status = statusFromButton || "pending";
      const categoriaNome = row.querySelector('select[name="categoria_nome"]').value;
      const categoriaTipo = row.querySelector('select[name="categoria_tipo"]').value;
      let linhaData = {{
        status: status,
        categoriaNome: categoriaNome,
        categoriaTipo: categoriaTipo
      }};
      let dadosSalvos = JSON.parse(localStorage.getItem('dadosTransacoes')) || {{}};
      dadosSalvos[id] = linhaData;
      localStorage.setItem('dadosTransacoes', JSON.stringify(dadosSalvos));
    }}

    /* Carrega as alterações salvas no localStorage */
    function carregarAlteracoes() {{
      let dadosSalvos = JSON.parse(localStorage.getItem('dadosTransacoes'));
      if(!dadosSalvos) return;
      document.querySelectorAll('tr[data-id]').forEach(row => {{
        const id = row.getAttribute('data-id');
        if(dadosSalvos[id]) {{
          let linhaData = dadosSalvos[id];
          row.querySelector('select[name="categoria_nome"]').value = linhaData.categoriaNome;
          row.querySelector('select[name="categoria_tipo"]').value = linhaData.categoriaTipo;
          row.classList.remove('pending', 'validated', 'canceled');
          row.classList.add(linhaData.status);
        }}
      }});
    }}

    /* Aplica a pré-seleção nas linhas sem dados salvos, considerando regras adicionais */
    function aplicarPreselecao() {{
      document.querySelectorAll('tr[data-id]').forEach(row => {{
        const id = row.getAttribute('data-id');
        let dadosSalvos = JSON.parse(localStorage.getItem('dadosTransacoes')) || {{}};
        if(!dadosSalvos[id]) {{
          let descricao = row.querySelector('.descricao').innerText.trim();
          let tipoTransacao = row.getAttribute('data-tipo-transacao').trim().toLowerCase();
          let contatoCpf = row.getAttribute('data-contato-cpf').trim();
          let contatoNome = row.getAttribute('data-contato-nome').toLowerCase();
          let sugestao = null;
          // Regra: Se o contato (nome) contiver "zoop" ou "ticket log"
          if(contatoNome.includes("zoop") || contatoNome.includes("ticket log")) {{
              sugestao = {{ nome: "Custos operacionais", tipo: "Despesas fixas" }};
          }}
          // Regra: Se o CPF do contato for "40498567869" ou "31687798818"
          else if(contatoCpf === "40498567869" || contatoCpf === "31687798818") {{
              sugestao = {{ nome: "Despesas administrativas", tipo: "Pessoas" }};
          }}
          // Regra: Se for crédito e o contato for de pessoa física (CPF com 11 dígitos)
          else if(tipoTransacao === "crédito" && contatoCpf && contatoCpf.length === 11) {{
              sugestao = {{ nome: "Locacao de maquinas", tipo: "Locacao de maquinas" }};
          }}
          // Caso contrário, aplica as regras baseadas na descrição
          else {{
              sugestao = aplicarRegrasDescricao(descricao);
          }}

          if(sugestao) {{
            if(sugestao.nome) {{
              row.querySelector('select[name="categoria_nome"]').value = sugestao.nome;
              if(categorias[sugestao.nome]) {{
                row.querySelector('select[name="categoria_tipo"]').value = categorias[sugestao.nome];
              }}
            }}
            if(sugestao.tipo) {{
              row.querySelector('select[name="categoria_tipo"]').value = sugestao.tipo;
            }}
            if(sugestao.prefixo) {{
              let spanPrefixo = row.querySelector('.prefixo');
              if(spanPrefixo) {{
                spanPrefixo.innerText = sugestao.prefixo + " ";
              }}
            }}
          }}
        }}
      }});
    }}

    window.onload = function() {{
      carregarAlteracoes();
      aplicarPreselecao();
    }};
  </script>
</head>
<body>
  <h1>Relatório de Transações</h1>
  <table>
    <thead>
      <tr>
        <th>Data</th>
        <th class="descricao">Descrição</th>
        <th>Valor</th>
        <th class="tipoTransacao">Tipo Transação</th>
        <th>Favorecido</th>
        <th>CPF/CNPJ Parcial</th>
        <th>Tipo Documento</th>
        <th>Contato</th>
        <th>Nome da Categoria</th>
        <th>Tipo</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
"""

for item in dados_classificados:
    contato_data = item["contato"]
    # Monta a célula de contato
    contato_info = (
        f"<strong>CPF/CNPJ:</strong> {contato_data.get('cpf_cnpj', '')}<br>"
        f"<strong>Nome:</strong> {contato_data.get('nome', '')}<br>"
        f"<strong>Razão Social:</strong> {contato_data.get('razao_social', '')}<br>"
        f"<strong>Nome Fantasia:</strong> {contato_data.get('nome_fantasia', '')}"
    )
    # Se o tipo_documento for CPF mas o campo no contato estiver ausente, destaca em vermelho
    contato_class = "contato-info"
    if item["tipo_documento"] == "CPF" and not contato_data.get("cpf_cnpj"):
        contato_class += " contato-alert"

    prefixo_span = '<span class="prefixo"></span>'
    select_nome = f"""<select name="categoria_nome" onchange="atualizarTipo(this)">
      <option value="">Selecione</option>
      {''.join([f'<option value="{nome}">{nome}</option>' for nome in nomes_categorias])}
    </select>"""
    select_tipo = f"""<select name="categoria_tipo">
      <option value="">Selecione</option>
      {''.join([f'<option value="{tipo}">{tipo}</option>' for tipo in tipos_categorias])}
    </select>"""
    # Botões de status com emoticons
    btn_status = f"""
      <button class="status-btn btn-valid" onclick="setStatus(this, 'validated')">✅</button>
      <button class="status-btn btn-cancel" onclick="setStatus(this, 'canceled')">❌</button>
    """
    data_contato = contato_data.get("cpf_cnpj", "")
    data_tipo_transacao = item.get("tipo_transacao", "")
    data_contato_nome = (contato_data.get("nome") or "").strip()
    html_content += f"""
      <tr data-id="{item.get('id', '')}" data-contato-cpf="{data_contato}" data-tipo-transacao="{data_tipo_transacao}" data-contato-nome="{data_contato_nome}" class="pending">
        <td>{item.get('data', '')}</td>
        <td class="descricao">{item.get('descricao', '')}</td>
        <td>{item.get('valor_absoluto', '')}</td>
        <td class="tipoTransacao">{item.get('tipo_transacao', '')}</td>
        <td>{item.get('favorecido', '')}</td>
        <td>{item.get('cpf_cnpj_parcial', '')}</td>
        <td>{item.get('tipo_documento', '')}</td>
        <td class="{contato_class}">{contato_info}</td>
        <td>{prefixo_span}{select_nome}</td>
        <td>{select_tipo}</td>
        <td>{btn_status}</td>
      </tr>
    """

html_content += """
    </tbody>
  </table>
  <p>As alterações são salvas automaticamente no seu navegador (LocalStorage).</p>
</body>
</html>
"""

# Exporta o HTML para um arquivo
output_file = "relatorio_transacoes_com_categorias_status.html"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Relatório exportado com sucesso para '{output_file}'.")
