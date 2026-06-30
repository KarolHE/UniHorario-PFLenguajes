% ============================================================
%  restricciones.pl — Reglas de validación de horarios
%  UniHorario | Módulo Prolog
%  Nota: hechos.pl es generado automáticamente por Scala
% ============================================================

a_minutos(Hora, Minutos) :-
    Horas is Hora // 100,
    Mins  is Hora mod 100,
    Minutos is Horas * 60 + Mins.

bloques_solapan(Dia, InicioA, FinA, Dia, InicioB, FinB) :-
    a_minutos(InicioA, IniAMin),
    a_minutos(FinA,    FinAMin),
    a_minutos(InicioB, IniBMin),
    a_minutos(FinB,    FinBMin),
    IniAMin < FinBMin,
    IniBMin < FinAMin.

secciones_chocan(SecA, SecB) :-
    SecA \= SecB,
    horario(SecA, DiaA, IniA, FinA),
    horario(SecB, DiaB, IniB, FinB),
    bloques_solapan(DiaA, IniA, FinA, DiaB, IniB, FinB).

explicar_conflicto(SecA, SecB) :-
    secciones_chocan(SecA, SecB),
    seccion(SecA, CursoA, DocenteA),
    seccion(SecB, CursoB, DocenteB),
    horario(SecA, Dia, IniA, FinA),
    horario(SecB, Dia, IniB, FinB),
    bloques_solapan(Dia, IniA, FinA, Dia, IniB, FinB),
    format("Conflicto: Sección ~w (~w, ~w) choca con Sección ~w (~w, ~w) el ~w~n",
           [SecA, CursoA, DocenteA, SecB, CursoB, DocenteB, Dia]).

seccion_valida(Sec) :-
    seccion(Sec, _, _),
    horario(Sec, _, _, _).

combinacion_valida([]).
combinacion_valida([_]).
combinacion_valida([Sec | Resto]) :-
    \+ (member(Otra, Resto), secciones_chocan(Sec, Otra)),
    combinacion_valida(Resto).