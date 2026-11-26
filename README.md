# MusicFy

Reproductor musical de escritorio desarrollado con **Python + PyQt6**. Su diseño toma como referencia el lenguaje visual AURORA de N3mesis Launcher: fondo azul noche, paneles oscuros, acentos azul lavanda y superficies limpias.

## Primera versión

- Biblioteca local indexada en SQLite.
- Importación de canciones sueltas o carpetas completas.
- Metadatos básicos con Mutagen.
- Reproducción, pausa, anterior/siguiente, posición y volumen con Qt Multimedia.
- Búsqueda dentro de la biblioteca, favoritos e historial.
- Reproducción online de URLs compatibles mediante yt-dlp (sin descarga local).

## Requisitos

- Python 3.10 o posterior.
- PyQt6 con Qt Multimedia.
- Mutagen.
- yt-dlp para la función online.

## Instalación

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Linux / macOS:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

## Uso

1. Abre **Añadir canciones** o **Añadir carpeta** para importar tu música.
2. Selecciona una fila y haz doble clic para reproducirla.
3. Usa el menú contextual para marcar favoritos o retirar entradas de la biblioteca.
4. Pulsa **URL online** para abrir un recurso compatible. La fuente debe permitir expresamente su reproducción externa y debes tener derecho a acceder al contenido.

## Uso responsable de fuentes online

MusicFy no elimina DRM, no evita controles de acceso y no debe utilizarse para copiar o reproducir contenido sin autorización. Utiliza URLs de material propio, de dominio público, con licencias compatibles o para el que tengas permiso. Respeta siempre las condiciones de la plataforma y los derechos de los titulares.

La reproducción de formatos y URLs depende de los códecs y backends multimedia disponibles en el sistema. Algunas fuentes online pueden no ser compatibles con Qt Multimedia.

## Estructura

```
main.py
musicfy/
  __init__.py
  app.py
  database.py
  library.py
  online.py
  styles.qss
requirements.txt
```

## Próximas mejoras

- Portadas y extracción de carátulas.
- Listas de reproducción editables.
- Descargas únicamente desde fuentes con permiso explícito y licencias verificables.
- Ecualizador, letras y visualizador.
- Empaquetado para Windows y Linux.
