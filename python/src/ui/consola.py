import sys, os as _os
_motor = _os.path.normpath(_os.path.join(_os.path.dirname(__file__), "..", "motor"))
if _motor not in sys.path:
    sys.path.insert(0, _motor)
from rankeador import (cargar_preferencias, guardar_preferencias,
                       DIAS_SEMANA, TURNOS)
import tkinter as tk
from tkinter import ttk, messagebox, font
import json
import os
from datetime import datetime
import random

# ─────────────────────────────────────────────
#  PALETA UTP
# ─────────────────────────────────────────────
C_RED      = "#E30613"
C_RED_DARK = "#B5000F"
C_BLACK    = "#111111"
C_DARK     = "#1C1C1C"
C_GRAY     = "#2A2A2A"
C_GRAY2    = "#3D3D3D"
C_LIGHT    = "#F5F5F5"
C_WHITE    = "#FFFFFF"
C_ACCENT   = "#FF4D4D"
C_TEXT_MUT = "#9A9A9A"
C_SUCCESS  = "#2ECC71"
C_WARNING  = "#F39C12"

DATA_FILE   = "data/cursos_ingresados.json"
HIST_FILE   = "data/resultados/historial.json"

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
HORAS = [f"{h:02d}:{m:02d}" for h in range(7, 22) for m in (0, 30)]


# ─────────────────────────────────────────────
#  HELPERS DE DATOS
# ─────────────────────────────────────────────
def cargar_json(path, default):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default

def guardar_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def hora_a_min(h):
    try:
        p = h.split(":")
        return int(p[0]) * 60 + int(p[1])
    except Exception:
        return 0

def bloques_chocan(b1, b2):
    if b1["dia"] != b2["dia"]:
        return False
    i1, f1 = hora_a_min(b1["inicio"]), hora_a_min(b1["fin"])
    i2, f2 = hora_a_min(b2["inicio"]), hora_a_min(b2["fin"])
    return i1 < f2 and i2 < f1

def detectar_conflictos(cursos):
    bloques = []
    for curso in cursos:
        for sec in curso.get("secciones", []):
            for bloque in sec.get("bloques", []):
                bloques.append({**bloque, "curso": curso["nombre"], "seccion": sec["codigo"], "docente": sec["docente"]})
    conflictos = []
    for i in range(len(bloques)):
        for j in range(i + 1, len(bloques)):
            if bloques_chocan(bloques[i], bloques[j]):
                conflictos.append((bloques[i], bloques[j]))
    return conflictos


# ─────────────────────────────────────────────
#  WIDGET BASE  — botón estilizado
# ─────────────────────────────────────────────
class BotonUTP(tk.Canvas):
    def __init__(self, parent, texto, comando=None, ancho=200, alto=42,
                 color=C_RED, color_texto=C_WHITE, radio=8, **kw):
        # Extraer bg de kw para evitar duplicado con el que calculamos aquí
        kw.pop("bg", None)
        try:
            bg = parent["bg"]
        except Exception:
            bg = C_DARK
        super().__init__(parent, width=ancho, height=alto,
                         bg=bg, highlightthickness=0, **kw)
        self._cmd = comando
        self._color = color
        self._color_hover = C_RED_DARK if color == C_RED else C_GRAY2
        self._color_texto = color_texto
        self._ancho = ancho
        self._alto = alto
        self._radio = radio
        self._texto = texto
        self._dibujar(color)
        self.bind("<Enter>", lambda e: self._dibujar(self._color_hover))
        self.bind("<Leave>", lambda e: self._dibujar(color))
        self.bind("<Button-1>", lambda e: self._click())

    def _dibujar(self, color):
        self.delete("all")
        r, w, h = self._radio, self._ancho, self._alto
        self.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=color, outline=color)
        self.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, fill=color, outline=color)
        self.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, fill=color, outline=color)
        self.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, fill=color, outline=color)
        self.create_rectangle(r, 0, w-r, h, fill=color, outline=color)
        self.create_rectangle(0, r, w, h-r, fill=color, outline=color)
        self.create_text(w//2, h//2, text=self._texto, fill=self._color_texto,
                         font=("Segoe UI", 10, "bold"))

    def _click(self):
        if self._cmd:
            self._cmd()


