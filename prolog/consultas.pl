% ============================================================
%  consultas.pl — Interfaz de consultas para Python
%  UniHorario | Módulo Prolog
%  Requiere: hechos.pl (generado por Scala), restricciones.pl,
%            combinador.pl
% ============================================================

:- ensure_loaded(hechos).
:- ensure_loaded(restricciones).
:- ensure_loaded(combinador).

consultar_combinaciones(Cursos, Resultado) :-
    todas_las_combinaciones(Cursos, Resultado).

hay_conflicto(SecA, SecB) :-
    secciones_chocan(SecA, SecB).

todos_los_conflictos(SecA, SecB) :-
    seccion(SecA, _, _),
    seccion(SecB, _, _),
    SecA @< SecB,
    secciones_chocan(SecA, SecB).

detalle_combinacion([], []).
detalle_combinacion([Sec | Resto], [Info | InfoResto]) :-
    seccion(Sec, Curso, Docente),
    findall(
        bloque(Dia, Ini, Fin),
        horario(Sec, Dia, Ini, Fin),
        Bloques
    ),
    Info = seccion(Sec, Curso, Docente, Bloques),
    detalle_combinacion(Resto, InfoResto).

secciones_disponibles(Curso, Secciones) :-
    secciones_de_curso(Curso, Secciones).

cursos_registrados(Cursos) :-
    todos_los_cursos(Cursos).

es_combinacion_valida(Secciones) :-
    combinacion_valida(Secciones).

resumen_sistema :-
    todos_los_cursos(Cursos),
    length(Cursos, NCursos),
    findall(S, seccion(S, _, _), Secciones),
    length(Secciones, NSecciones),
    findall(H, horario(H, _, _, _), Horarios),
    length(Horarios, NHorarios),
    format("~n=== Estado del sistema UniHorario ===~n"),
    format("  Cursos registrados  : ~w~n", [NCursos]),
    format("  Secciones totales   : ~w~n", [NSecciones]),
    format("  Bloques horarios    : ~w~n", [NHorarios]),
    format("=====================================~n").

% ============================================================
%  VALIDACIÓN MANUAL (Mejora 4 — Avance 2)
%  El estudiante elige una sección por curso desde la UI.
%  Esta consulta verifica si la selección es válida y, de no
%  serlo, devuelve el detalle de cada par de secciones en conflicto.
% ============================================================

% Lista de pares de secciones que chocan dentro de una selección dada.
conflictos_en_seleccion([], []).
conflictos_en_seleccion([Sec | Resto], Conflictos) :-
    findall(
        par(Sec, Otra),
        (member(Otra, Resto), secciones_chocan(Sec, Otra)),
        ConflictosAqui
    ),
    conflictos_en_seleccion(Resto, ConflictosResto),
    append(ConflictosAqui, ConflictosResto, Conflictos).

% Punto de entrada llamado desde Python (prolog_bridge.py).
% Recibe la lista de codigos de seccion elegidos por el usuario,
% vía variable de entorno o argumento, y escribe el resultado en JSON
% por salida estándar para que Python lo capture.
validar_seleccion(Secciones, Valida, Conflictos) :-
    conflictos_en_seleccion(Secciones, Conflictos),
    ( Conflictos == [] -> Valida = true ; Valida = false ).

% Formatea un conflicto par(SecA, SecB) como texto legible con motivo.
formatear_conflicto(par(SecA, SecB), Texto) :-
    seccion(SecA, CursoA, DocenteA),
    seccion(SecB, CursoB, DocenteB),
    horario(SecA, Dia, IniA, FinA),
    horario(SecB, Dia, IniB, FinB),
    bloques_solapan(Dia, IniA, FinA, Dia, IniB, FinB),
    !,
    format(atom(Texto),
           "~w (~w, ~w) choca con ~w (~w, ~w) el ~w de ~w a ~w",
           [SecA, CursoA, DocenteA, SecB, CursoB, DocenteB, Dia, IniA, FinA]).
formatear_conflicto(par(SecA, SecB), Texto) :-
    format(atom(Texto), "~w choca con ~w", [SecA, SecB]).

% Consulta principal expuesta a Python: recibe lista de secciones
% (atoms) ya parseada por el bridge y devuelve un termino Prolog
% que el bridge convierte a JSON antes de imprimirlo en stdout.
validar_seleccion_resultado(Secciones, resultado(Valida, TextosConflictos)) :-
    validar_seleccion(Secciones, Valida, Conflictos),
    maplist(formatear_conflicto, Conflictos, TextosConflictos).