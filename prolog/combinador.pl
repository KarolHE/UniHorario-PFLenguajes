% ============================================================
%  combinador.pl — Generación de combinaciones válidas
%  UniHorario | Módulo Prolog
%  Requiere: hechos.pl (generado por Scala), restricciones.pl
% ============================================================

:- ensure_loaded(restricciones).

secciones_de_curso(Curso, Secciones) :-
    findall(Sec, seccion(Sec, Curso, _), Secciones).

elegir_una_por_curso([], []).
elegir_una_por_curso([Curso | Resto], [Sec | Seleccion]) :-
    secciones_de_curso(Curso, Secciones),
    Secciones \= [],
    member(Sec, Secciones),
    elegir_una_por_curso(Resto, Seleccion).

todos_los_cursos(Cursos) :-
    findall(C, curso(C, _), TodosConRepetidos),
    list_to_set(TodosConRepetidos, Cursos).

combinaciones_validas(Cursos, Combinacion) :-
    elegir_una_por_curso(Cursos, Combinacion),
    combinacion_valida(Combinacion).

todas_las_combinaciones(Cursos, Todas) :-
    findall(
        Combinacion,
        combinaciones_validas(Cursos, Combinacion),
        Todas
    ).

combinaciones_para(Cursos, Todas) :-
    todas_las_combinaciones(Cursos, Todas).

mostrar_combinaciones(Cursos) :-
    todas_las_combinaciones(Cursos, Todas),
    length(Todas, Total),
    format("~nCombinaciones válidas encontradas: ~w~n", [Total]),
    format("-------------------------------------------~n"),
    forall(
        nth1(I, Todas, Combo),
        (
            format("Combinación ~w:~n", [I]),
            forall(
                member(Sec, Combo),
                (
                    seccion(Sec, Curso, Docente),
                    format("  - ~w | ~w | ~w~n", [Sec, Curso, Docente])
                )
            ),
            nl
        )
    ).