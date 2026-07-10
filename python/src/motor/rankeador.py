import json
import os
from typing import List, Dict, Optional

RESULTADOS_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "..", "data", "resultados"
))

PREFS_FILE = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "..", "data", "preferencias.json"
))

# ─────────────────────────────────────────────
#  PREFERENCIAS POR DEFECTO
# ─────────────────────────────────────────────
PREFERENCIAS_DEFAULT = {
    "turno": "cualquiera",       # "manana" | "tarde" | "noche" | "cualquiera"
    "dias_libres": [],           # lista de dias que el usuario quiere libres
    "pesos": {
        "dias_concentrados": 1.5,
        "menos_huecos":      1.2,
        "horario_comodo":    0.8,
        "carga_equilibrada": 1.0,
        "turno_preferido":   0.0,   # se activa si el usuario elige turno
        "dias_libres":       0.0,   # se activa si el usuario elige dias libres
    }
}

TURNOS = {
    "manana":     (7  * 60, 13 * 60),   # 07:00 – 13:00
    "tarde":      (13 * 60, 19 * 60),   # 13:00 – 19:00
    "noche":      (19 * 60, 22 * 60),   # 19:00 – 22:00
    "cualquiera": None,
}

DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]


def hora_a_min(h: str) -> int:
    """Convierte '8:30' a 510 minutos."""
    try:
        partes = h.split(":")
        return int(partes[0]) * 60 + int(partes[1])
    except Exception:
        return 0


# ─────────────────────────────────────────────
#  GESTIÓN DE PREFERENCIAS
# ─────────────────────────────────────────────

def cargar_preferencias() -> Dict:
    """Lee preferencias.json o retorna las por defecto."""
    if os.path.exists(PREFS_FILE):
        try:
            with open(PREFS_FILE, "r", encoding="utf-8") as f:
                guardadas = json.load(f)
            # Merge con defaults para no perder claves nuevas
            prefs = dict(PREFERENCIAS_DEFAULT)
            prefs.update(guardadas)
            prefs["pesos"] = dict(PREFERENCIAS_DEFAULT["pesos"])
            prefs["pesos"].update(guardadas.get("pesos", {}))
            return prefs
        except Exception:
            pass
    return dict(PREFERENCIAS_DEFAULT)


def guardar_preferencias(prefs: Dict) -> None:
    """Persiste las preferencias en disco."""
    os.makedirs(os.path.dirname(PREFS_FILE), exist_ok=True)
    with open(PREFS_FILE, "w", encoding="utf-8") as f:
        json.dump(prefs, f, ensure_ascii=False, indent=2)


def aplicar_pesos_segun_preferencias(prefs: Dict) -> Dict:
    """
    Ajusta los pesos dinámicamente según lo que el usuario eligió.
    Si eligió turno → activa peso turno_preferido.
    Si eligió días libres → activa peso dias_libres.
    """
    pesos = dict(prefs.get("pesos", PREFERENCIAS_DEFAULT["pesos"]))

    if prefs.get("turno", "cualquiera") != "cualquiera":
        pesos["turno_preferido"] = 2.0   # criterio importante

    if prefs.get("dias_libres"):
        pesos["dias_libres"] = 2.5       # criterio muy importante

    return pesos


# ─────────────────────────────────────────────
#  CRITERIOS DE PUNTUACIÓN (existentes)
# ─────────────────────────────────────────────

def puntaje_dias(combinacion: List[Dict]) -> float:
    """Menos días distintos usados = mejor (más concentrado)."""
    dias = set()
    for sec in combinacion:
        for blq in sec.get("bloques", []):
            dias.add(blq["dia"])
    return (6 - len(dias)) * 10


