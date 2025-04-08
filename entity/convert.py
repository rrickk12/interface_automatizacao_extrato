import csv
import sys

def convert_csv_separator(input_filename: str, output_filename: str) -> None:
    with open(input_filename, newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile, delimiter=',')
        with open(output_filename, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile, delimiter=';')
            for row in reader:
                writer.writerow(row)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python convert_separator.py arquivo_entrada.csv arquivo_saida.csv")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    convert_csv_separator(input_file, output_file)
    print(f"Arquivo convertido e salvo em {output_file}")
