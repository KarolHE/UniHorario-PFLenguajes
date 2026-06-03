% ============================================================
%  consultas.pl — Interfaz de consultas para Python
%  UniHorario | Módulo Prolog
%  Requiere: hechos.pl (generado por Scala), restricciones.pl,
%            combinador.pl
% ============================================================

:- ensure_loaded(restricciones).
:- ensure_loaded(combinador).


% ------------------------------------------------------------
% PARTE 1: Consulta principal — obtener combinaciones válidas
% ------------------------------------------------------------
% Python llama esta regla pasando una lista de cursos.
% Devuelve todas las combinaciones válidas encontradas.
%
% Ejemplo desde Python (via pyswip):
%   list(prolog.query("consultar_combinaciones(['matematica_ii','fisica_i'], Resultado)"))

consultar_combinaciones(Cursos, Resultado) :-
    todas_las_combinaciones(Cursos, Resultado).


% ------------------------------------------------------------
% PARTE 2: Consulta de conflictos entre dos secciones
% ------------------------------------------------------------
% Verifica si dos secciones específicas tienen conflicto.
% Devuelve true/false. Python puede usarlo para validar
% antes de armar una combinación.
%
% Ejemplo:
%   prolog.query("hay_conflicto('35671', '38421')")

hay_conflicto(SecA, SecB) :-
    secciones_chocan(SecA, SecB).


% ------------------------------------------------------------
% PARTE 3: Consulta de todos los conflictos existentes
% ------------------------------------------------------------
% Devuelve todos los pares de secciones que tienen conflicto
% en la base de conocimiento actual.
%
% Ejemplo:
%   list(prolog.query("todos_los_conflictos(SecA, SecB)"))

todos_los_conflictos(SecA, SecB) :-
    seccion(SecA, _, _),
    seccion(SecB, _, _),
    SecA @< SecB,
    secciones_chocan(SecA, SecB).


% ------------------------------------------------------------
% PARTE 4: Consulta de detalle de una combinación
% ------------------------------------------------------------
% Dado una lista de secciones (una combinación), devuelve
% la información completa de cada sección:
%   Sec, Curso, Docente, Dia, HoraInicio, HoraFin

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


% ------------------------------------------------------------
% PARTE 5: Consulta de secciones disponibles por curso
% ------------------------------------------------------------
% Python puede pedir qué secciones existen para un curso.
%
% Ejemplo:
%   list(prolog.query("secciones_disponibles('matematica_ii', Secs)"))

secciones_disponibles(Curso, Secciones) :-
    secciones_de_curso(Curso, Secciones).


% ------------------------------------------------------------
% PARTE 6: Consulta de cursos registrados
% ------------------------------------------------------------
% Devuelve todos los cursos que están en hechos.pl.
% Python lo usa para saber qué cursos puede combinar.
%
% Ejemplo:
%   list(prolog.query("cursos_registrados(Cursos)"))

cursos_registrados(Cursos) :-
    todos_los_cursos(Cursos).


% ------------------------------------------------------------
% PARTE 7: Validar una combinación puntual
% ------------------------------------------------------------
% Python arma una combinación y pregunta si es válida.
% Devuelve true si no hay ningún conflicto.
%
% Ejemplo:
%   prolog.query("es_combinacion_valida(['35671','48201'])")

es_combinacion_valida(Secciones) :-
    combinacion_valida(Secciones).


% ------------------------------------------------------------
% PARTE 8: Resumen del estado del sistema
% ------------------------------------------------------------
% Útil para que Python verifique que Prolog cargó bien
% los datos antes de hacer consultas.

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