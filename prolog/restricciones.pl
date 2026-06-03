% ============================================================
%  restricciones.pl — Reglas de validación de horarios
%  UniHorario | Módulo Prolog
%  Nota: hechos.pl es generado automáticamente por Scala
% ============================================================


% ------------------------------------------------------------
% PARTE 1: Conversión de horas a minutos
% ------------------------------------------------------------
% Scala exporta las horas como enteros: 800 = 8:00, 1330 = 13:30
% Convertimos a minutos para poder comparar correctamente.
% Ejemplo: 800  -> 8*60 + 0  = 480 minutos
%          830  -> 8*60 + 30 = 510 minutos
%          1330 -> 13*60 + 30 = 810 minutos

a_minutos(Hora, Minutos) :-
    Horas is Hora // 100,
    Mins  is Hora mod 100,
    Minutos is Horas * 60 + Mins.


% ------------------------------------------------------------
% PARTE 2: Detección de solapamiento entre dos bloques
% ------------------------------------------------------------
% Dos bloques se solapan si:
%   - Son el mismo día, Y
%   - El bloque A empieza antes de que termine el bloque B, Y
%   - El bloque B empieza antes de que termine el bloque A

bloques_solapan(Dia, InicioA, FinA, Dia, InicioB, FinB) :-
    a_minutos(InicioA, IniAMin),
    a_minutos(FinA,    FinAMin),
    a_minutos(InicioB, IniBMin),
    a_minutos(FinB,    FinBMin),
    IniAMin < FinBMin,
    IniBMin < FinAMin.


% ------------------------------------------------------------
% PARTE 3: Verificar si dos secciones tienen conflicto horario
% ------------------------------------------------------------
% Dos secciones chocan si tienen al menos un par de bloques
% que se solapan.

secciones_chocan(SecA, SecB) :-
    SecA \= SecB,
    horario(SecA, DiaA, IniA, FinA),
    horario(SecB, DiaB, IniB, FinB),
    bloques_solapan(DiaA, IniA, FinA, DiaB, IniB, FinB).


% ------------------------------------------------------------
% PARTE 4: Explicación del conflicto (mensaje descriptivo)
% ------------------------------------------------------------
% Cuando dos secciones chocan, genera un mensaje legible
% indicando qué secciones y en qué día ocurre el conflicto.
% Ejemplo de salida:
%   Conflicto: Sección 35671 (matematica_ii, Dr. García)
%   choca con Sección 38421 (fisica_i, Mg. Torres) el lunes

explicar_conflicto(SecA, SecB) :-
    secciones_chocan(SecA, SecB),
    seccion(SecA, CursoA, DocenteA),
    seccion(SecB, CursoB, DocenteB),
    horario(SecA, Dia, IniA, FinA),
    horario(SecB, Dia, IniB, FinB),
    bloques_solapan(Dia, IniA, FinA, Dia, IniB, FinB),
    format("Conflicto: Sección ~w (~w, ~w) choca con Sección ~w (~w, ~w) el ~w~n",
           [SecA, CursoA, DocenteA, SecB, CursoB, DocenteB, Dia]).


% ------------------------------------------------------------
% PARTE 5: Verificar si una sección es válida individualmente
% ------------------------------------------------------------
% Una sección es válida si existe en la base de conocimiento
% y tiene al menos un bloque horario registrado.

seccion_valida(Sec) :-
    seccion(Sec, _, _),
    horario(Sec, _, _, _).


% ------------------------------------------------------------
% PARTE 6: Verificar si una combinación de secciones es válida
% ------------------------------------------------------------
% Una lista de secciones es válida si ningún par de secciones
% dentro de ella tiene conflicto horario.

combinacion_valida([]).
combinacion_valida([_]).
combinacion_valida([Sec | Resto]) :-
    \+ (member(Otra, Resto), secciones_chocan(Sec, Otra)),
    combinacion_valida(Resto).