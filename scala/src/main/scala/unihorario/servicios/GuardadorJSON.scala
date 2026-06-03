package unihorario.servicios

import unihorario.modelos.{BloqueHorario, Curso, Seccion}
import io.circe._
import io.circe.syntax._
import io.circe.generic.semiauto._

import java.io.{File, PrintWriter}
import scala.util.{Try, Using}

object GuardadorJSON {

  // Encoders: convierten los modelos a JSON
  implicit val encoderBloque:  Encoder[BloqueHorario] = deriveEncoder
  implicit val encoderSeccion: Encoder[Seccion]        = deriveEncoder
  implicit val encoderCurso:   Encoder[Curso]          = deriveEncoder

  def guardar(cursos: List[Curso], ruta: String = "data/cursos_ingresados.json"): Boolean = {
    val json = cursos.asJson.spaces2
    Try {
      val archivo = new File(ruta)
      archivo.getParentFile.mkdirs()
      Using(new PrintWriter(archivo)) { writer =>
        writer.write(json)
      }
    }.isSuccess
  }

  def confirmarGuardado(cursos: List[Curso], ruta: String = "data/cursos_ingresados.json"): Unit = {
    if (guardar(cursos, ruta)) {
      println(s"✓ Datos guardados correctamente en $ruta")
      println(s"  ${cursos.size} curso(s) registrado(s)")
    } else {
      println(s"✗ Error al guardar los datos en $ruta")
    }
  }
}