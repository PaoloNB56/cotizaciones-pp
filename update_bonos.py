from __future__ import annotations

import json
import os
from io import BytesIO
from datetime import date, datetime, timedelta
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

import requests
import urllib3

# Desactivar warnings por verify=False (solo si lo usamos)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === CONFIGURACIÓN GENERAL ===

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# QuickTrade: Excel históricos
QT_BASE_URL = "https://quicktrade.com.ar/Financial/GetExcelReporteCotizacionesHistoricas"

# Instrumentos que vas a bajar de QuickTrade
# clave = símbolo que usarás en PP (y nombre del JSON)
# "simbolo" = id de QuickTrade, "fecha_desde" en formato dd/MM/yyyy
INSTRUMENTOS_QT = {
    #"T15D5": {"simbolo": "28073", "fecha_desde": "30/11/2024"},
    "AL35":  {"simbolo": "13996", "fecha_desde": "30/11/2024"},
    "AE38":  {"simbolo": "14006", "fecha_desde": "01/12/2024"},
    #"AE38D":  {"simbolo": "14055", "fecha_desde": "01/12/2024"}, 
    #"T13F6": {"simbolo": "28920", "fecha_desde": "01/12/2024"},
    "AL41":  {"simbolo": "13998", "fecha_desde": "01/12/2024"},
    "AN29":  {"simbolo": "36985", "fecha_desde": "01/12/2024"},
    #"TTM26":  {"simbolo": "30303", "fecha_desde": "01/12/2024"},
    #"TTJ26":  {"simbolo": "30302", "fecha_desde": "01/12/2024"},
    #"T30J6":  {"simbolo": "30077", "fecha_desde": "01/12/2024"},
    "X29Y6":  {"simbolo": "36686", "fecha_desde": "01/12/2024"},
    "AO28":  {"simbolo": "38405", "fecha_desde": "01/04/2026"},
    "S30N6": {"simbolo": "37006", "fecha_desde": "01/01/2000"},  # Todo el histórico disponible
}

# Dólares desde Dolarazo (API JSON)
DOLARAZO_BASE_URL = "https://dolarazo.com.ar/api/v1/cotizaciones"

DOLARAZO_DOLARES_CONFIG = {
    "CCL": {
        "symbol": "CCL",                 # nombre del archivo JSON -> CCL.json
        "fecha_desde_iso": "2024-01-01", # AAAA-MM-DD desde cuando querés el histórico
        "casa": "contadoconliqui",
    },
    "MEP": {
        "symbol": "MEP",                 # nombre del archivo JSON -> MEP.json
        "fecha_desde_iso": "2024-01-01", # AAAA-MM-DD desde cuando querés el histórico
        "casa": "bolsa",
    },
}

# Para tu caso con error de certificado en QuickTrade
VERIFY_SSL_QT = False  # si más adelante arreglás certificados, podés poner True

HEADERS_DOLARAZO = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,*/*",
    "Referer": "https://dolarazo.com.ar/",
}

HEADERS_QT = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,*/*",
    "Referer": "https://quicktrade.com.ar/",
}


# === FECHAS ===

def hoy_dd_mm_aaaa() -> str:
    """Para QuickTrade (dd/MM/yyyy)."""
    return datetime.today().strftime("%d/%m/%Y")


def hoy_yyyy_mm_dd() -> str:
    """Para APIs con fechas ISO (yyyy-MM-dd)."""
    return datetime.today().strftime("%Y-%m-%d")


# === UTILIDADES ===

def normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia nombres de columnas (espacios, BOM, etc.)."""
    df = df.copy()
    df.columns = [str(c).strip().lstrip("\ufeff") for c in df.columns]
    return df


def df_a_registros(df: pd.DataFrame) -> list[dict]:
    """
    QuickTrade -> lista de {"date": "YYYY-MM-DD", "close": 102.65}
    (BYMA usa precios *1000, así que dividimos por 1000).
    """
    import pandas as pd

    df = normalizar_columnas(df)

    for col in ["Fecha", "Cierre"]:
        if col not in df.columns:
            raise ValueError(
                f"Columna '{col}' no encontrada en el archivo. "
                f"Columnas disponibles: {list(df.columns)}"
            )

    registros: list[dict] = []

    for _, row in df.iterrows():
        fecha_val = row["Fecha"]

        cierre_val = row["Cierre"]
        if pd.isna(cierre_val):
            continue
        if not str(fecha_val).strip():
            continue
        registros.append(cotizacion_quicktrade_a_pp(fecha_val, cierre_val))

    registros.sort(key=lambda r: r["date"])
    return registros


def cotizacion_quicktrade_a_pp(fecha_val, cierre_val) -> dict:
    """Conversión compartida por pandas (PC) y openpyxl (runner portátil)."""
    if isinstance(fecha_val, (datetime, date)):
        dt = fecha_val
    else:
        dt = datetime.strptime(str(fecha_val).strip(), "%d/%m/%Y")
    return {"date": dt.strftime("%Y-%m-%d"), "close": round(float(cierre_val) / 1000.0, 6)}


def descargar_contenido_quicktrade(simbolo_qt: str, fecha_desde: str, fecha_hasta: str) -> bytes:
    """Descarga común, sin dependencia de pandas ni del sistema operativo."""
    params = {
        "simbolo": simbolo_qt,
        "fechaDesde": fecha_desde,
        "fechaHasta": fecha_hasta,
        "especieVencimiento": "24 hs.",
    }

    print(f"  -> Descargando QuickTrade simbolo={simbolo_qt} desde {fecha_desde} hasta {fecha_hasta}...")
    resp = requests.get(QT_BASE_URL, params=params, headers=HEADERS_QT, verify=VERIFY_SSL_QT, timeout=30)
    resp.raise_for_status()

    return resp.content


def descargar_excel_quicktrade(simbolo_qt: str, fecha_desde: str, fecha_hasta: str) -> pd.DataFrame:
    """Baja el XLSX de QuickTrade y lo lee con pandas (flujo local original)."""
    import pandas as pd

    buffer = BytesIO(descargar_contenido_quicktrade(simbolo_qt, fecha_desde, fecha_hasta))
    df = pd.read_excel(buffer, engine="openpyxl")
    return df


def guardar_json_simbolo(simbolo: str, registros: list[dict]):
    """Guarda la lista de registros en <SIMBOLO>.json."""
    ruta = os.path.join(BASE_DIR, f"{simbolo}.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(registros, f, ensure_ascii=False, indent=2)

    print(f"  -> Guardado {len(registros)} registros en {ruta}")


def cargar_json_simbolo(simbolo: str) -> list[dict]:
    """Lee <SIMBOLO>.json si existe; si no, devuelve lista vacía."""
    ruta = os.path.join(BASE_DIR, f"{simbolo}.json")
    if not os.path.exists(ruta):
        return []

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"  !! No se pudo leer {ruta}: {e}. Se reconstruye desde el inicio.")
        return []

    if not isinstance(data, list):
        print(f"  !! {ruta} no contiene una lista. Se reconstruye desde el inicio.")
        return []

    return data


def filtrar_registros_en_rango(registros: list[dict], fecha_desde: date, fecha_hasta: date) -> list[dict]:
    """Normaliza registros existentes y conserva sólo los que están dentro del rango configurado."""
    filtrados: list[dict] = []

    for registro in registros:
        try:
            fecha = date.fromisoformat(str(registro["date"]))
            cierre = float(registro["close"])
        except (KeyError, TypeError, ValueError):
            continue

        if fecha_desde <= fecha <= fecha_hasta:
            filtrados.append({"date": fecha.strftime("%Y-%m-%d"), "close": round(cierre, 6)})

    filtrados.sort(key=lambda r: r["date"])
    return filtrados


def parsear_fecha_actualizacion(fecha_actualizacion: str) -> date:
    """Convierte la fecha ISO del endpoint actual de Dolarazo a date."""
    return datetime.fromisoformat(fecha_actualizacion.replace("Z", "+00:00")).date()


def registro_dolarazo_a_pp(row: dict, fecha_desde: date, fecha_hasta: date) -> dict | None:
    """Convierte un registro de Dolarazo a {"date": "YYYY-MM-DD", "close": venta}."""
    try:
        fecha = date.fromisoformat(str(row["fecha"]))
        cierre = float(row["venta"])
    except (KeyError, TypeError, ValueError):
        return None

    if fecha < fecha_desde or fecha > fecha_hasta:
        return None

    # Dolarazo replica sábados y domingos; los JSON del proyecto guardan ruedas hábiles.
    if fecha.weekday() >= 5:
        return None

    return {"date": fecha.strftime("%Y-%m-%d"), "close": round(cierre, 6)}


def parsear_registros_dolarazo_historico(payload: dict, fecha_desde: date, fecha_hasta: date) -> list[dict]:
    """Extrae registros históricos desde la respuesta JSON de Dolarazo."""
    if not payload.get("ok"):
        raise ValueError("Dolarazo respondió ok=false")

    data = payload.get("data")
    if not isinstance(data, list):
        raise ValueError("la respuesta histórica de Dolarazo no contiene una lista en 'data'")

    registros: list[dict] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        registro = registro_dolarazo_a_pp(row, fecha_desde, fecha_hasta)
        if registro is not None:
            registros.append(registro)

    registros.sort(key=lambda r: r["date"])
    return registros


def parsear_registro_dolarazo_actual(payload: dict, fecha_desde: date, fecha_hasta: date) -> list[dict]:
    """Extrae la cotización vigente desde la respuesta JSON de Dolarazo."""
    if not payload.get("ok"):
        raise ValueError("Dolarazo respondió ok=false")

    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("la respuesta actual de Dolarazo no contiene un objeto en 'data'")

    try:
        fecha = parsear_fecha_actualizacion(str(data["fechaActualizacion"]))
    except (KeyError, TypeError, ValueError) as e:
        raise ValueError(f"fechaActualizacion inválida en Dolarazo: {e}") from e

    registro = registro_dolarazo_a_pp(
        {
            "fecha": fecha.strftime("%Y-%m-%d"),
            "venta": data.get("venta"),
        },
        fecha_desde,
        fecha_hasta,
    )
    return [registro] if registro is not None else []


def descargar_json_dolarazo(path: str) -> dict:
    """Descarga un endpoint de Dolarazo y devuelve el JSON."""
    url = f"{DOLARAZO_BASE_URL}/{path}"
    print(f"  -> Descargando Dolarazo {path}...")
    resp = requests.get(url, headers=HEADERS_DOLARAZO, timeout=30)
    resp.raise_for_status()
    return resp.json()


def descargar_registros_dolarazo(casa: str, fecha_desde: date, fecha_hasta: date) -> list[dict]:
    """Descarga histórico + cotización actual de Dolarazo."""
    registros = parsear_registros_dolarazo_historico(
        descargar_json_dolarazo(f"historicas/{casa}"),
        fecha_desde,
        fecha_hasta,
    )
    registros.extend(
        parsear_registro_dolarazo_actual(
            descargar_json_dolarazo(f"dolares/{casa}"),
            fecha_desde,
            fecha_hasta,
        )
    )
    return registros


# === ACTUALIZACIONES ===

def actualizar_todos_quicktrade(fecha_hasta_ddmmyyyy: str):
    """Actualiza todos los bonos configurados en INSTRUMENTOS_QT."""
    print(f"Actualizando datos de QuickTrade (fechaHasta={fecha_hasta_ddmmyyyy})...\n")

    for simbolo_pp, cfg in INSTRUMENTOS_QT.items():
        simbolo_qt = cfg["simbolo"]
        fecha_desde = cfg["fecha_desde"]

        try:
            df = descargar_excel_quicktrade(simbolo_qt, fecha_desde, fecha_hasta_ddmmyyyy)
            registros = df_a_registros(df)
            guardar_json_simbolo(simbolo_pp, registros)
        except Exception as e:
            print(f"  !! Error al procesar {simbolo_pp} ({simbolo_qt}): {e}")

        print()

    print("Actualización de QuickTrade terminada.\n")


def actualizar_dolar_dolarazo(nombre: str, config: dict, fecha_hasta_iso: str):
    """Descarga una cotización de dólar desde Dolarazo y la guarda como JSON."""
    simbolo = config["symbol"]
    fecha_desde_iso = config["fecha_desde_iso"]
    casa = config["casa"]
    fecha_desde = date.fromisoformat(fecha_desde_iso)
    fecha_hasta = date.fromisoformat(fecha_hasta_iso)

    if fecha_hasta < fecha_desde:
        print(f"  !! Rango inválido para {nombre}: {fecha_desde_iso} > {fecha_hasta_iso}.")
        return

    print(f"Actualizando {nombre} (Dolarazo) desde {fecha_desde_iso} hasta {fecha_hasta_iso}...")
    registros_existentes = filtrar_registros_en_rango(
        cargar_json_simbolo(simbolo),
        fecha_desde,
        fecha_hasta,
    )

    fecha_desde_descarga = fecha_desde
    if registros_existentes:
        fechas_existentes = [date.fromisoformat(r["date"]) for r in registros_existentes]
        primera_fecha = min(fechas_existentes)
        ultima_fecha = max(fechas_existentes)

        if primera_fecha > fecha_desde:
            print(
                f"  -> {simbolo}.json empieza en {primera_fecha:%Y-%m-%d}; "
                "se mantiene el histórico local y se actualiza incrementalmente."
            )

        if ultima_fecha >= fecha_hasta:
            print(f"  -> {simbolo}.json ya llega hasta {fecha_hasta_iso}; no hace falta descargar Dolarazo.")
            print(f"Actualización de {nombre} terminada.\n")
            return

        fecha_desde_descarga = ultima_fecha + timedelta(days=1)
        print(
            f"  -> {simbolo}.json llega hasta {ultima_fecha:%Y-%m-%d}; "
            f"se descarga desde {fecha_desde_descarga:%Y-%m-%d}."
        )
    else:
        print(f"  -> No hay datos locales válidos para {simbolo}; se descarga el rango completo.")

    registros_descargados: list[dict] = []
    if fecha_desde_descarga <= fecha_hasta:
        try:
            registros_descargados.extend(descargar_registros_dolarazo(casa, fecha_desde_descarga, fecha_hasta))
        except requests.HTTPError as e:
            print(f"  !! Error HTTP al descargar {nombre}: {e}. No se sobrescribe {simbolo}.json.")
            return
        except requests.RequestException as e:
            print(f"  !! Error de red al descargar {nombre}: {e}. No se sobrescribe {simbolo}.json.")
            return
        except ValueError as e:
            print(f"  !! Error al parsear {nombre}: {e}. No se sobrescribe {simbolo}.json.")
            return

    registros_por_fecha = {r["date"]: r for r in registros_existentes}
    registros_por_fecha.update({r["date"]: r for r in registros_descargados})

    if not registros_por_fecha:
        print(f"  !! No se encontraron registros para {nombre}. No se sobrescribe {simbolo}.json.")
        return

    registros = list(registros_por_fecha.values())
    registros.sort(key=lambda r: r["date"])

    if registros == registros_existentes:
        print(f"  -> No hubo registros nuevos para {simbolo}; no se modifica {simbolo}.json.")
        print(f"Actualización de {nombre} terminada.\n")
        return

    guardar_json_simbolo(simbolo, registros)
    print(f"Actualización de {nombre} terminada.\n")


def actualizar_ccl_dolarazo(fecha_hasta_iso: str):
    """Descarga el CCL de Dolarazo y lo guarda como CCL.json."""
    actualizar_dolar_dolarazo("CCL", DOLARAZO_DOLARES_CONFIG["CCL"], fecha_hasta_iso)


def actualizar_mep_dolarazo(fecha_hasta_iso: str):
    """Descarga el MEP de Dolarazo y lo guarda como MEP.json."""
    actualizar_dolar_dolarazo("MEP", DOLARAZO_DOLARES_CONFIG["MEP"], fecha_hasta_iso)


# === SERVIDOR HTTP ===

def iniciar_servidor_http(puerto: int = 8000):
    """Levanta un servidor HTTP en BASE_DIR (para que PP lea los JSON)."""
    os.chdir(BASE_DIR)
    server = ThreadingHTTPServer(("0.0.0.0", puerto), SimpleHTTPRequestHandler)
    print(f"Servidor HTTP en marcha en http://localhost:{puerto}/")
    print("Dejá esta ventana abierta mientras PP descargue las cotizaciones.\n")
    server.serve_forever()


# === MAIN ===

if __name__ == "__main__":
    fecha_hasta_ddmmyyyy = hoy_dd_mm_aaaa()
    fecha_hasta_iso = hoy_yyyy_mm_dd()

    actualizar_todos_quicktrade(fecha_hasta_ddmmyyyy)
    actualizar_ccl_dolarazo(fecha_hasta_iso)
    actualizar_mep_dolarazo(fecha_hasta_iso)

    iniciar_servidor_http(puerto=8000)
