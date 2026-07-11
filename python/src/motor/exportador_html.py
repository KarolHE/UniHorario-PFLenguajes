import os
from datetime import datetime
from html import escape
from typing import Dict, List, Tuple

DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]

COLORES_CURSO = [
    "#C0392B", "#1565C0", "#2E7D32", "#6A1B9A",
    "#E65100", "#00838F", "#AD1457", "#558B2F",
    "#827717", "#4A148C", "#006064", "#BF360C",
]

FRANJA_MIN = 30
HORA_INICIO = 7
HORA_FIN = 22


def hora_a_min(h: str) -> int:
    try:
        hh, mm = h.split(":")
        return int(hh) * 60 + int(mm)
    except Exception:
        return 0


def min_a_hora(m: int) -> str:
    return f"{m // 60:02d}:{m % 60:02d}"


def _asignar_colores(cursos: List[Dict]) -> Dict[str, str]:
    colores = {}
    for curso in cursos:
        nombre = curso.get("nombre", "Curso")
        if nombre not in colores:
            colores[nombre] = COLORES_CURSO[len(colores) % len(COLORES_CURSO)]
    return colores


def _dias_con_clases(cursos: List[Dict]) -> List[str]:
    usados = {
        bloque.get("dia")
        for curso in cursos
        for sec in curso.get("secciones", [])
        for bloque in sec.get("bloques", [])
    }
    return [dia for dia in DIAS_SEMANA if dia in usados] or DIAS_SEMANA[:5]