# ─────────────────────────────────────────────
#  APLICACIÓN PRINCIPAL
# ─────────────────────────────────────────────
class UniHorarioApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("UniHorario — UTP")
        self.geometry("960x640")
        self.minsize(860, 580)
        self.configure(bg=C_BLACK)
        self.resizable(True, True)

        # ── Icono ventana (canvas simulado)
        try:
            ico = tk.PhotoImage(width=32, height=32)
            self.iconphoto(False, ico)
        except Exception:
            pass

        # ── Estado global
        self.cursos = cargar_json(DATA_FILE, [])
        self.historial = cargar_json(HIST_FILE, [])
        self.pantalla_actual = None

        # ── Layout raíz
        self._crear_sidebar()
        self.contenedor = tk.Frame(self, bg=C_DARK)
        self.contenedor.pack(side="left", fill="both", expand=True)

        self.ir_a("inicio")

    # ── SIDEBAR ──────────────────────────────
    def _crear_sidebar(self):
        sb = tk.Frame(self, bg=C_BLACK, width=220)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        # Logo UTP
        logo_frame = tk.Frame(sb, bg=C_RED, height=72)
        logo_frame.pack(fill="x")
        logo_frame.pack_propagate(False)
        tk.Label(logo_frame, text="UTP", font=("Segoe UI Black", 26, "bold"),
                 bg=C_RED, fg=C_WHITE).place(relx=0.18, rely=0.5, anchor="center")
        tk.Label(logo_frame, text="UniHorario", font=("Segoe UI", 10),
                 bg=C_RED, fg=C_WHITE).place(relx=0.62, rely=0.38, anchor="center")
        tk.Label(logo_frame, text="Planificador inteligente", font=("Segoe UI", 7),
                 bg=C_RED, fg="#FFB3B3").place(relx=0.62, rely=0.65, anchor="center")

        separador = tk.Frame(sb, bg=C_RED, height=3)
        separador.pack(fill="x")

        # Menú
        self._nav_btns = {}
        nav_items = [
            ("🏠  Inicio",         "inicio"),
            ("📚  Mis Cursos",     "cursos"),
            ("📅  Ver Horario",    "horario"),
            ("📊  Tabla Semanal",  "tabla"),
            ("⚙️  Preferencias",   "preferencias"),
            ("🕐  Historial",      "historial"),
        ]
        menu_frame = tk.Frame(sb, bg=C_BLACK)
        menu_frame.pack(fill="both", expand=True, pady=(16, 0))

        for label, key in nav_items:
            btn = tk.Label(menu_frame, text=label, font=("Segoe UI", 11),
                           bg=C_BLACK, fg=C_TEXT_MUT, anchor="w",
                           padx=24, pady=12, cursor="hand2")
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=C_GRAY, fg=C_WHITE))
            btn.bind("<Leave>", lambda e, b=btn, k=key: b.config(
                bg=C_RED if self.pantalla_actual == k else C_BLACK,
                fg=C_WHITE if self.pantalla_actual == k else C_TEXT_MUT))
            btn.bind("<Button-1>", lambda e, k=key: self.ir_a(k))
            self._nav_btns[key] = btn

        # Versión
        tk.Label(sb, text="v1.0.0 · UTP 2025", font=("Segoe UI", 7),
                 bg=C_BLACK, fg=C_GRAY2).pack(side="bottom", pady=8)

    def _actualizar_nav(self, key):
        for k, btn in self._nav_btns.items():
            if k == key:
                btn.config(bg=C_RED, fg=C_WHITE)
            else:
                btn.config(bg=C_BLACK, fg=C_TEXT_MUT)

    # ── NAVEGACIÓN ───────────────────────────
    def ir_a(self, pantalla):
        self.pantalla_actual = pantalla
        self._actualizar_nav(pantalla)
        for widget in self.contenedor.winfo_children():
            widget.destroy()
        if pantalla == "inicio":
            PantallaInicio(self.contenedor, self)
        elif pantalla == "cursos":
            PantallaCursos(self.contenedor, self)
        elif pantalla == "horario":
            PantallaHorario(self.contenedor, self)
        elif pantalla == "historial":
            PantallaHistorial(self.contenedor, self)
        elif pantalla == "tabla":
            PantallaTabla(self.contenedor, self)
        elif pantalla == "preferencias":
            PantallaPreferencias(self.contenedor, self)

    def guardar_cursos(self):
        guardar_json(DATA_FILE, self.cursos)

    def guardar_historial(self):
        guardar_json(HIST_FILE, self.historial)


# ─────────────────────────────────────────────
#  PANTALLA: INICIO
# ─────────────────────────────────────────────
class PantallaInicio(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C_DARK)
        self.pack(fill="both", expand=True)
        self.app = app
        self._construir()

    def _construir(self):
        # Header
        header = tk.Frame(self, bg=C_RED, height=180)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="¡Hola, estudiante! 👋",
                 font=("Segoe UI", 11), bg=C_RED, fg="#FFD0D0").pack(anchor="w", padx=40, pady=(28, 0))
        tk.Label(header, text="Planifica tu horario ideal",
                 font=("Segoe UI Black", 26, "bold"), bg=C_RED, fg=C_WHITE).pack(anchor="w", padx=40)
        tk.Label(header, text="Agrega tus cursos, secciones y docentes — nosotros detectamos los conflictos.",
                 font=("Segoe UI", 10), bg=C_RED, fg="#FFB3B3").pack(anchor="w", padx=40)

        # Stats
        stats_frame = tk.Frame(self, bg=C_DARK)
        stats_frame.pack(fill="x", padx=32, pady=24)

        n_cursos = len(self.app.cursos)
        n_secciones = sum(len(c.get("secciones", [])) for c in self.app.cursos)
        n_hist = len(self.app.historial)
        conflictos = detectar_conflictos(self.app.cursos)

        stats = [
            ("📚", str(n_cursos), "Cursos"),
            ("📋", str(n_secciones), "Secciones"),
            ("⚠️", str(len(conflictos)), "Conflictos"),
            ("🕐", str(n_hist), "Guardados"),
        ]
        for emoji, valor, etiqueta in stats:
            card = tk.Frame(stats_frame, bg=C_GRAY, padx=20, pady=16)
            card.pack(side="left", fill="both", expand=True, padx=6)
            tk.Label(card, text=emoji, font=("Segoe UI", 20), bg=C_GRAY, fg=C_WHITE).pack()
            tk.Label(card, text=valor, font=("Segoe UI Black", 28, "bold"),
                     bg=C_GRAY, fg=C_RED if (etiqueta == "Conflictos" and int(valor) > 0) else C_WHITE).pack()
            tk.Label(card, text=etiqueta, font=("Segoe UI", 9),
                     bg=C_GRAY, fg=C_TEXT_MUT).pack()

        # Acciones rápidas
        tk.Label(self, text="Acciones rápidas", font=("Segoe UI", 13, "bold"),
                 bg=C_DARK, fg=C_WHITE).pack(anchor="w", padx=40, pady=(8, 12))

        acc = tk.Frame(self, bg=C_DARK)
        acc.pack(fill="x", padx=32)

        BotonUTP(acc, "➕  Agregar curso", lambda: self.app.ir_a("cursos"),
                 ancho=180, alto=44, bg=C_DARK).pack(side="left", padx=6)
        BotonUTP(acc, "📅  Ver horario", lambda: self.app.ir_a("horario"),
                 ancho=180, alto=44, color=C_GRAY, bg=C_DARK).pack(side="left", padx=6)

        # Tip
        tips = [
            "💡  Agrega todas las secciones disponibles para que el sistema elija la mejor combinación.",
            "💡  Puedes agregar el mismo curso varias veces con distintas secciones y horarios.",
            "💡  El sistema detecta automáticamente cuando dos clases se cruzan en el mismo horario.",
            "💡  Guarda tu horario favorito en el historial para consultarlo después.",
        ]
        tip_frame = tk.Frame(self, bg=C_GRAY, padx=20, pady=14)
        tip_frame.pack(fill="x", padx=32, pady=24)
        tk.Label(tip_frame, text=random.choice(tips), font=("Segoe UI", 10),
                 bg=C_GRAY, fg=C_LIGHT, wraplength=600, justify="left").pack(anchor="w")