def puntaje_huecos(combinacion: List[Dict]) -> float:
    """Menos tiempo libre entre clases en el mismo día = mejor."""
    bloques_por_dia: Dict[str, list] = {}
    for sec in combinacion:
        for blq in sec.get("bloques", []):
            dia = blq["dia"]
            bloques_por_dia.setdefault(dia, []).append(
                (hora_a_min(blq["inicio"]), hora_a_min(blq["fin"]))
            )

    total_huecos = 0
    for dia, bloques in bloques_por_dia.items():
        bloques_sorted = sorted(bloques, key=lambda x: x[0])
        for i in range(1, len(bloques_sorted)):
            hueco = bloques_sorted[i][0] - bloques_sorted[i - 1][1]
            if hueco > 0:
                total_huecos += hueco

    return max(0, 50 - (total_huecos // 30))


def puntaje_horario_temprano(combinacion: List[Dict]) -> float:
    """Penaliza clases antes de 8am o después de 7pm."""
    penalizacion = 0
    for sec in combinacion:
        for blq in sec.get("bloques", []):
            ini = hora_a_min(blq["inicio"])
            fin = hora_a_min(blq["fin"])
            if ini < 8 * 60:
                penalizacion += (8 * 60 - ini) // 30
            if fin > 19 * 60:
                penalizacion += (fin - 19 * 60) // 30
    return max(0, 30 - penalizacion)


def puntaje_carga_equilibrada(combinacion: List[Dict]) -> float:
    """Prefiere carga distribuida entre días (baja varianza)."""
    bloques_por_dia: Dict[str, int] = {}
    for sec in combinacion:
        for blq in sec.get("bloques", []):
            dia = blq["dia"]
            bloques_por_dia[dia] = bloques_por_dia.get(dia, 0) + 1

    if not bloques_por_dia:
        return 0

    valores = list(bloques_por_dia.values())
    promedio = sum(valores) / len(valores)
    varianza = sum((v - promedio) ** 2 for v in valores) / len(valores)
    return max(0, 20 - varianza * 2)


# ─────────────────────────────────────────────
#  CRITERIOS NUEVOS (Mejora 2)
# ─────────────────────────────────────────────

def puntaje_turno(combinacion: List[Dict], turno: str) -> float:
    """
    Premia combinaciones donde la mayoría de clases caen en el turno preferido.
    turno: 'manana' | 'tarde' | 'noche' | 'cualquiera'
    Retorna 0-40 puntos.
    """
    if turno == "cualquiera" or turno not in TURNOS:
        return 0

    rango = TURNOS[turno]
    if rango is None:
        return 0

    turno_ini, turno_fin = rango
    total_bloques  = 0
    bloques_en_turno = 0

    for sec in combinacion:
        for blq in sec.get("bloques", []):
            ini_m = hora_a_min(blq["inicio"])
            fin_m = hora_a_min(blq["fin"])
            total_bloques += 1
            # Se considera en turno si la mayor parte del bloque cae dentro
            overlap_ini = max(ini_m, turno_ini)
            overlap_fin = min(fin_m, turno_fin)
            if overlap_fin > overlap_ini:
                duracion_total   = fin_m - ini_m
                duracion_overlap = overlap_fin - overlap_ini
                if duracion_overlap / duracion_total >= 0.5:
                    bloques_en_turno += 1

    if total_bloques == 0:
        return 0

    proporcion = bloques_en_turno / total_bloques
    return round(proporcion * 40, 2)   # máx 40 puntos


def puntaje_dias_libres(combinacion: List[Dict], dias_libres: List[str]) -> float:
    """
    Premia combinaciones que no tienen clases en los días que el usuario quiere libres.
    Por cada día libre respetado → 15 puntos. Por cada violación → -20 puntos.
    """
    if not dias_libres:
        return 0

    dias_con_clases = set()
    for sec in combinacion:
        for blq in sec.get("bloques", []):
            dias_con_clases.add(blq["dia"])

    puntaje = 0.0
    for dia in dias_libres:
        if dia not in dias_con_clases:
            puntaje += 15   # día libre respetado
        else:
            puntaje -= 20   # violación: tiene clase ese día

    return puntaje


# ─────────────────────────────────────────────
#  PUNTAJE TOTAL con preferencias
# ─────────────────────────────────────────────

def puntaje_total(combinacion: List[Dict],
                  prefs: Optional[Dict] = None) -> float:
    """Suma ponderada de todos los criterios según preferencias."""
    if prefs is None:
        prefs = PREFERENCIAS_DEFAULT

    pesos = aplicar_pesos_segun_preferencias(prefs)
    turno      = prefs.get("turno", "cualquiera")
    dias_libres = prefs.get("dias_libres", [])

    return (
        puntaje_dias(combinacion)             * pesos["dias_concentrados"] +
        puntaje_huecos(combinacion)           * pesos["menos_huecos"]      +
        puntaje_horario_temprano(combinacion) * pesos["horario_comodo"]     +
        puntaje_carga_equilibrada(combinacion)* pesos["carga_equilibrada"]  +
        puntaje_turno(combinacion, turno)     * pesos["turno_preferido"]    +
        puntaje_dias_libres(combinacion, dias_libres) * pesos["dias_libres"]
    )


# ─────────────────────────────────────────────
#  FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────

def rankear(combinaciones: List[List[Dict]],
            top: int = 5,
            prefs: Optional[Dict] = None) -> List[Dict]:
    """
    Recibe lista de combinaciones y preferencias del usuario.
    Retorna las 'top' mejores con su puntaje y detalle.
    """
    if not combinaciones:
        return []

    if prefs is None:
        prefs = cargar_preferencias()

    turno       = prefs.get("turno", "cualquiera")
    dias_libres = prefs.get("dias_libres", [])

    resultados = []
    for i, combo in enumerate(combinaciones):
        score = puntaje_total(combo, prefs)
        dias = sorted(set(
            blq["dia"]
            for sec in combo
            for blq in sec.get("bloques", [])
        ))
        resultados.append({
            "posicion": i + 1,
            "puntaje": round(score, 2),
            "dias_usados": dias,
            "n_dias": len(dias),
            "secciones": combo,
            "preferencias_aplicadas": {
                "turno": turno,
                "dias_libres": dias_libres,
            },
            "detalle_puntaje": {
                "dias_concentrados": round(puntaje_dias(combo), 2),
                "menos_huecos":      round(puntaje_huecos(combo), 2),
                "horario_comodo":    round(puntaje_horario_temprano(combo), 2),
                "carga_equilibrada": round(puntaje_carga_equilibrada(combo), 2),
                "turno_preferido":   round(puntaje_turno(combo, turno), 2),
                "dias_libres":       round(puntaje_dias_libres(combo, dias_libres), 2),
            }
        })

<<<<<<< HEAD
    # Ordenar de mayor a menor puntaje
    resultados.sort(
        key=lambda x: x["puntaje"], 
        reverse=True)

    # Reasignar posiciones tras el ordenamiento
=======
    resultados.sort(key=lambda x: x["puntaje"], reverse=True)
>>>>>>> origin/Caleb
    for i, r in enumerate(resultados):
        r["posicion"] = i + 1

    top_resultados = resultados[:top]

    os.makedirs(RESULTADOS_DIR, exist_ok=True)
    if top_resultados:
        ruta = os.path.join(RESULTADOS_DIR, "mejor_horario.json")
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(top_resultados[0], f, ensure_ascii=False, indent=2)

    return top_resultados


def cargar_mejor_horario() -> Dict:
    """Lee mejor_horario.json si existe."""
    ruta = os.path.join(RESULTADOS_DIR, "mejor_horario.json")
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}