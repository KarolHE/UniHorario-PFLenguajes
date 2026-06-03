package unihorario.modelos

case class Seccion(
  codigo: String,
  docente: String,
  bloques: List[BloqueHorario]
) {
  require(codigo.nonEmpty,  "El código de sección no puede estar vacío")
  require(docente.nonEmpty, "El nombre del docente no puede estar vacío")
  require(bloques.nonEmpty, "La sección debe tener al menos un bloque horario")

  // Verifica si esta sección choca con otra
  def chocaCon(otra: Seccion): Boolean =
    bloques.exists(b => otra.bloques.exists(b.seSolapaCon))

  // Devuelve los bloques que chocan con otra sección (para explicar el conflicto)
  def bloquesEnConflictoCon(otra: Seccion): List[(BloqueHorario, BloqueHorario)] =
    for {
      b1 <- bloques
      b2 <- otra.bloques
      if b1.seSolapaCon(b2)
    } yield (b1, b2)

  // Convierte la sección a hechos Prolog
  def toPrologHechos(nombreCurso: String): List[String] = {
    val cursoId  = nombreCurso.toLowerCase.replaceAll("\\s+", "_")
    val seccionId = codigo

    val hechoCurso   = s"seccion('$seccionId', '$cursoId', '$docente')."
    val hechoBloques = bloques.map { b =>
      s"horario('$seccionId', ${b.dia.toLowerCase}, ${b.horaInicio}, ${b.horaFin})."
    }

    hechoCurso :: hechoBloques
  }

  override def toString: String =
    s"Sección $codigo | $docente | ${bloques.mkString(", ")}"
}