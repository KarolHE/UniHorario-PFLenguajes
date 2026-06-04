import sys
import os

# Asegura que Python encuentre los módulos desde src/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.consola import UniHorarioApp, aplicar_estilos

def main():
    app = UniHorarioApp()
    aplicar_estilos()
    app.mainloop()

if __name__ == "__main__":
    main()