# ─────────────────────────────────────────────
#  PANTALLA: CURSOS
# ─────────────────────────────────────────────
class PantallaCursos(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C_DARK)
        self.pack(fill="both", expand=True)
        self.app = app
        self.curso_sel = tk.StringVar()
        self._construir()

    def _construir(self):
        # Título
        hdr = tk.Frame(self, bg=C_DARK, pady=20)
        hdr.pack(fill="x", padx=32)
        tk.Label(hdr, text="Mis Cursos", font=("Segoe UI Black", 22, "bold"),
                 bg=C_DARK, fg=C_WHITE).pack(side="left")
        BotonUTP(hdr, "➕  Nuevo curso", self._nuevo_curso,
                 ancho=160, alto=36, bg=C_DARK).pack(side="right")

        # Layout dos columnas
        body = tk.Frame(self, bg=C_DARK)
        body.pack(fill="both", expand=True, padx=32)

        # Lista cursos (izquierda)
        izq = tk.Frame(body, bg=C_GRAY, width=260)
        izq.pack(side="left", fill="y", padx=(0, 12))
        izq.pack_propagate(False)

        tk.Label(izq, text="CURSOS REGISTRADOS", font=("Segoe UI", 8, "bold"),
                 bg=C_GRAY, fg=C_TEXT_MUT).pack(anchor="w", padx=14, pady=(14, 4))

        lista_frame = tk.Frame(izq, bg=C_GRAY)
        lista_frame.pack(fill="both", expand=True)

        self.lista_canvas = tk.Canvas(lista_frame, bg=C_GRAY, highlightthickness=0)
        scrollbar = ttk.Scrollbar(lista_frame, orient="vertical", command=self.lista_canvas.yview)
        self.lista_inner = tk.Frame(self.lista_canvas, bg=C_GRAY)

        self.lista_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.lista_canvas.pack(side="left", fill="both", expand=True)
        self.lista_canvas.create_window((0, 0), window=self.lista_inner, anchor="nw")
        self.lista_inner.bind("<Configure>", lambda e: self.lista_canvas.configure(
            scrollregion=self.lista_canvas.bbox("all")))

        # Panel derecho
        self.panel_der = tk.Frame(body, bg=C_DARK)
        self.panel_der.pack(side="left", fill="both", expand=True)

        self._refrescar_lista()

    def _refrescar_lista(self):
        for w in self.lista_inner.winfo_children():
            w.destroy()
        if not self.app.cursos:
            tk.Label(self.lista_inner, text="Sin cursos aún.\nPresiona ➕ para agregar.",
                     font=("Segoe UI", 9), bg=C_GRAY, fg=C_TEXT_MUT,
                     justify="center").pack(pady=30, padx=10)
            return
        for i, curso in enumerate(self.app.cursos):
            f = tk.Frame(self.lista_inner, bg=C_GRAY2, cursor="hand2")
            f.pack(fill="x", padx=8, pady=3)
            n_sec = len(curso.get("secciones", []))
            tk.Label(f, text=curso["nombre"], font=("Segoe UI", 10, "bold"),
                     bg=C_GRAY2, fg=C_WHITE, anchor="w", padx=10, pady=8).pack(fill="x")
            tk.Label(f, text=f"{n_sec} sección(es)", font=("Segoe UI", 8),
                     bg=C_GRAY2, fg=C_TEXT_MUT, anchor="w", padx=10).pack(fill="x")
            f.bind("<Button-1>", lambda e, idx=i: self._ver_curso(idx))
            for child in f.winfo_children():
                child.bind("<Button-1>", lambda e, idx=i: self._ver_curso(idx))

    def _nuevo_curso(self):
        ventana = tk.Toplevel(self.app)
        ventana.title("Nuevo Curso")
        ventana.geometry("400x180")
        ventana.configure(bg=C_DARK)
        ventana.grab_set()

        tk.Label(ventana, text="Nombre del curso", font=("Segoe UI", 10, "bold"),
                 bg=C_DARK, fg=C_WHITE).pack(anchor="w", padx=24, pady=(20, 4))
        entry = tk.Entry(ventana, font=("Segoe UI", 11), bg=C_GRAY, fg=C_WHITE,
                         insertbackground=C_WHITE, relief="flat", bd=8)
        entry.pack(fill="x", padx=24)
        entry.focus_set()

        def guardar():
            nombre = entry.get().strip()
            if not nombre:
                messagebox.showwarning("Campo vacío", "Ingresa el nombre del curso.", parent=ventana)
                return
            self.app.cursos.append({"nombre": nombre, "secciones": []})
            self.app.guardar_cursos()
            ventana.destroy()
            self._refrescar_lista()
            self._ver_curso(len(self.app.cursos) - 1)

        entry.bind("<Return>", lambda e: guardar())
        BotonUTP(ventana, "Guardar curso", guardar, ancho=180, alto=40, bg=C_DARK).pack(pady=16)

    def _ver_curso(self, idx):
        curso = self.app.cursos[idx]
        for w in self.panel_der.winfo_children():
            w.destroy()

        # Encabezado del curso
        hdr = tk.Frame(self.panel_der, bg=C_DARK)
        hdr.pack(fill="x", pady=(0, 12))
        tk.Label(hdr, text=curso["nombre"], font=("Segoe UI Black", 16, "bold"),
                 bg=C_DARK, fg=C_WHITE).pack(side="left")

        def eliminar_curso():
            if messagebox.askyesno("Eliminar", f"¿Eliminar '{curso['nombre']}'?"):
                self.app.cursos.pop(idx)
                self.app.guardar_cursos()
                self._refrescar_lista()
                for w in self.panel_der.winfo_children():
                    w.destroy()

        BotonUTP(hdr, "🗑 Eliminar", eliminar_curso,
                 ancho=120, alto=32, color=C_GRAY2, bg=C_DARK).pack(side="right")
        BotonUTP(hdr, "➕ Sección", lambda: self._nueva_seccion(idx),
                 ancho=130, alto=32, bg=C_DARK).pack(side="right", padx=6)

        # Secciones
        if not curso["secciones"]:
            tk.Label(self.panel_der, text="Sin secciones. Agrega una con ➕ Sección",
                     font=("Segoe UI", 10), bg=C_DARK, fg=C_TEXT_MUT).pack(pady=30)
            return

        scroll_frame = tk.Frame(self.panel_der, bg=C_DARK)
        scroll_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(scroll_frame, bg=C_DARK, highlightthickness=0)
        vsb = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=C_DARK)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        for j, sec in enumerate(curso["secciones"]):
            card = tk.Frame(inner, bg=C_GRAY, padx=16, pady=12)
            card.pack(fill="x", pady=4)

            top = tk.Frame(card, bg=C_GRAY)
            top.pack(fill="x")
            tk.Label(top, text=f"Sección {sec['codigo']}",
                     font=("Segoe UI", 11, "bold"), bg=C_GRAY, fg=C_WHITE).pack(side="left")
            tk.Label(top, text=f"👤 {sec['docente']}",
                     font=("Segoe UI", 9), bg=C_GRAY, fg=C_TEXT_MUT).pack(side="left", padx=12)

            def elim_sec(ci=idx, si=j):
                self.app.cursos[ci]["secciones"].pop(si)
                self.app.guardar_cursos()
                self._ver_curso(ci)

            BotonUTP(top, "✕", lambda ci=idx, si=j: elim_sec(ci, si),
                     ancho=32, alto=26, color=C_GRAY2, bg=C_GRAY).pack(side="right")

            for bloque in sec.get("bloques", []):
                tk.Label(card, text=f"  📅 {bloque['dia']}  {bloque['inicio']} – {bloque['fin']}",
                         font=("Segoe UI", 9), bg=C_GRAY, fg=C_LIGHT).pack(anchor="w", pady=1)

    def _nueva_seccion(self, curso_idx):
        ventana = tk.Toplevel(self.app)
        ventana.title("Nueva Sección")
        ventana.geometry("480x520")
        ventana.configure(bg=C_DARK)
        ventana.grab_set()

        tk.Label(ventana, text="Nueva sección", font=("Segoe UI Black", 14, "bold"),
                 bg=C_DARK, fg=C_WHITE).pack(anchor="w", padx=24, pady=(20, 4))

        def campo(parent, label):
            tk.Label(parent, text=label, font=("Segoe UI", 9, "bold"),
                     bg=C_DARK, fg=C_TEXT_MUT).pack(anchor="w", padx=24, pady=(10, 2))
            e = tk.Entry(parent, font=("Segoe UI", 11), bg=C_GRAY, fg=C_WHITE,
                         insertbackground=C_WHITE, relief="flat", bd=8)
            e.pack(fill="x", padx=24)
            return e

        e_cod = campo(ventana, "Código de sección (ej: 35671)")
        e_doc = campo(ventana, "Nombre del docente")

        # Bloques
        tk.Label(ventana, text="HORARIOS", font=("Segoe UI", 9, "bold"),
                 bg=C_DARK, fg=C_TEXT_MUT).pack(anchor="w", padx=24, pady=(14, 4))

        bloques_frame = tk.Frame(ventana, bg=C_DARK)
        bloques_frame.pack(fill="x", padx=24)
        bloques = []

        def agregar_bloque():
            row = tk.Frame(bloques_frame, bg=C_GRAY, pady=6)
            row.pack(fill="x", pady=3)

            dia_var = tk.StringVar(value=DIAS[0])
            ini_var = tk.StringVar(value="07:00")
            fin_var = tk.StringVar(value="09:00")

            tk.Label(row, text="Día:", bg=C_GRAY, fg=C_WHITE, font=("Segoe UI", 9)).pack(side="left", padx=(8, 2))
            ttk.Combobox(row, textvariable=dia_var, values=DIAS, width=10, state="readonly").pack(side="left", padx=2)
            tk.Label(row, text="De:", bg=C_GRAY, fg=C_WHITE, font=("Segoe UI", 9)).pack(side="left", padx=4)
            ttk.Combobox(row, textvariable=ini_var, values=HORAS, width=7, state="readonly").pack(side="left", padx=2)
            tk.Label(row, text="a:", bg=C_GRAY, fg=C_WHITE, font=("Segoe UI", 9)).pack(side="left", padx=4)
            ttk.Combobox(row, textvariable=fin_var, values=HORAS, width=7, state="readonly").pack(side="left", padx=2)

            bloques.append((dia_var, ini_var, fin_var, row))

            def quitar(r=row, b=(dia_var, ini_var, fin_var)):
                r.destroy()
                bloques.remove((*b, r))

            BotonUTP(row, "✕", quitar, ancho=28, alto=24, color=C_GRAY2, bg=C_GRAY).pack(side="left", padx=4)

        BotonUTP(bloques_frame, "+ Agregar día/hora", agregar_bloque,
                 ancho=180, alto=32, color=C_GRAY2, bg=C_DARK).pack(anchor="w", pady=4)
        agregar_bloque()

        def guardar():
            cod = e_cod.get().strip()
            doc = e_doc.get().strip()
            if not cod or not doc:
                messagebox.showwarning("Campos vacíos", "Completa código y docente.", parent=ventana)
                return
            if not bloques:
                messagebox.showwarning("Sin horarios", "Agrega al menos un bloque horario.", parent=ventana)
                return
            blqs = []
            for dia_v, ini_v, fin_v, _ in bloques:
                ini, fin = ini_v.get(), fin_v.get()
                if hora_a_min(ini) >= hora_a_min(fin):
                    messagebox.showwarning("Horario inválido",
                                           f"La hora de fin debe ser mayor que la de inicio ({dia_v.get()}).",
                                           parent=ventana)
                    return
                blqs.append({"dia": dia_v.get(), "inicio": ini, "fin": fin})
            self.app.cursos[curso_idx]["secciones"].append({
                "codigo": cod, "docente": doc, "bloques": blqs
            })
            self.app.guardar_cursos()
            ventana.destroy()
            self._refrescar_lista()
            self._ver_curso(curso_idx)

        BotonUTP(ventana, "Guardar sección", guardar, ancho=200, alto=40, bg=C_DARK).pack(pady=14)


