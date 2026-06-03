package unihorario.servicios

import unihorario.modelos.Curso

import java.io.{File, PrintWriter}
import scala.util.Using

object ExportadorProlog {

  def exportar(cursos: List[Curso], ruta: String = "prolog/hechos.pl"): Boolean = {
    if (cursos.isEmpty) {
      println("! No hay cursos para exportar a Prolog")
      return false
    }

    val lineas = construirHechos(cursos)

    try {
      val archivo = new File(ruta)
      archivo.getParentFile.mkdirs()
      Using(new PrintWriter(archivo)) { writer =>
        writer.println(s"% hechos.pl — generado automáticamente por UniHorario")
        writer.println(s"% Cursos: ${cursos.size}")
        writer.println(s"% Secciones: ${cursos.flatMap(_.secciones).size}")
        writer.println()
        lineas.foreach(writer.println)
      }
      println(s"✓ hechos.pl generado en $ruta")
      println(s"  ${cursos.size} curso(s) | ${cursos.flatMap(_.secciones).size} sección(es)")
      true
    } catch {
      case e: Exception =>
        println(s"✗ Error al generar hechos.pl: ${e.getMessage}")
        false
    }
  }

  private def construirHechos(cursos: List[Curso]): List[String] = {
    val hechos = scala.collection.mutable.ListBuffer.empty[String]

    // Hechos de cursos
    hechos += "% --- Cursos ---"
    cursos.foreach { curso =>
      val cursoId = curso.nombre.toLowerCase.replaceAll("\\s+", "_")
      hechos += s"curso('$cursoId', '${curso.nombre}')."
    }

    hechos += ""

    // Hechos de secciones y horarios
    hechos += "% --- Secciones y horarios ---"
    cursos.foreach { curso =>
      val cursoId = curso.nombre.toLowerCase.replaceAll("\\s+", "_")
      curso.secciones.foreach { seccion =>
        hechos += s"seccion('${seccion.codigo}', '$cursoId', '${seccion.docente}')."
        seccion.bloques.foreach { bloque =>
          val inicioMin = bloque.horaInicio.replace(":", "")
val finMin    = bloque.horaFin.replace(":", "")
          hechos += s"horario('${seccion.codigo}', ${bloque.dia.toLowerCase}, $inicioMin, $finMin)."
        }
      }
      hechos += ""
    }

    hechos.toList
  }
}