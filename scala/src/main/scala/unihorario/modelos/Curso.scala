package unihorario.modelos
 
case class Curso(
  id: String,
  nombre: String,
  horasSemanales: Int,
  prerequisito: Option[String] = None,
  tipoAula: String = "teoria"
) {
  require(horasSemanales > 0, s"El curso $nombre debe tener al menos 1 hora semanal")
  require(
    tipoAula == "teoria" || tipoAula == "laboratorio",
    s"El tipo de aula '$tipoAula' no es válido. Use 'teoria' o 'laboratorio'"
  )
 
  def tienePrerequisito: Boolean = prerequisito.isDefined
 
  def necesitaLaboratorio: Boolean = tipoAula == "laboratorio"
 
  override def toString: String =
    s"Curso[$id] $nombre ($horasSemanales h/sem)" +
    prerequisito.map(p => s" | Prerequisito: $p").getOrElse("") +
    s" | Aula: $tipoAula"
}
 
object Curso {
  def fromCSV(linea: String): Option[Curso] = {
    val campos = linea.split(",").map(_.trim)
    if (campos.length < 4) return None
    try {
      Some(Curso(
        id             = campos(0),
        nombre         = campos(1),
        horasSemanales = campos(2).toInt,
        prerequisito   = if (campos(3).isEmpty) None else Some(campos(3)),
        tipoAula       = if (campos.length > 4 && campos(4).nonEmpty) campos(4) else "teoria"
      ))
    } catch {
      case _: Exception => None
    }
  }
}
 