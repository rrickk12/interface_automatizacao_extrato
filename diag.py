import csv

caminho = "entity/contatos_atualizados.csv"

with open(caminho, newline='', encoding='utf-8') as f:
    first_line = f.readline()
    delimitador = ";" if ";" in first_line else ","
    f.seek(0)

    reader = csv.reader(f, delimiter=delimitador)
    header = next(reader)
    num_cols = len(header)
    print(f"Delimitador detectado: '{delimitador}'")
    print(f"Número de colunas esperado: {num_cols}")

    for i, row in enumerate(reader, start=2):
        if len(row) != num_cols:
            print(f"[Linha {i}] Colunas encontradas: {len(row)} - Conteúdo: {row}")
