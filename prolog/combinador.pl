% ============================================================
%  combinador.pl — Generación de combinaciones válidas
%  UniHorario | Módulo Prolog
%  Requiere: hechos.pl (generado por Scala), restricciones.pl
% ============================================================

:- ensure_loaded(restricciones).


% ------------------------------------------------------------
% PARTE 1: Obtener todas las secciones de un curso
% ------------------------------------------------------------
% Dado un curso (ej: 'matematica_ii'), devuelve todas
% sus secciones registradas en hechos.pl

secciones_de_curso(Curso, Secciones) :-
    findall(Sec, seccion(Sec, Curso, _), Secciones).


% ------------------------------------------------------------
% PARTE 2: Elegir una sección por curso
% ------------------------------------------------------------
% De una lista de cursos, elige exactamente UNA sección
% por cada curso. El resultado es una lista de secciones,
% una por curso.

elegir_una_por_curso([], []).
elegir_una_por_curso([Curso | Resto], [Sec | Seleccion]) :-
    secciones_de_curso(Curso, Secciones),
    Secciones \= [],
    member(Sec, Secciones),
    elegir_una_por_curso(Resto, Seleccion).


% ------------------------------------------------------------
% PARTE 3: Obtener todos los cursos disponibles
% ------------------------------------------------------------
% Recorre hechos.pl y obtiene la lista de cursos únicos
% registrados (sin repeticiones).

todos_los_cursos(Cursos) :-
    findall(C, curso(C, _), TodosConRepetidos),
    list_to_set(TodosConRepetidos, Cursos).


% ------------------------------------------------------------
% PARTE 4: Generar combinaciones válidas
% ------------------------------------------------------------
% Para una lista de cursos dada, genera todas las
% combinaciones posibles (una sección por curso) que
% NO tengan conflictos horarios entre sí.

combinaciones_validas(Cursos, Combinacion) :-
    elegir_una_por_curso(Cursos, Combinacion),
    combinacion_valida(Combinacion).


% ------------------------------------------------------------
% PARTE 5: Recolectar todas las combinaciones válidas
% ------------------------------------------------------------
% Devuelve en una lista TODAS las combinaciones válidas
% para los cursos dados. Útil para que Python las reciba.

todas_las_combinaciones(Cursos, Todas) :-
    findall(
        Combinacion,
        combinaciones_validas(Cursos, Combinacion),
        Todas
    ).


% ------------------------------------------------------------
% PARTE 6: Buscar combinaciones con cursos específicos
% ------------------------------------------------------------
% Permite buscar combinaciones válidas para una sublista
% de cursos seleccionados (no necesariamente todos).

combinaciones_para(Cursos, Todas) :-
    todas_las_combinaciones(Cursos, Todas).


% ------------------------------------------------------------
% PARTE 7: Mostrar combinaciones en consola (modo debug)
% ------------------------------------------------------------
% Imprime todas las combinaciones válidas encontradas
% junto con el total. Útil para probar desde SWI-Prolog.

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