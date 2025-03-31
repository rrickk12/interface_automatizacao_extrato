import pandas as pd

def associar_transacoes_contatos(transacoes: list, contatos_df: pd.DataFrame) -> list:
    """
    Para cada transação no extrato, tenta associar um contato do DataFrame de contatos atualizados.
    Adiciona um novo campo "contato" em cada transação com os dados do contato correspondente.
    Se o CPF/CNPJ da transação estiver mascarado (contém "*"), utiliza correspondência por substring.
    """
    from modules.conciliador.utils import extrair_digitos

    for trans in transacoes:
        doc_trans = trans.get("cpf_cnpj_parcial", "")
        # Extrai somente os dígitos, ignorando espaços e outros caracteres
        doc_trans_normalizado = extrair_digitos(doc_trans)
        contato_encontrado = None

        # Se o campo da transação estiver mascarado, usamos busca por substring
        if "*" in doc_trans:
            for _, contato in contatos_df.iterrows():
                doc_contato = extrair_digitos(str(contato.get("cpf_cnpj", "")))
                if doc_trans_normalizado and doc_trans_normalizado in doc_contato:
                    contato_encontrado = contato.to_dict()
                    break
        else:
            # Caso contrário, utilizamos correspondência exata ou por sufixo
            for _, contato in contatos_df.iterrows():
                doc_contato = extrair_digitos(str(contato.get("cpf_cnpj", "")))
                if doc_trans_normalizado == doc_contato or doc_contato.endswith(doc_trans_normalizado):
                    contato_encontrado = contato.to_dict()
                    break

        trans["contato"] = contato_encontrado

    return transacoes


import os
import json
import logging

def export_to_html(data, output_file):
    """
    Gera um arquivo HTML formatado a partir dos dados (lista de transações com contato),
    aplicando formatação condicional para facilitar a validação.
    """
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Extrato Conciliado com Contatos</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        h2 { margin-bottom: 5px; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; vertical-align: top; }
        th { background-color: #f2f2f2; }
        .transaction { margin-bottom: 40px; padding: 10px; }
        .with-contact { background-color: #d4f7dc; } /* pastel verde */
        .without-contact { background-color: #f7d4d4; } /* pastel vermelho */
        .contact { margin-left: 20px; }
        .socios { margin-left: 40px; }
        .empty-field { background-color: #fff7b2; } /* pastel amarelo */
        .not-classified { background-color: #ffe0b3; } /* pastel laranja */
        .credito { background-color: #d4f7dc; } /* mesmo que with-contact */
        .debito { background-color: #f7d4d4; } /* mesmo que without-contact */
    </style>
</head>
<body>
    <h1>Extrato Conciliado com Contatos</h1>
"""
    # Para cada transação, cria um bloco de exibição
    for trans in data:
        # Determina a classe do bloco conforme se há contato ou não
        trans_class = "with-contact" if trans.get("contato") else "without-contact"
        documento = trans.get("documento", "Sem documento")
        html += f"<div class='transaction {trans_class}'>\n"
        html += f"<h2>Transação: {documento}</h2>\n"
        html += "<table>\n"
        # Exibe os campos da transação (exceto o contato)
        for key, value in trans.items():
            if key == "contato":
                continue
            # Aplica formatação condicional para campos específicos
            style = ""
            if key == "favorecido" and (not value or str(value).strip() == ""):
                style = "class='empty-field'"
            elif key == "categoria" and str(value).strip().lower() == "não classificado":
                style = "class='not-classified'"
            elif key == "tipo_transacao":
                if str(value).strip().lower() == "crédito":
                    style = "class='credito'"
                elif str(value).strip().lower() == "débito":
                    style = "class='debito'"
            # Converte valores complexos para string com indentação
            if isinstance(value, (list, dict)):
                value_str = json.dumps(value, ensure_ascii=False, indent=2)
            else:
                value_str = str(value)
            html += f"<tr><th>{key}</th><td {style}>{value_str}</td></tr>\n"
        html += "</table>\n"
        
        # Se houver informação de contato, exibe em bloco separado
        contato = trans.get("contato")
        if contato:
            html += "<div class='contact'>\n"
            html += "<h3>Contato</h3>\n"
            html += "<table>\n"
            for key, value in contato.items():
                style = ""
                # Se o campo for vazio, destaque com amarelo
                if not value and key != "socios":
                    style = "class='empty-field'"
                # Para a coluna "socios", se for uma lista não vazia, cria sub-tabela
                if key == "socios":
                    html += f"<tr><th>{key}</th><td>"
                    if isinstance(value, list) and value:
                        html += "<table class='socios'>\n"
                        # Cabeçalho para a tabela de sócios
                        html += "<tr>"
                        for sub_key in value[0].keys():
                            html += f"<th>{sub_key}</th>"
                        html += "</tr>\n"
                        for socio in value:
                            html += "<tr>"
                            for sub_value in socio.values():
                                html += f"<td>{sub_value}</td>"
                            html += "</tr>\n"
                        html += "</table>"
                    else:
                        html += str(value)
                    html += "</td></tr>\n"
                else:
                    html += f"<tr><th>{key}</th><td {style}>{value}</td></tr>\n"
            html += "</table>\n"
            html += "</div>\n"
        html += "</div>\n"
    
    html += "</body>\n</html>"
    
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)
        logging.info("HTML exportado com sucesso para: %s", output_file)
    except Exception as e:
        logging.error("Erro ao exportar HTML: %s", e)

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # Caminho para o JSON de entrada (ex.: o extrato conciliado com contatos)
    input_file = "extrato_conciliado_com_contatos.json"  # Altere conforme necessário
    output_file = "extrato_conciliado_com_contatos.html"
    
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        export_to_html(data, output_file)
    except Exception as e:
        logging.error("Erro ao ler o arquivo JSON de entrada: %s", e)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # Caminho para o JSON de entrada (ex.: o extrato conciliado com contatos)
    input_file = "extrato_conciliado_com_contatos.json"  # Altere conforme necessário
    output_file = "extrato_conciliado_com_contatos.html"
    
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        export_to_html(data, output_file)
    except Exception as e:
        logging.error("Erro ao ler o arquivo JSON de entrada: %s", e)