def _construir_mapa(cursos: List[Dict],
                    dias: List[str],
                    colores: Dict[str, str]) -> Dict[Tuple[str, int], List[Dict]]:
    mapa: Dict[Tuple[str, int], List[Dict]] = {}
    for curso in cursos:
        nombre = curso.get("nombre", "Curso")
        for sec in curso.get("secciones", []):
            for bloque in sec.get("bloques", []):
                dia = bloque.get("dia")
                if dia not in dias:
                    continue

                ini_m = hora_a_min(bloque.get("inicio", "00:00"))
                fin_m = hora_a_min(bloque.get("fin", "00:00"))
                franja = (ini_m // FRANJA_MIN) * FRANJA_MIN

                while franja < fin_m:
                    mapa.setdefault((dia, franja), []).append({
                        "curso": nombre,
                        "seccion": sec.get("codigo", ""),
                        "docente": sec.get("docente", ""),
                        "inicio": bloque.get("inicio", ""),
                        "fin": bloque.get("fin", ""),
                        "color": colores.get(nombre, "#555555"),
                        "es_inicio": franja == (ini_m // FRANJA_MIN) * FRANJA_MIN,
                    })
                    franja += FRANJA_MIN
    return mapa


def _hex_a_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    except Exception:
        return f"rgba(85,85,85,{alpha})"


def _render_leyenda(cursos: List[Dict], colores: Dict[str, str]) -> str:
    vistos = set()
    items = []
    for curso in cursos:
        nombre = curso.get("nombre", "Curso")
        if nombre in vistos:
            continue
        vistos.add(nombre)
        color = colores.get(nombre, "#555555")
        items.append(
            f'<span class="chip" style="--chip:{color}">'
            f'<span class="dot"></span>{escape(nombre)}</span>'
        )
    return "\n".join(items)


def _render_conflicto(items: List[Dict]) -> str:
    detalles = []
    for item in items:
        detalles.append(
            '<div class="conflict-item">'
            f'<strong>{escape(item["curso"])}</strong> '
            f'Sec. {escape(str(item["seccion"]))} · {escape(str(item["docente"]))} '
            f'<span>{escape(item["inicio"])} - {escape(item["fin"])}</span>'
            '</div>'
        )
    return (
        '<td class="celda conflicto">'
        '<div class="bloque-nombre">CONFLICTO</div>'
        + "".join(detalles) +
        '</td>\n'
    )


def _render_ocupada(item: Dict) -> str:
    color = item["color"]
    contenido = ""
    if item["es_inicio"]:
        contenido = (
            f'<div class="bloque-nombre" style="color:{color}">{escape(item["curso"])}</div>'
            f'<div class="bloque-detalle">Sec. {escape(str(item["seccion"]))} · '
            f'{escape(str(item["docente"]))}</div>'
            f'<div class="bloque-hora">{escape(item["inicio"])} - {escape(item["fin"])}</div>'
        )
    return (
        f'<td class="celda ocupada" style="background:{_hex_a_rgba(color, 0.23)};'
        f'border-left-color:{color}">{contenido}</td>\n'
    )


def generar_html(cursos: List[Dict], ruta_salida: str) -> bool:
    if not cursos:
        return False

    dias = _dias_con_clases(cursos)
    colores = _asignar_colores(cursos)
    mapa = _construir_mapa(cursos, dias, colores)

    n_cursos = len(cursos)
    n_secciones = sum(len(curso.get("secciones", [])) for curso in cursos)
    conflictos = sum(1 for items in mapa.values() if len(items) > 1)
    fecha_gen = datetime.now().strftime("%d/%m/%Y %H:%M")

    cabecera_dias = '<th class="hora-col">Hora</th>\n' + "\n".join(
        f"<th>{escape(dia)}</th>" for dia in dias
    )

    filas_html = []
    franja = HORA_INICIO * 60
    fila_idx = 0
    while franja < HORA_FIN * 60:
        fila = [f'<tr class="{"par" if fila_idx % 2 == 0 else "impar"}">']
        fila.append(
            f'<td class="hora-cell"><strong>{min_a_hora(franja)}</strong>'
            f'<span>{min_a_hora(franja + FRANJA_MIN)}</span></td>'
        )

        for dia in dias:
            items = mapa.get((dia, franja), [])
            if len(items) > 1:
                fila.append(_render_conflicto(items))
            elif len(items) == 1:
                fila.append(_render_ocupada(items[0]))
            else:
                fila.append('<td class="celda libre"></td>\n')

        fila.append("</tr>")
        filas_html.append("\n".join(fila))
        franja += FRANJA_MIN
        fila_idx += 1

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>UniHorario - Horario Semanal</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: "Segoe UI", Arial, sans-serif;
      background: #101010;
      color: #f4f4f4;
    }}
    .header {{
      background: #E30613;
      color: #fff;
      padding: 24px 36px;
      display: flex;
      align-items: center;
      gap: 22px;
      border-bottom: 4px solid #B5000F;
    }}
    .brand {{
      width: 78px;
      height: 54px;
      display: grid;
      place-items: center;
      font-size: 2rem;
      font-weight: 900;
      background: #fff;
      color: #E30613;
    }}
    h1 {{
      margin: 0;
      font-size: 1.55rem;
    }}
    .header p {{
      margin: 4px 0 0;
      color: #ffd0d0;
      font-size: 0.9rem;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(4, minmax(140px, 1fr));
      background: #181818;
      border-bottom: 1px solid #2d2d2d;
    }}
    .stat {{
      padding: 14px 28px;
      border-right: 1px solid #2d2d2d;
    }}
    .stat:last-child {{ border-right: 0; }}
    .stat-val {{
      color: #fff;
      font-size: 1.45rem;
      font-weight: 800;
    }}
    .stat-lbl {{
      color: #9a9a9a;
      font-size: 0.75rem;
      margin-top: 2px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .leyenda {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      padding: 16px 32px;
      background: #1f1f1f;
      border-bottom: 1px solid #2d2d2d;
    }}
    .leyenda-label {{
      color: #a0a0a0;
      font-weight: 700;
      font-size: 0.82rem;
      margin-right: 4px;
    }}
    .chip {{
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 6px 10px;
      background: #2b2b2b;
      border: 1px solid #3c3c3c;
      color: #f8f8f8;
      font-size: 0.8rem;
      font-weight: 700;
    }}
    .dot {{
      width: 10px;
      height: 10px;
      background: var(--chip);
      display: inline-block;
    }}
    .tabla-wrap {{
      padding: 24px 32px 40px;
      overflow-x: auto;
    }}
    table {{
      width: 100%;
      min-width: 920px;
      border-collapse: collapse;
      table-layout: fixed;
      font-size: 0.82rem;
      box-shadow: 0 0 0 1px #2a2a2a;
    }}
    thead th {{
      position: sticky;
      top: 0;
      z-index: 2;
      background: #E30613;
      color: #fff;
      padding: 11px 10px;
      text-align: center;
      border-right: 1px solid #B5000F;
    }}
    .hora-col {{
      width: 86px;
    }}
    tr.par {{ background: #1c1c1c; }}
    tr.impar {{ background: #232323; }}
    .hora-cell {{
      width: 86px;
      color: #bdbdbd;
      text-align: center;
      border: 1px solid #2a2a2a;
      padding: 5px 6px;
      vertical-align: middle;
    }}
    .hora-cell strong {{
      display: block;
      color: #f2f2f2;
      font-size: 0.78rem;
    }}
    .hora-cell span {{
      display: block;
      color: #777;
      font-size: 0.68rem;
      margin-top: 1px;
    }}
    .celda {{
      height: 34px;
      min-width: 136px;
      border: 1px solid #2a2a2a;
      padding: 4px 7px;
      vertical-align: top;
      overflow: hidden;
    }}
    .libre {{
      background: rgba(255,255,255,0.015);
    }}
    .ocupada {{
      border-left: 5px solid;
    }}
    .conflicto {{
      background: rgba(243, 156, 18, 0.24);
      border-left: 5px solid #F39C12;
      color: #ffe4b0;
    }}
    .bloque-nombre {{
      font-weight: 800;
      font-size: 0.78rem;
      line-height: 1.15;
    }}
    .bloque-detalle {{
      color: #d1d1d1;
      font-size: 0.7rem;
      margin-top: 2px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .bloque-hora {{
      color: #969696;
      font-size: 0.68rem;
      margin-top: 1px;
    }}
    .conflict-item {{
      margin-top: 4px;
      font-size: 0.68rem;
      color: #ffd99a;
      line-height: 1.25;
    }}
    .conflict-item span {{
      color: #ffefcc;
      white-space: nowrap;
    }}
    .footer {{
      padding: 18px 32px;
      text-align: center;
      color: #666;
      border-top: 1px solid #242424;
      font-size: 0.76rem;
    }}
    @media (max-width: 760px) {{
      .header {{
        align-items: flex-start;
        padding: 20px;
      }}
      .brand {{
        width: 62px;
        height: 46px;
        font-size: 1.55rem;
      }}
      .stats {{
        grid-template-columns: repeat(2, 1fr);
      }}
      .stat {{
        padding: 12px 18px;
      }}
      .tabla-wrap, .leyenda {{
        padding-left: 16px;
        padding-right: 16px;
      }}
    }}
  </style>
</head>
<body>
  <header class="header">
    <div class="brand">UTP</div>
    <div>
      <h1>UniHorario - Horario Semanal</h1>
      <p>Generado el {escape(fecha_gen)} · Exportación visual autocontenida</p>
    </div>
  </header>

  <section class="stats">
    <div class="stat"><div class="stat-val">{n_cursos}</div><div class="stat-lbl">Cursos</div></div>
    <div class="stat"><div class="stat-val">{n_secciones}</div><div class="stat-lbl">Secciones</div></div>
    <div class="stat"><div class="stat-val">{len(dias)}</div><div class="stat-lbl">Días con clases</div></div>
    <div class="stat"><div class="stat-val">{conflictos}</div><div class="stat-lbl">Conflictos</div></div>
  </section>

  <section class="leyenda">
    <span class="leyenda-label">Cursos</span>
    {_render_leyenda(cursos, colores)}
  </section>

  <main class="tabla-wrap">
    <table aria-label="Horario semanal">
      <thead>
        <tr>{cabecera_dias}</tr>
      </thead>
      <tbody>
        {"".join(filas_html)}
      </tbody>
    </table>
  </main>

  <footer class="footer">
    UniHorario · Universidad Tecnológica del Perú · Franjas de 30 minutos
  </footer>
</body>
</html>"""

    try:
        carpeta = os.path.dirname(os.path.abspath(ruta_salida))
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        with open(ruta_salida, "w", encoding="utf-8") as f:
            f.write(html)
        return True
    except Exception:
        return False
