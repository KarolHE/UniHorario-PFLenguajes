package unihorario.modelos

case class BloqueHorario(
  id: String,
  curso: Curso,
  docente: Docente,
  aula: Aula,
  dia: String,
  horaInicio: Int,
  duracion: Int
) {
  require(
    List("lunes","martes","miercoles","jueves","viernes","sabado").contains(dia),
    s"El día '$dia' no es válido"
  )
  require(horaInicio >= 7 && horaInicio <= 21,
    s"La hora de inicio $horaInicio está fuera del rango permitido (7–21)")
  require(duracion >= 1 && duracion <= 4,
    s"La duración $duracion no es válida. Debe ser entre 1 y 4 horas")
  require(horaInicio + duracion <= 22,
    s"El bloque excede el horario permitido (máx 22:00)")

  def horaFin: Int = horaInicio + duracion

  def franja: String = horaInicio match {
    case h if h >= 7  && h < 13 => "manana"
    case h if h >= 13 && h < 18 => "tarde"
    case _                       => "noche"
  }

  def seSolapaConBloque(otro: BloqueHorario): Boolean =
    dia == otro.dia &&
    horaInicio < otro.horaFin &&
    otro.horaInicio < horaFin

  def conflictoDeDocente(otro: BloqueHorario): Boolean =
    docente.id == otro.docente.id && seSolapaConBloque(otro)

  def conflictoDeAula(otro: BloqueHorario): Boolean =
    aula.id == otro.aula.id && seSolapaConBloque(otro)

  def toPrologHecho: String =
    s"""bloque('$id', '${curso.id}', '${docente.id}', '${aula.id}', $dia, $horaInicio, $horaFin)."""

  override def toString: String =
    s"[$dia $horaInicio:00–$horaFin:00] ${curso.nombre} | ${docente.nombre} | ${aula.nombre}"
}