import json
import os
from typing import List, Dict

RESULTADOS_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "..", "data", "resultados"
))


def hora_a_min(h: str) -> int:
    """Convierte '8:30' a 510 minutos."""
    try:
        partes = h.split(":")
        return int(partes[0]) * 60 + int(partes[1])
    except Exception:
        return 0


# ─────────────────────────────────────────────
#  CRITERIOS DE PUNTUACIÓN
#  Cada función retorna un puntaje (mayor = mejor)
# ─────────────────────────────────────────────

def puntaje_dias(combinacion: List[Dict]) -> float:
    """Menos días distintos usados = mejor (más concentrado)."""
    dias = set()
    for sec in combinacion:
        for blq in sec.get("bloques", []):
            dias.add(blq["dia"])
    # Máximo 6 días, queremos pocos días → invertimos
    return (6 - len(dias)) * 10


def puntaje_huecos(combinacion: List[Dict]) -> float:
    """Menos tiempo libre entre clases en el mismo día = mejor."""
    bloques_por_dia: Dict[str, list] = {}
    for sec in combinacion:
        for blq in sec.get("bloques", []):
            dia = blq["dia"]
            if dia not in bloques_por_dia:
                bloques_por_dia[dia] = []
            bloques_por_dia[dia].append(
                (hora_a_min(blq["inicio"]), hora_a_min(blq["fin"]))
            )

    total_huecos = 0
    for dia, bloques in bloques_por_dia.items():
        bloques_sorted = sorted(bloques, key=lambda x: x[0])
        for i in range(1, len(bloques_sorted)):
            hueco = bloques_sorted[i][0] - bloques_sorted[i - 1][1]
            if hueco > 0:
                total_huecos += hueco

    # Convertir a puntaje: menos huecos = más puntos
    # Penalizamos 1 punto por cada 30 min de hueco
    return max(0, 50 - (total_huecos // 30))


def puntaje_horario_temprano(combinacion: List[Dict]) -> float:
    """Prefiere horarios que no empiecen muy temprano (antes de 8am) ni muy tarde (después de 7pm)."""
    penalizacion = 0
    for sec in combinacion:
        for blq in sec.get("bloques", []):
            ini = hora_a_min(blq["inicio"])
            fin = hora_a_min(blq["fin"])
            if ini < 8 * 60:   # antes de 8am
                penalizacion += (8 * 60 - ini) // 30
            if fin > 19 * 60:  # después de 7pm
                penalizacion += (fin - 19 * 60) // 30
    return max(0, 30 - penalizacion)


def puntaje_carga_equilibrada(combinacion: List[Dict]) -> float:
    """Prefiere que la carga esté distribuida entre los días (no todo en un día)."""
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

    # Menos varianza = más equilibrado = más puntos
    return max(0, 20 - varianza * 2)


def puntaje_total(combinacion: List[Dict]) -> float:
    """Suma ponderada de todos los criterios."""
    return (
        puntaje_dias(combinacion) * 1.5 +
        puntaje_huecos(combinacion) * 1.2 +
        puntaje_horario_temprano(combinacion) * 0.8 +
        puntaje_carga_equilibrada(combinacion) * 1.0
    )


# ─────────────────────────────────────────────
#  FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────

def rankear(combinaciones: List[List[Dict]], top: int = 5) -> List[Dict]:
    """
    Recibe lista de combinaciones (cada una es lista de secciones elegidas).
    Retorna las 'top' mejores con su puntaje y detalle.
    """
    if not combinaciones:
        return []

    resultados = []
    for i, combo in enumerate(combinaciones):
        score = puntaje_total(combo)
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
            "detalle_puntaje": {
                "dias_concentrados": round(puntaje_dias(combo), 2),
                "menos_huecos":      round(puntaje_huecos(combo), 2),
                "horario_comodo":    round(puntaje_horario_temprano(combo), 2),
                "carga_equilibrada": round(puntaje_carga_equilibrada(combo), 2),
            }
        })

    # Ordenar de mayor a menor puntaje
    resultados.sort(
        key=lambda x: x["puntaje"], 
        reverse=True)

    # Reasignar posiciones tras el ordenamiento
    for i, r in enumerate(resultados):
        r["posicion"] = i + 1

    top_resultados = resultados[:top]

    # Guardar mejor horario
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