# ─────────────────────────────────────────────
#  PANTALLA: HORARIO
# ─────────────────────────────────────────────
class PantallaHorario(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C_DARK)
        self.pack(fill="both", expand=True)
        self.app = app
        self._construir()

    def _construir(self):
        hdr = tk.Frame(self, bg=C_DARK, pady=18)
        hdr.pack(fill="x", padx=32)
        tk.Label(hdr, text="Vista del Horario", font=("Segoe UI Black", 22, "bold"),
                 bg=C_DARK, fg=C_WHITE).pack(side="left")
        BotonUTP(hdr, "💾 Guardar en historial", self._guardar_historial,
                 ancho=200, alto=36, bg=C_DARK).pack(side="right")

        conflictos = detectar_conflictos(self.app.cursos)
        if conflictos:
            warn = tk.Frame(self, bg="#3D1A00", padx=16, pady=10)
            warn.pack(fill="x", padx=32, pady=(0, 10))
            tk.Label(warn, text=f"⚠️  {len(conflictos)} conflicto(s) detectado(s):",
                     font=("Segoe UI", 10, "bold"), bg="#3D1A00", fg=C_WARNING).pack(anchor="w")
            for c1, c2 in conflictos[:3]:
                msg = (f"  • {c1['curso']} (Sec. {c1['seccion']}) choca con "
                       f"{c2['curso']} (Sec. {c2['seccion']}) el {c1['dia']}")
                tk.Label(warn, text=msg, font=("Segoe UI", 9),
                         bg="#3D1A00", fg="#FFD580").pack(anchor="w")

        # Grilla
        dias_usados = set()
        for curso in self.app.cursos:
            for sec in curso.get("secciones", []):
                for b in sec.get("bloques", []):
                    dias_usados.add(b["dia"])
        dias = [d for d in DIAS if d in dias_usados] or DIAS[:5]

        horas_int = list(range(7, 22))

        grid_frame = tk.Frame(self, bg=C_DARK)
        grid_frame.pack(fill="both", expand=True, padx=32, pady=(0, 20))

        canvas = tk.Canvas(grid_frame, bg=C_DARK, highlightthickness=0)
        hsb = ttk.Scrollbar(grid_frame, orient="horizontal", command=canvas.xview)
        vsb = ttk.Scrollbar(grid_frame, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=C_DARK)
        canvas.configure(xscrollcommand=hsb.set, yscrollcommand=vsb.set)
        hsb.pack(side="bottom", fill="x")
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        COL_W, ROW_H = 140, 44
        HORA_W = 64

        # Cabecera días
        tk.Frame(inner, bg=C_DARK, width=HORA_W, height=ROW_H).grid(row=0, column=0)
        for col, dia in enumerate(dias):
            tk.Label(inner, text=dia, font=("Segoe UI", 9, "bold"),
                     bg=C_RED, fg=C_WHITE, width=18, height=2).grid(row=0, column=col+1, padx=1, pady=1)

        # Filas de horas
        colores = [C_RED, "#1565C0", "#2E7D32", "#6A1B9A", "#E65100", "#00838F"]
        curso_color = {}
        ci = 0
        for curso in self.app.cursos:
            if curso["nombre"] not in curso_color:
                curso_color[curso["nombre"]] = colores[ci % len(colores)]
                ci += 1

        # Mapa de celdas
        celda_map = {}
        for curso in self.app.cursos:
            for sec in curso.get("secciones", []):
                for blq in sec.get("bloques", []):
                    dia = blq["dia"]
                    if dia not in dias:
                        continue
                    ini_m = hora_a_min(blq["inicio"])
                    fin_m = hora_a_min(blq["fin"])
                    for h in horas_int:
                        h_m = h * 60
                        if ini_m <= h_m < fin_m:
                            key = (dia, h)
                            if key not in celda_map:
                                celda_map[key] = []
                            celda_map[key].append({
                                "curso": curso["nombre"],
                                "sec": sec["codigo"],
                                "color": curso_color[curso["nombre"]]
                            })

        for row, hora in enumerate(horas_int):
            tk.Label(inner, text=f"{hora:02d}:00", font=("Segoe UI", 8),
                     bg=C_DARK, fg=C_TEXT_MUT, width=7).grid(row=row+1, column=0, pady=1)
            for col, dia in enumerate(dias):
                key = (dia, hora)
                bg = C_GRAY if row % 2 == 0 else C_GRAY2
                if key in celda_map:
                    items = celda_map[key]
                    color = items[0]["color"]
                    if len(items) > 1:
                        color = C_WARNING  # conflicto
                    texto = items[0]["curso"][:16]
                    tk.Label(inner, text=texto, font=("Segoe UI", 8),
                             bg=color, fg=C_WHITE, width=18, height=2,
                             relief="flat").grid(row=row+1, column=col+1, padx=1, pady=1)
                else:
                    tk.Label(inner, text="", bg=bg, width=18, height=2).grid(
                        row=row+1, column=col+1, padx=1, pady=1)

    def _guardar_historial(self):
        if not self.app.cursos:
            messagebox.showinfo("Sin datos", "No hay cursos para guardar.")
            return
        entrada = {
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "cursos": [c["nombre"] for c in self.app.cursos],
            "n_secciones": sum(len(c.get("secciones", [])) for c in self.app.cursos),
            "snapshot": self.app.cursos.copy()
        }
        self.app.historial.insert(0, entrada)
        self.app.guardar_historial()
        messagebox.showinfo("Guardado", "✅ Horario guardado en el historial.")


