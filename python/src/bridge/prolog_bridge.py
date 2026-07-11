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


# ============================================================
#  VALIDACIÓN MANUAL  (Mejora 4 — Avance 2)
#  El estudiante elige una sección por curso desde la UI y
#  Prolog responde si la combinación tiene conflictos.
# ============================================================

def validar_seleccion_manual(codigos_secciones: list, timeout: int = 15) -> dict:
    """
    Recibe una lista de códigos de sección (strings), por ejemplo:
    ["sec_101", "sec_205", "sec_310"]

    Construye dinámicamente la consulta Prolog y la ejecuta sobre
    consultas.pl usando el predicado validar_seleccion_resultado/2.

    Retorna:
      {"ok": True, "valida": bool, "conflictos": [str, ...]}
      o
      {"ok": False, "error": "..."}
    """
    if not codigos_secciones:
        return {"ok": False, "error": "No se seleccionó ninguna sección."}

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

    # Construir la lista Prolog ['sec_101','sec_205',...]
    # Los códigos vienen como atoms (strings entre comillas simples)
    lista_pl = "[" + ",".join(f"'{c}'" for c in codigos_secciones) + "]"

    # Consulta que ejecuta la validación y emite el resultado como JSON
    # usando format/2 con escape manual (sin librerías externas de Prolog).
    consulta = (
        f"validar_seleccion_resultado({lista_pl}, resultado(Valida, Conflictos)), "
        f"atomic_list_concat(Conflictos, '||', ConflictosTexto), "
        f"format('VALIDA:~w~nCONFLICTOS:~w~n', [Valida, ConflictosTexto])"
    )

    try:
        resultado = subprocess.run(
            ["swipl", "-g", consulta, "-g", "halt", CONSULTAS_PL],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=PROLOG_DIR
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Prolog tardó demasiado validando la selección."}
    except Exception as e:
        return {"ok": False, "error": str(e)}

    if resultado.returncode != 0:
        err = resultado.stderr.strip() or "Error desconocido en Prolog."
        return {"ok": False, "error": err}

    salida = resultado.stdout.strip()

    # Parsear la salida con formato VALIDA:<true|false>\nCONFLICTOS:<a||b||c>
    m_valida = re.search(r"VALIDA:(true|false)", salida)
    m_conf   = re.search(r"CONFLICTOS:(.*)", salida)

    if not m_valida:
        return {"ok": False, "error": f"No se pudo interpretar la respuesta de Prolog: {salida}"}

    valida = m_valida.group(1) == "true"
    conflictos_texto = m_conf.group(1).strip() if m_conf else ""
    conflictos = [c for c in conflictos_texto.split("||") if c] if conflictos_texto else []

    return {"ok": True, "valida": valida, "conflictos": conflictos}