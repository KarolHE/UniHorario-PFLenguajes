package unihorario.modelos

case class Curso(
  nombre: String,
  secciones: List[Seccion] = List.empty
) {
  require(nombre.nonEmpty, "El nombre del curso no puede estar vacío")

  def agregarSeccion(seccion: Seccion): Curso =
    this.copy(secciones = secciones :+ seccion)

  def tieneSecciones: Boolean = secciones.nonEmpty

  def buscarSeccion(codigo: String): Option[Seccion] =
    secciones.find(_.codigo == codigo)

  override def toString: String =
    s"$nombre (${secciones.size} sección(es))"
}