# ─────────────────────────────────────────────
#  PANTALLA: HISTORIAL
# ─────────────────────────────────────────────
class PantallaHistorial(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C_DARK)
        self.pack(fill="both", expand=True)
        self.app = app
        self._construir()

    def _construir(self):
        hdr = tk.Frame(self, bg=C_DARK, pady=18)
        hdr.pack(fill="x", padx=32)
        tk.Label(hdr, text="Historial de Horarios", font=("Segoe UI Black", 22, "bold"),
                 bg=C_DARK, fg=C_WHITE).pack(side="left")

        if not self.app.historial:
            tk.Label(self, text="No hay horarios guardados aún.\nGuarda uno desde la pantalla 'Ver Horario'.",
                     font=("Segoe UI", 11), bg=C_DARK, fg=C_TEXT_MUT,
                     justify="center").pack(expand=True)
            return

        canvas = tk.Canvas(self, bg=C_DARK, highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=C_DARK)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True, padx=32)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        for i, entrada in enumerate(self.app.historial):
            card = tk.Frame(inner, bg=C_GRAY, padx=18, pady=14)
            card.pack(fill="x", pady=5)

            top = tk.Frame(card, bg=C_GRAY)
            top.pack(fill="x")
            tk.Label(top, text=f"📅 {entrada['fecha']}", font=("Segoe UI", 10, "bold"),
                     bg=C_GRAY, fg=C_WHITE).pack(side="left")
            tk.Label(top, text=f"{entrada['n_secciones']} sección(es)",
                     font=("Segoe UI", 8), bg=C_GRAY, fg=C_TEXT_MUT).pack(side="right")

            cursos_texto = "  ·  ".join(entrada.get("cursos", []))
            tk.Label(card, text=cursos_texto, font=("Segoe UI", 9),
                     bg=C_GRAY, fg=C_LIGHT, wraplength=580, justify="left").pack(anchor="w", pady=(4, 0))

            btn_row = tk.Frame(card, bg=C_GRAY)
            btn_row.pack(anchor="w", pady=(10, 0))

            def restaurar(idx=i):
                snap = self.app.historial[idx].get("snapshot", [])
                if snap:
                    self.app.cursos = snap
                    self.app.guardar_cursos()
                    messagebox.showinfo("Restaurado", "✅ Horario restaurado correctamente.")
                    self.app.ir_a("cursos")

            def eliminar(idx=i):
                self.app.historial.pop(idx)
                self.app.guardar_historial()
                self.app.ir_a("historial")

            BotonUTP(btn_row, "↩ Restaurar", restaurar,
                     ancho=130, alto=30, bg=C_GRAY).pack(side="left", padx=4)
            BotonUTP(btn_row, "🗑 Eliminar", eliminar,
                     ancho=110, alto=30, color=C_GRAY2, bg=C_GRAY).pack(side="left", padx=4)



