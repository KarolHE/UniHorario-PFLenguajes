package unihorario.servicios

import unihorario.modelos.{BloqueHorario, Curso, Seccion}
import io.circe._
import io.circe.parser._
import io.circe.generic.semiauto._

import scala.io.Source
import scala.util.{Try, Using}

object CargadorJSON {

  // Decoders: convierten JSON de vuelta a modelos
  implicit val decoderBloque:  Decoder[BloqueHorario] = deriveDecoder
  implicit val decoderSeccion: Decoder[Seccion]        = deriveDecoder
  implicit val decoderCurso:   Decoder[Curso]          = deriveDecoder

  def cargar(ruta: String = "data/cursos_ingresados.json"): Either[String, List[Curso]] = {
    val contenido = Using(Source.fromFile(ruta))(_.mkString)

    contenido match {
      case scala.util.Failure(_) =>
        Left(s"No se pudo leer el archivo: $ruta")
      case scala.util.Success(json) =>
        decode[List[Curso]](json) match {
          case Left(error) => Left(s"Error al parsear el JSON: ${error.getMessage}")
          case Right(cursos) => Right(cursos)
        }
    }
  }

  def cargarOVacio(ruta: String = "data/cursos_ingresados.json"): List[Curso] =
    cargar(ruta) match {
      case Right(cursos) =>
        println(s"✓ ${cursos.size} curso(s) cargado(s) desde $ruta")
        cursos
      case Left(error) =>
        println(s"! Iniciando con lista vacía. ($error)")
        List.empty
    }
}