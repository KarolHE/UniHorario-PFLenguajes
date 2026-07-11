import subprocess
import os
import json
import re

PROLOG_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "..", "prolog"
))

CONSULTAS_PL  = os.path.join(PROLOG_DIR, "consultas.pl")
HECHOS_PL     = os.path.join(PROLOG_DIR, "hechos.pl")
RESULTADOS_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "..", "data", "resultados"
))


def _prolog_disponible() -> bool:
    """Verifica que SWI-Prolog (swipl) esté instalado."""
    try:
        subprocess.run(["swipl", "--version"], capture_output=True, timeout=5)
        return True
    except FileNotFoundError:
        return False


def _ejecutar_consulta(consulta: str, timeout: int = 30) -> dict:
    """
    Ejecuta una consulta Prolog sobre consultas.pl.
    Retorna {"ok": True, "salida": "..."} o {"ok": False, "error": "..."}
    """
    if not _prolog_disponible():
        return {
            "ok": False,
            "error": (
                "SWI-Prolog no está instalado. "
                "Descárgalo en https://www.swi-prolog.org/Download.html"
            )
        }

    if not os.path.exists(HECHOS_PL):
        return {
            "ok": False,
            "error": "hechos.pl no encontrado. Primero exporta los datos desde Scala."
        }

    if not os.path.exists(CONSULTAS_PL):
        return {
            "ok": False,
            "error": "consultas.pl no encontrado en la carpeta prolog/."
        }

    try:
        resultado = subprocess.run(
            ["swipl", "-g", consulta, "-g", "halt", CONSULTAS_PL],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=PROLOG_DIR
        )
        if resultado.returncode == 0:
            return {"ok": True, "salida": resultado.stdout.strip()}
        else:
            return {
                "ok": False,
                "error": resultado.stderr.strip() or "Error en Prolog."
            }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Prolog tardó demasiado generando combinaciones."}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def generar_combinaciones() -> dict:
    """
    Pide a Prolog todas las combinaciones de secciones sin conflictos.
    Guarda el resultado en data/resultados/combinaciones_validas.json
    Retorna {"ok": True, "combinaciones": [...]} o {"ok": False, "error": "..."}
    """
    res = _ejecutar_consulta("generar_combinaciones_json", timeout=60)
    if not res["ok"]:
        return res

    # Intentar parsear JSON de la salida de Prolog
    try:
        combinaciones = json.loads(res["salida"])
    except json.JSONDecodeError:
        # Intentar extraer JSON embebido en la salida
        match = re.search(r"\[.*\]", res["salida"], re.DOTALL)
        if match:
            try:
                combinaciones = json.loads(match.group())
            except Exception:
                combinaciones = []
        else:
            combinaciones = []

    os.makedirs(RESULTADOS_DIR, exist_ok=True)
    ruta = os.path.join(RESULTADOS_DIR, "combinaciones_validas.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(combinaciones, f, ensure_ascii=False, indent=2)

    return {"ok": True, "combinaciones": combinaciones}


def detectar_conflictos_prolog() -> dict:
    """
    Pide a Prolog que explique todos los conflictos encontrados.
    Retorna {"ok": True, "conflictos": [...]} o {"ok": False, "error": "..."}
    """
    res = _ejecutar_consulta("explicar_conflictos", timeout=30)
    if not res["ok"]:
        return res
    return {"ok": True, "conflictos": res["salida"]}


def cargar_combinaciones_guardadas() -> list:
    """
    Lee combinaciones_validas.json si existe.
    Retorna lista de combinaciones o lista vacía.
    """
    ruta = os.path.join(RESULTADOS_DIR, "combinaciones_validas.json")
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []
def validar_seleccion_manual(codigos_secciones: list) -> dict:
    """
    Valida una selección manual de secciones (una por curso) contra restricciones.pl.
    codigos_secciones: ej. ['35671', '40012']
    Retorna:
      {"ok": True, "valida": True, "conflictos": []}
      {"ok": True, "valida": False, "conflictos": ["Conflicto: ...", ...]}
      {"ok": False, "error": "..."}
    """
    if not _prolog_disponible():
        return {"ok": False, "error": (
            "SWI-Prolog no está instalado. "
            "Descárgalo en https://www.swi-prolog.org/Download.html"
        )}

    if not os.path.exists(HECHOS_PL) or os.path.getsize(HECHOS_PL) == 0:
        return {"ok": False, "error": (
            "hechos.pl está vacío. Corre primero el exportador de Scala "
            "(ExportadorProlog) para generar los hechos desde tus cursos."
        )}

    restricciones_pl = os.path.join(PROLOG_DIR, "restricciones.pl")
    if not os.path.exists(restricciones_pl):
        return {"ok": False, "error": "restricciones.pl no encontrado en prolog/."}

    if len(codigos_secciones) < 2:
        return {"ok": True, "valida": True, "conflictos": []}

    hechos_path = HECHOS_PL.replace("\\", "/")  # evita romper el string en Windows
    lista_pl = "[" + ",".join(f"'{c}'" for c in codigos_secciones) + "]"
    goal = f"consult('{hechos_path}'), validar_seleccion({lista_pl})"

    try:
        resultado = subprocess.run(
            ["swipl", "-g", goal, "-g", "halt", restricciones_pl],
            capture_output=True, text=True, timeout=15, cwd=PROLOG_DIR
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Prolog tardó demasiado validando la selección."}
    except Exception as e:
        return {"ok": False, "error": str(e)}

    salida = resultado.stdout.strip()
    if resultado.returncode != 0 and not salida:
        return {"ok": False, "error": resultado.stderr.strip() or "Error desconocido en Prolog."}

    lineas = [l for l in salida.splitlines() if l.strip()]
    if not lineas:
        return {"ok": False, "error": "Prolog no devolvió resultado."}

    if lineas[0] == "OK":
        return {"ok": True, "valida": True, "conflictos": []}
    return {"ok": True, "valida": False, "conflictos": lineas[1:]}