ThisBuild / version      := "1.0.0"
ThisBuild / scalaVersion := "2.13.12"
ThisBuild / organization := "unihorario"

lazy val root = (project in file("."))
  .settings(
    name := "unihorario",

    libraryDependencies ++= Seq(
      // Lectura y escritura de JSON (para exportar a Python y Prolog)
      "io.circe" %% "circe-core"    % "0.14.6",
      "io.circe" %% "circe-generic" % "0.14.6",
      "io.circe" %% "circe-parser"  % "0.14.6",

      // Lectura de archivos CSV
      "com.github.tototoshi" %% "scala-csv" % "1.3.10",

      // Tests
      "org.scalatest" %% "scalatest" % "3.2.17" % Test
    ),

    // Punto de entrada del programa
    Compile / mainClass := Some("unihorario.Main"),

    // Empaquetar todo en un solo JAR ejecutable (para que Python lo invoque)
    assembly / assemblyJarName := "unihorario.jar",
    assembly / assemblyMergeStrategy := {
      case PathList("META-INF", _*) => MergeStrategy.discard
      case _                        => MergeStrategy.first
    }
  )
