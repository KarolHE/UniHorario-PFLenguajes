import subprocess
import os
import json

# Ruta al JAR compilado de Scala
JAR_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "..", "scala", "target", "scala-2.13", "unihorario.jar"
)

DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "..", "data", "cursos_ingresados.json"
)

HECHOS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "..", "prolog", "hechos.pl"
)


def _jar_disponible() -> bool:
    """Verifica que el JAR de Scala existe."""
    return os.path.exists(os.path.normpath(JAR_PATH))


def exportar_a_prolog() -> dict:
    """
    Llama a Scala para que lea cursos_ingresados.json
    y genere prolog/hechos.pl automáticamente.
    Retorna {"ok": True} o {"ok": False, "error": "..."}
    """
    if not _jar_disponible():
        return {
            "ok": False,
            "error": (
                "No se encontró unihorario.jar. "
                "Compila Scala primero con: cd scala && sbt assembly"
            )
        }

    if not os.path.exists(os.path.normpath(DATA_FILE)):
        return {
            "ok": False,
            "error": "No hay cursos guardados. Agrega cursos antes de generar el horario."
        }

    try:
        resultado = subprocess.run(
            ["java", "-jar", os.path.normpath(JAR_PATH), "exportar"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if resultado.returncode == 0:
            return {"ok": True, "salida": resultado.stdout.strip()}
        else:
            return {
                "ok": False,
                "error": resultado.stderr.strip() or "Error desconocido en Scala."
            }
    except FileNotFoundError:
        return {
            "ok": False,
            "error": "Java no está instalado o no está en el PATH del sistema."
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Scala tardó demasiado. Intenta de nuevo."}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def verificar_datos() -> dict:
    """
    Llama a Scala en modo 'verificar' para obtener un resumen
    de los datos cargados (cursos, secciones, bloques).
    Retorna {"ok": True, "resumen": "..."} o {"ok": False, "error": "..."}
    """
    if not _jar_disponible():
        return {"ok": False, "error": "JAR de Scala no encontrado."}

    try:
        resultado = subprocess.run(
            ["java", "-jar", os.path.normpath(JAR_PATH), "verificar"],
            capture_output=True,
            text=True,
            timeout=15
        )
        if resultado.returncode == 0:
            return {"ok": True, "resumen": resultado.stdout.strip()}
        else:
            return {"ok": False, "error": resultado.stderr.strip()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def hechos_generados() -> bool:
    """Retorna True si hechos.pl ya fue generado por Scala."""
    return os.path.exists(os.path.normpath(HECHOS_FILE))