# ─────────────────────────────────────────────
#  PANTALLA: TABLA SEMANAL  (Mejora 1 - Avance 2)
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
#  PANTALLA: PREFERENCIAS DE RANKEADOR  (Mejora 2 - Avance 2)
# ─────────────────────────────────────────────
class PantallaPreferencias(tk.Frame):
    """
    Permite al usuario configurar su turno preferido y dias libres
    antes de rankear las combinaciones de horario.
    Los cambios se persisten en data/preferencias.json
    """

    NOMBRES_TURNO = {
        "manana":     "Mañana  (07:00 – 13:00)",
        "tarde":      "Tarde   (13:00 – 19:00)",
        "noche":      "Noche   (19:00 – 22:00)",
        "cualquiera": "Sin preferencia",
    }

    def __init__(self, parent, app):
        super().__init__(parent, bg=C_DARK)
        self.pack(fill="both", expand=True)
        self.app = app
        self.prefs = cargar_preferencias()
        self._vars_dias = {}
        self._var_turno = tk.StringVar(value=self.prefs.get("turno", "cualquiera"))
        self._construir()

    def _construir(self):
        # ── Header
        hdr = tk.Frame(self, bg=C_DARK, pady=16)
        hdr.pack(fill="x", padx=32)
        tk.Label(hdr, text="Preferencias de Horario",
                 font=("Segoe UI Black", 22, "bold"),
                 bg=C_DARK, fg=C_WHITE).pack(side="left")

        # ── Descripción
        desc = tk.Frame(self, bg=C_GRAY, padx=20, pady=12)
        desc.pack(fill="x", padx=32, pady=(0, 20))
        tk.Label(desc,
                 text=("Configura tus preferencias para que el sistema priorice "
                       "los horarios que mejor se adapten a tu rutina.\n"
                       "Estas preferencias afectan el puntaje al rankear combinaciones."),
                 font=("Segoe UI", 10), bg=C_GRAY, fg=C_LIGHT,
                 wraplength=680, justify="left").pack(anchor="w")

        # ── Contenido en dos columnas
        body = tk.Frame(self, bg=C_DARK)
        body.pack(fill="both", expand=True, padx=32)

        self._seccion_turno(body)
        self._seccion_dias_libres(body)

        # ── Botón guardar
        btn_frame = tk.Frame(self, bg=C_DARK)
        btn_frame.pack(fill="x", padx=32, pady=20)
        BotonUTP(btn_frame, "💾  Guardar preferencias", self._guardar,
                 ancho=220, alto=44, bg=C_DARK).pack(side="left")
        BotonUTP(btn_frame, "↺  Restablecer", self._restablecer,
                 ancho=160, alto=44, color=C_GRAY2, bg=C_DARK).pack(side="left", padx=12)

        # ── Panel de resumen actual
        self._panel_resumen(self)

    def _seccion_turno(self, parent):
        card = tk.Frame(parent, bg=C_GRAY, padx=20, pady=16)
        card.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(card, text="⏰  Turno preferido",
                 font=("Segoe UI", 12, "bold"),
                 bg=C_GRAY, fg=C_WHITE).pack(anchor="w", pady=(0, 8))
        tk.Label(card,
                 text="El rankeador dará más puntos a combinaciones\ndonde la mayoría de clases caigan en este turno.",
                 font=("Segoe UI", 9), bg=C_GRAY, fg=C_TEXT_MUT,
                 justify="left").pack(anchor="w", pady=(0, 12))

        for key, label in self.NOMBRES_TURNO.items():
            color_rb = C_RED if self._var_turno.get() == key else C_GRAY2
            rb = tk.Radiobutton(
                card, text=label,
                variable=self._var_turno, value=key,
                font=("Segoe UI", 10),
                bg=C_GRAY, fg=C_WHITE,
                selectcolor=C_RED,
                activebackground=C_GRAY,
                activeforeground=C_WHITE,
                relief="flat", padx=8, pady=6,
                cursor="hand2"
            )
            rb.pack(anchor="w", pady=2)

    def _seccion_dias_libres(self, parent):
        card = tk.Frame(parent, bg=C_GRAY, padx=20, pady=16)
        card.pack(side="left", fill="both", expand=True, padx=(10, 0))

        tk.Label(card, text="📅  Días libres deseados",
                 font=("Segoe UI", 12, "bold"),
                 bg=C_GRAY, fg=C_WHITE).pack(anchor="w", pady=(0, 8))
        tk.Label(card,
                 text="Marca los días que prefieres no tener clases.\nEl sistema penalizará combinaciones que los ocupen.",
                 font=("Segoe UI", 9), bg=C_GRAY, fg=C_TEXT_MUT,
                 justify="left").pack(anchor="w", pady=(0, 12))

        dias_guardados = self.prefs.get("dias_libres", [])
        for dia in DIAS_SEMANA:
            var = tk.BooleanVar(value=(dia in dias_guardados))
            self._vars_dias[dia] = var
            cb = tk.Checkbutton(
                card, text=dia,
                variable=var,
                font=("Segoe UI", 10),
                bg=C_GRAY, fg=C_WHITE,
                selectcolor=C_RED,
                activebackground=C_GRAY,
                activeforeground=C_WHITE,
                relief="flat", padx=8, pady=4,
                cursor="hand2"
            )
            cb.pack(anchor="w", pady=1)

    def _panel_resumen(self, parent):
        frame = tk.Frame(parent, bg=C_GRAY2, padx=20, pady=10)
        frame.pack(fill="x", padx=32, pady=(0, 16))
        turno_txt = self.NOMBRES_TURNO.get(
            self.prefs.get("turno", "cualquiera"), "Sin preferencia")
        dias_txt = ", ".join(self.prefs.get("dias_libres", [])) or "Ninguno"
        tk.Label(frame,
                 text=f"Configuración actual  →  Turno: {turno_txt}    Días libres: {dias_txt}",
                 font=("Segoe UI", 9), bg=C_GRAY2, fg=C_TEXT_MUT).pack(anchor="w")

    def _guardar(self):
        turno = self._var_turno.get()
        dias_libres = [d for d, v in self._vars_dias.items() if v.get()]

        # Validar: no pueden ser libres TODOS los días
        if len(dias_libres) >= len(DIAS_SEMANA):
            messagebox.showwarning("Selección inválida",
                                   "No puedes marcar todos los días como libres.")
            return

        self.prefs["turno"]      = turno
        self.prefs["dias_libres"] = dias_libres
        guardar_preferencias(self.prefs)

        turno_txt  = self.NOMBRES_TURNO.get(turno, turno)
        dias_texto = ", ".join(dias_libres) if dias_libres else "Ninguno"
        messagebox.showinfo("Guardado",
                            f"✅ Preferencias guardadas.\n\n"
                            f"Turno: {turno_txt}\n"
                            f"Días libres: {dias_texto}\n\n"
                            f"El rankeador usará estas preferencias la próxima vez.")

    def _restablecer(self):
        if messagebox.askyesno("Restablecer", "¿Restablecer preferencias por defecto?"):
            self._var_turno.set("cualquiera")
            for var in self._vars_dias.values():
                var.set(False)
            self.prefs["turno"]       = "cualquiera"
            self.prefs["dias_libres"] = []
            guardar_preferencias(self.prefs)
            messagebox.showinfo("Restablecido", "Preferencias restablecidas.")

