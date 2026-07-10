% ============================================================
%  consultas.pl — Interfaz de consultas para Python
%  UniHorario | Módulo Prolog
%  Requiere: hechos.pl (generado por Scala), restricciones.pl,
%            combinador.pl
% ============================================================

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