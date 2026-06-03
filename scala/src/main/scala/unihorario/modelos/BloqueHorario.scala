package unihorario.modelos

case class BloqueHorario(
  dia: String,
  horaInicio: String,
  horaFin: String
) {
  require(
    List("lunes","martes","miercoles","jueves","viernes","sabado").contains(dia.toLowerCase),
    s"El día '$dia' no es válido"
  )
  require(BloqueHorario.formatoValido(horaInicio), s"Hora de inicio inválida: '$horaInicio'. Use formato HH:MM")
  require(BloqueHorario.formatoValido(horaFin),    s"Hora de fin inválida: '$horaFin'. Use formato HH:MM")
  require(
    BloqueHorario.aMinutos(horaFin) > BloqueHorario.aMinutos(horaInicio),
    s"La hora de fin debe ser mayor a la de inicio"
  )

  private def inicioEnMinutos: Int = BloqueHorario.aMinutos(horaInicio)
  private def finEnMinutos: Int    = BloqueHorario.aMinutos(horaFin)

  def seSolapaCon(otro: BloqueHorario): Boolean =
    dia.toLowerCase == otro.dia.toLowerCase &&
    inicioEnMinutos < BloqueHorario.aMinutos(otro.horaFin) &&
    BloqueHorario.aMinutos(otro.horaInicio) < finEnMinutos

  override def toString: String =
    s"$dia $horaInicio - $horaFin"
}

object BloqueHorario {

  // Valida formato HH:MM con cualquier minuto entre 00 y 59, rango 7:00 - 22:00
  def formatoValido(hora: String): Boolean = {
    val partes = hora.split(":")
    if (partes.length != 2) return false
    try {
      val h = partes(0).toInt
      val m = partes(1).toInt
      h >= 7 && h <= 22 && m >= 0 && m <= 59 && !(h == 22 && m > 0)
    } catch {
      case _: Exception => false
    }
  }

  // Convierte "7:45" → 465 minutos
  def aMinutos(hora: String): Int = {
    val partes = hora.split(":")
    partes(0).toInt * 60 + partes(1).toInt
  }
}