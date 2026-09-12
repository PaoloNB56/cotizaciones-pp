#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import glob

# Carpeta donde están los .txt (por defecto, la del propio script)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Carpeta de salida para los JSON que va a consumir Portfolio Performance
OUTPUT_DIR = os.path.join(BASE_DIR, "FCI")


def convertir_archivo_txt(path_txt: str) -> None:
    nombre_txt = os.path.basename(path_txt)
    simbolo = os.path.splitext(nombre_txt)[0]  # BCACCA.txt -> BCACCA

    print(f"\nProcesando {nombre_txt} (símbolo {simbolo})...")

    # Leer el JSON original (Balanz)
    try:
        with open(path_txt, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  !! No se pudo leer/parsing JSON de {nombre_txt}: {e}")
        return

    historico = data.get("historico")
    if not isinstance(historico, list):
        print(f"  !! El archivo {nombre_txt} no tiene la clave 'historico' con una lista.")
        return

    # Convertir al formato simple que usará PP
    quotes = []
    for item in historico:
        try:
            fecha = item["fecha"]              # 'YYYY-MM-DD'
            valor = float(item["valorcuotaparte"])
        except (KeyError, TypeError, ValueError):
            # Si alguna entrada viene mal, la salteamos
            continue

        quotes.append({
            "date": fecha,
            "close": valor
        })

    if not quotes:
        print(f"  !! No se generó ninguna cotización para {nombre_txt}.")
        return

    # Asegurar carpeta de salida
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Archivo de salida: mismo nombre, extensión .json
    out_path = os.path.join(OUTPUT_DIR, f"{simbolo}.json")

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(quotes, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  !! Error al escribir {out_path}: {e}")
        return

    print(f"  -> Generado {out_path} con {len(quotes)} registros.")


def main():
    print(f"Buscando archivos .txt en {BASE_DIR} ...")
    txt_files = glob.glob(os.path.join(BASE_DIR, "*.txt"))

    if not txt_files:
        print("No se encontraron archivos .txt.")
        return

    for path_txt in txt_files:
        convertir_archivo_txt(path_txt)

    print("\nListo. JSON para PP en la carpeta:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
