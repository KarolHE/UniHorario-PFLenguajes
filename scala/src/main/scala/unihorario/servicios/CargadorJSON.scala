package unihorario.servicios

import unihorario.modelos.{BloqueHorario, Curso, Seccion}
import io.circe._
import io.circe.parser._
import io.circe.generic.semiauto._

import scala.io.Source
import scala.util.{Try, Using}

object CargadorJSON {

  // ── Decoder manual de BloqueHorario (Fix Avance 2) ──────────────
  // Python (consola.py) guarda los campos como "inicio" / "fin",
  // mientras que el modelo Scala internamente usa horaInicio/horaFin.
  // Este decoder acepta AMBOS formatos para no romper compatibilidad,
  // probando primero "inicio"/"fin" (formato real de Python) y luego
  // "horaInicio"/"horaFin" como respaldo.
  implicit val decoderBloque: Decoder[BloqueHorario] = Decoder.instance { c =>
    for {
      dia        <- c.downField("dia").as[String]
      horaInicio <- c.downField("inicio").as[String]
                      .orElse(c.downField("horaInicio").as[String])
      horaFin    <- c.downField("fin").as[String]
                      .orElse(c.downField("horaFin").as[String])
    } yield BloqueHorario(dia, horaInicio, horaFin)
  }

  implicit val decoderSeccion: Decoder[Seccion] = deriveDecoder
  implicit val decoderCurso:   Decoder[Curso]   = deriveDecoder

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