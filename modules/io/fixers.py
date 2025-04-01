# modules/io/fixers.py

def fix_broken_csv_line(filepath: str, output_path: str):
    """
    Corrige um CSV mal formatado onde vários registros estão em uma linha só.
    Especificamente corrige casos como: ..."";"" "<cpf>";"<nome>";... → quebra linha corretamente.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Corrige espaços indevidos entre registros
    fixed = content.replace('"";"" "', '"";""\n"')

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(fixed)

    print(f"✅ Arquivo corrigido salvo em: {output_path}")