class PantallaTabla(tk.Frame):
    """Grilla semanal con franjas de 30 min, colores por curso y exportacion .txt"""

    COLORES_CURSO = [
        "#C0392B", "#1565C0", "#2E7D32", "#6A1B9A",
        "#E65100", "#00838F", "#AD1457", "#558B2F",
    ]
    FRANJA_MIN  = 30
    HORA_INICIO = 7
    HORA_FIN    = 22

    def __init__(self, parent, app):
        super().__init__(parent, bg=C_DARK)
        self.pack(fill="both", expand=True)
        self.app = app
        self._color_curso = {}
        self._asignar_colores()
        self._construir()

    def _asignar_colores(self):
        for i, curso in enumerate(self.app.cursos):
            nombre = curso["nombre"]
            if nombre not in self._color_curso:
                self._color_curso[nombre] = self.COLORES_CURSO[i % len(self.COLORES_CURSO)]

    def _construir(self):
        hdr = tk.Frame(self, bg=C_DARK, pady=16)
        hdr.pack(fill="x", padx=32)
        tk.Label(hdr, text="Tabla Semanal de Horarios",
                 font=("Segoe UI Black", 22, "bold"),
                 bg=C_DARK, fg=C_WHITE).pack(side="left")
        BotonUTP(hdr, "Exportar .txt", self._exportar_txt,
                 ancho=150, alto=36, bg=C_DARK).pack(side="right")

        self._construir_leyenda()

        if not self.app.cursos:
            tk.Label(self,
                     text="No hay cursos registrados.\nVe a Mis Cursos para agregar.",
                     font=("Segoe UI", 11), bg=C_DARK, fg=C_TEXT_MUT,
                     justify="center").pack(expand=True)
            return

        wrap = tk.Frame(self, bg=C_DARK)
        wrap.pack(fill="both", expand=True, padx=32, pady=(0, 16))

        self._canvas = tk.Canvas(wrap, bg=C_DARK, highlightthickness=0)
        hsb = ttk.Scrollbar(wrap, orient="horizontal", command=self._canvas.xview)
        vsb = ttk.Scrollbar(wrap, orient="vertical",   command=self._canvas.yview)
        self._inner = tk.Frame(self._canvas, bg=C_DARK)

        self._canvas.configure(xscrollcommand=hsb.set, yscrollcommand=vsb.set)
        hsb.pack(side="bottom", fill="x")
        vsb.pack(side="right",  fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)
        self._canvas.create_window((0, 0), window=self._inner, anchor="nw")
        self._inner.bind("<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind_all("<MouseWheel>",
            lambda e: self._canvas.yview_scroll(-1*(e.delta//120), "units"))

        self._construir_grilla()

    def _construir_leyenda(self):
        if not self.app.cursos:
            return
        ley = tk.Frame(self, bg=C_GRAY, padx=16, pady=10)
        ley.pack(fill="x", padx=32, pady=(0, 8))
        tk.Label(ley, text="Cursos:", font=("Segoe UI", 9, "bold"),
                 bg=C_GRAY, fg=C_TEXT_MUT).pack(side="left", padx=(0, 12))
        for curso in self.app.cursos:
            nombre = curso["nombre"]
            color  = self._color_curso.get(nombre, C_RED)
            chip   = tk.Frame(ley, bg=color, padx=8, pady=3)
            chip.pack(side="left", padx=4)
            tk.Label(chip, text=nombre[:22], font=("Segoe UI", 8, "bold"),
                     bg=color, fg=C_WHITE).pack()

    def _get_dias_y_mapa(self):
        dias_con_clases = set()
        mapa = {}
        for curso in self.app.cursos:
            for sec in curso.get("secciones", []):
                for blq in sec.get("bloques", []):
                    dia = blq["dia"]
                    dias_con_clases.add(dia)
                    ini_m = hora_a_min(blq["inicio"])
                    fin_m = hora_a_min(blq["fin"])
                    f = (ini_m // self.FRANJA_MIN) * self.FRANJA_MIN
                    while f < fin_m:
                        key = (dia, f)
                        mapa.setdefault(key, []).append({
                            "curso":   curso["nombre"],
                            "seccion": sec["codigo"],
                            "docente": sec["docente"],
                            "inicio":  blq["inicio"],
                            "fin":     blq["fin"],
                            "color":   self._color_curso.get(curso["nombre"], C_RED),
                        })
                        f += self.FRANJA_MIN
        dias = [d for d in DIAS if d in dias_con_clases] or DIAS[:5]
        return dias, mapa

    def _construir_grilla(self):
        inner = self._inner
        dias, mapa = self._get_dias_y_mapa()

        # Cabecera
        tk.Label(inner, text="Hora", font=("Segoe UI", 8, "bold"),
                 bg=C_GRAY2, fg=C_TEXT_MUT,
                 width=7, height=2, anchor="center").grid(
                     row=0, column=0, padx=1, pady=1, sticky="nsew")

        for col, dia in enumerate(dias):
            tk.Label(inner, text=dia, font=("Segoe UI", 9, "bold"),
                     bg=C_RED, fg=C_WHITE,
                     width=20, height=2, anchor="center").grid(
                         row=0, column=col+1, padx=1, pady=1, sticky="nsew")

        # Franjas
        m = self.HORA_INICIO * 60
        row = 1
        while m < self.HORA_FIN * 60:
            hh, mm = m // 60, m % 60
            bg_row = C_GRAY if (row % 2 == 0) else C_GRAY2

            tk.Label(inner, text=f"{hh:02d}:{mm:02d}", font=("Segoe UI", 7),
                     bg=bg_row, fg=C_TEXT_MUT,
                     width=7, height=1, anchor="center").grid(
                         row=row, column=0, padx=1, pady=0, sticky="nsew")

            for col, dia in enumerate(dias):
                key = (dia, m)
                if key in mapa:
                    items = mapa[key]
                    if len(items) > 1:
                        bg_cell, fg_cell = C_WARNING, C_BLACK
                        texto = "CONFLICTO"
                    else:
                        bg_cell = items[0]["color"]
                        fg_cell = C_WHITE
                        ini_m_clase = hora_a_min(items[0]["inicio"])
                        if m == (ini_m_clase // self.FRANJA_MIN) * self.FRANJA_MIN:
                            texto = items[0]["curso"][:18]
                        else:
                            texto = ""

                    lbl = tk.Label(inner, text=texto,
                                   font=("Segoe UI", 7, "bold"),
                                   bg=bg_cell, fg=fg_cell,
                                   width=20, height=1, anchor="w", padx=4)
                    lbl.grid(row=row, column=col+1, padx=1, pady=0, sticky="nsew")

                    tip = (f"{mapa[key][0]['curso']}\n"
                           f"Sec.{mapa[key][0]['seccion']} - {mapa[key][0]['docente']}\n"
                           f"{mapa[key][0]['inicio']} - {mapa[key][0]['fin']}")
                    self._bind_tooltip(lbl, tip)
                else:
                    tk.Label(inner, text="", bg=bg_row, width=20, height=1).grid(
                        row=row, column=col+1, padx=1, pady=0, sticky="nsew")

            m += self.FRANJA_MIN
            row += 1

    def _bind_tooltip(self, widget, texto):
        tip = None

        def mostrar(e):
            nonlocal tip
            tip = tk.Toplevel(widget)
            tip.wm_overrideredirect(True)
            tip.wm_geometry(f"+{e.x_root+12}+{e.y_root+8}")
            tk.Label(tip, text=texto, font=("Segoe UI", 8),
                     bg="#FFFFCC", fg=C_BLACK, relief="solid", bd=1,
                     padx=6, pady=4, justify="left").pack()

        def ocultar(e):
            nonlocal tip
            if tip:
                tip.destroy()
                tip = None

        widget.bind("<Enter>", mostrar)
        widget.bind("<Leave>", ocultar)

    def _exportar_txt(self):
        if not self.app.cursos:
            messagebox.showinfo("Sin datos", "No hay cursos para exportar.")
            return

        dias, _ = self._get_dias_y_mapa()
        mapa_txt = {}
        for curso in self.app.cursos:
            for sec in curso.get("secciones", []):
                for blq in sec.get("bloques", []):
                    dia = blq["dia"]
                    ini_m = hora_a_min(blq["inicio"])
                    fin_m = hora_a_min(blq["fin"])
                    f = (ini_m // self.FRANJA_MIN) * self.FRANJA_MIN
                    while f < fin_m:
                        key = (dia, f)
                        mapa_txt.setdefault(key, []).append(
                            f"{curso['nombre']}[{sec['codigo']}]")
                        f += self.FRANJA_MIN

        COL = 22
        lineas = [
            "UNIHORARIO - Tabla Semanal de Horarios",
            "=" * (8 + (COL + 1) * len(dias)),
            f"{'Hora':<7}" + "".join(f"|{d:^{COL}}" for d in dias),
        ]
        lineas.append("-" * len(lineas[-1]))

        m = self.HORA_INICIO * 60
        while m < self.HORA_FIN * 60:
            hh, mm = m // 60, m % 60
            fila = f"{hh:02d}:{mm:02d} "
            for dia in dias:
                items = mapa_txt.get((dia, m), [])
                if items:
                    cont = "CONFLICTO" if len(items) > 1 else items[0][:COL-2]
                else:
                    cont = ""
                fila += f"|{cont:<{COL}}"
            lineas.append(fila)
            m += self.FRANJA_MIN

        lineas += ["-" * len(lineas[2]), "", "Generado por UniHorario - UTP"]

        import tkinter.filedialog as fd
        ruta = fd.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")],
            initialfile="horario_semanal.txt",
            title="Guardar tabla como..."
        )
        if ruta:
            with open(ruta, "w", encoding="utf-8") as fh:
                fh.write("\n".join(lineas))
            messagebox.showinfo("Exportado", f"Tabla guardada en:\n{ruta}")

# ─────────────────────────────────────────────
#  ESTILOS TTK
# ─────────────────────────────────────────────
def aplicar_estilos():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TScrollbar", background=C_GRAY2, troughcolor=C_DARK,
                    arrowcolor=C_TEXT_MUT, borderwidth=0)
    style.configure("TCombobox", fieldbackground=C_GRAY, background=C_GRAY,
                    foreground=C_WHITE, arrowcolor=C_WHITE, borderwidth=0)
    style.map("TCombobox", fieldbackground=[("readonly", C_GRAY)],
              foreground=[("readonly", C_WHITE)])


# ─────────────────────────────────────────────
#  PUNTO DE ENTRADA
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = UniHorarioApp()
    aplicar_estilos()
    app.mainloop()