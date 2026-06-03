package unihorario

import unihorario.servicios.{CargadorJSON, ExportadorProlog, GuardadorJSON}

object Main {

  val RUTA_JSON:  String = "data/cursos_ingresados.json"
  val RUTA_PROLOG: String = "prolog/hechos.pl"

  def main(args: Array[String]): Unit = {
    println("=========================================")
    println("   UniHorario — Sistema de Planificación ")
    println("=========================================")

    // Determina qué acción ejecutar según el argumento recibido
    val accion = if (args.nonEmpty) args(0) else "exportar"

    accion match {
      case "exportar" => exportarAProlog()
      case "verificar" => verificarDatos()
      case _ =>
        println(s"Acción desconocida: '$accion'")
        println("Acciones disponibles: exportar, verificar")
        System.exit(1)
    }
  }

  // Lee el JSON y genera hechos.pl para Prolog
  private def exportarAProlog(): Unit = {
    println("\n[1/2] Cargando cursos desde JSON...")
    val cursos = CargadorJSON.cargarOVacio(RUTA_JSON)

    if (cursos.isEmpty) {
      println("! No hay cursos registrados. Ingresa cursos desde el menú principal.")
      System.exit(0)
    }

    println(s"\n[2/2] Exportando ${cursos.size} curso(s) a Prolog...")
    val exito = ExportadorProlog.exportar(cursos, RUTA_PROLOG)

    if (exito) {
      println("\n✓ Listo. Prolog puede procesar los horarios.")
      System.exit(0)
    } else {
      println("\n✗ Error al exportar. Revisa los datos.")
      System.exit(1)
    }
  }

  // Solo verifica que el JSON sea válido y muestra un resumen
  private def verificarDatos(): Unit = {
    println("\nVerificando datos guardados...")
    CargadorJSON.cargar(RUTA_JSON) match {
      case Right(cursos) =>
        println(s"✓ Datos válidos")
        println(s"  Cursos    : ${cursos.size}")
        println(s"  Secciones : ${cursos.flatMap(_.secciones).size}")
        println(s"  Bloques   : ${cursos.flatMap(_.secciones).flatMap(_.bloques).size}")
        cursos.foreach { c =>
          println(s"\n  ${c.nombre}")
          c.secciones.foreach { s =>
            println(s"    Sección ${s.codigo} | ${s.docente}")
            s.bloques.foreach(b => println(s"      $b"))
          }
        }
      case Left(error) =>
        println(s"✗ $error")
        System.exit(1)
    }
  }
}