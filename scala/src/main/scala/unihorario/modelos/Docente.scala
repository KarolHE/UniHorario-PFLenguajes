package unihorario.modelos

case class Docente(
  id: String,
  nombre: String,
  maxHorasDia: Int = 3,
  disponibilidad: List[String] = List("lunes", "martes", "miercoles", "jueves", "viernes"),
  franjaPreferida: String = "manana"
) {
  require(maxHorasDia >= 1 && maxHorasDia <= 8,
    s"El docente $nombre debe tener entre 1 y 8 horas máximas por día")
  require(
    franjaPreferida == "manana" || franjaPreferida == "tarde" || franjaPreferida == "noche",
    s"La franja '$franjaPreferida' no es válida. Use 'manana', 'tarde' o 'noche'"
  )

  def disponibleEn(dia: String): Boolean =
    disponibilidad.map(_.toLowerCase).contains(dia.toLowerCase)

  def maxHorasSemanales: Int = maxHorasDia * disponibilidad.length

  override def toString: String =
    s"Docente[$id] $nombre | Máx $maxHorasDia h/día | " +
    s"Disponible: ${disponibilidad.mkString(", ")} | Prefiere: $franjaPreferida"
}

object Docente {
  val DIAS_VALIDOS = List("lunes", "martes", "miercoles", "jueves", "viernes", "sabado")

  def fromCSV(linea: String): Option[Docente] = {
    val campos = linea.split(",").map(_.trim)
    if (campos.length < 4) return None
    try {
      val dias = campos(3).split("-").map(_.trim).toList
        .filter(DIAS_VALIDOS.contains)
      Some(Docente(
        id              = campos(0),
        nombre          = campos(1),
        maxHorasDia     = campos(2).toInt,
        disponibilidad  = if (dias.nonEmpty) dias else DIAS_VALIDOS.take(5),
        franjaPreferida = if (campos.length > 4 && campos(4).nonEmpty) campos(4) else "manana"
      ))
    } catch {
      case _: Exception => None
    }
  }
}