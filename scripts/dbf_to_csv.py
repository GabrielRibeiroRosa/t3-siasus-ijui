"""Converte arquivos DBF do DATASUS em CSV para LOAD DATA INFILE e gera o DDL MySQL.

Uso:
    python dbf_to_csv.py ENTRADA.dbf --csv SAIDA.csv
    python dbf_to_csv.py ENTRADA.dbf --ddl NOME_TABELA

Formato do CSV (o esperado pelos scripts de carga): separador ',', campos entre aspas, fim de
linha CRLF, uma linha de cabecalho. Os bytes de texto sao copiados sem recodificar.
Campos numericos vazios sao gravados como \\N (NULL no MySQL).
"""
import argparse
import struct
import sys

CHUNK_RECORDS = 50_000


def read_header(f):
    head = f.read(32)
    n_records, header_len, record_len = struct.unpack("<IHH", head[4:12])
    fields, offset = [], 1  # o primeiro byte do registro e o marcador de exclusao
    while True:
        desc = f.read(32)
        if not desc or desc[0] == 0x0D:
            break
        name = desc[:11].split(b"\x00")[0].decode("ascii")
        ftype = chr(desc[11])
        length, decimals = desc[16], desc[17]
        fields.append((name, ftype, length, decimals, offset))
        offset += length
    f.seek(header_len)
    return n_records, record_len, fields


def ddl(fields, table):
    cols = []
    for name, ftype, length, decimals, _ in fields:
        if ftype == "N":
            sql_type = f"DECIMAL({length},{decimals})"
        elif ftype == "D":
            sql_type = "DATE"
        else:
            sql_type = f"CHAR({length})"
        cols.append(f"  {name.lower()} {sql_type}")
    return f"CREATE TABLE {table} (\n" + ",\n".join(cols) + "\n);"


def clean_text(raw):
    value = raw.rstrip(b" \x00")
    if b"\\" in value:
        value = value.replace(b"\\", b"\\\\")
    if b'"' in value:
        value = value.replace(b'"', b'""')
    return b'"' + value + b'"'


def convert(path, out_path):
    written = deleted = 0
    with open(path, "rb") as f, open(out_path, "wb") as out:
        n_records, record_len, fields = read_header(f)
        out.write(b",".join(b'"' + x[0].lower().encode() + b'"' for x in fields) + b"\r\n")
        spec = [(o, o + l, t in "NFD", t == "D") for _, t, l, _, o in fields]
        remaining = n_records
        while remaining > 0:
            block = f.read(min(remaining, CHUNK_RECORDS) * record_len)
            if not block:
                break
            lines = []
            for start in range(0, len(block) - record_len + 1, record_len):
                rec = block[start : start + record_len]
                if rec[0] == 0x2A:  # '*': registro excluido
                    deleted += 1
                    continue
                parts = []
                for a, b, numeric, is_date in spec:
                    if numeric:
                        v = rec[a:b].strip(b" \x00")
                        if is_date and v == b"00000000":
                            v = b""
                        parts.append(v if v else b"\\N")
                    else:
                        parts.append(clean_text(rec[a:b]))
                lines.append(b",".join(parts))
            written += len(lines)
            out.write(b"\r\n".join(lines) + b"\r\n" if lines else b"")
            remaining -= len(block) // record_len
    return n_records, written, deleted


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dbf")
    ap.add_argument("--csv")
    ap.add_argument("--ddl")
    args = ap.parse_args()
    if args.ddl:
        with open(args.dbf, "rb") as f:
            print(ddl(read_header(f)[2], args.ddl))
    if args.csv:
        total, written, deleted = convert(args.dbf, args.csv)
        print(f"{args.dbf}: cabecalho={total} gravados={written} excluidos={deleted}")
        if total != written + deleted:
            sys.exit("ERRO: a contagem nao bate com o cabecalho do DBF")


if __name__ == "__main__":
    main()
