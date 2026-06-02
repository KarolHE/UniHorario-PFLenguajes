package unihorario.modelos

case class Aula(
  id: String,
  nombre: String,
  capacidad: Int,
  tipo: String = "teoria"
) {
  require(capacidad > 0, s"El aula $nombre debe tener capacidad mayor a 0")
  require(
    tipo == "teoria" || tipo == "laboratorio" || tipo == "auditorio",
    s"El tipo '$tipo' no es válido. Use 'teoria', 'laboratorio' o 'auditorio'"
  )

  def esLaboratorio: Boolean = tipo == "laboratorio"

  def esAuditorio: Boolean = tipo == "auditorio"

  def puedeAlbergar(cantidadAlumnos: Int): Boolean =
    cantidadAlumnos <= capacidad

  def esCompatibleCon(curso: Curso): Boolean =
    tipo == curso.tipoAula

  override def toString: String =
    s"Aula[$id] $nombre | Capacidad: $capacidad | Tipo: $tipo"
}

object Aula {
  def fromCSV(linea: String): Option[Aula] = {
    val campos = linea.split(",").map(_.trim)
    if (campos.length < 4) return None
    try {
      Some(Aula(
        id        = campos(0),
        nombre    = campos(1),
        capacidad = campos(2).toInt,
        tipo      = if (campos(3).nonEmpty) campos(3) else "teoria"
      ))
    } catch {
      case _: Exception => None
    }
  }
}