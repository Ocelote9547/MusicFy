# N3mesisFy

Reproductor musical de escritorio desarrollado con **Python + PyQt6**, siguiendo la identidad visual AURORA de N3mesis Launcher.

## Interfaz AURORA (0.4.0)

- Tema inspirado en N3mesis Launcher: negro grafito, paneles oscuros, bordes finos y acento cian.
- Navegación horizontal superior en cápsula, inspirada en la estructura de N3mesis Launcher.\n- Iconografía vectorial pintada con Qt, consistente y sin depender de emojis ni de fuentes de símbolos instaladas en Windows.
- Controles de navegación, importación y reproducción con iconos vectoriales.
- Botón de reproducción, pausa, anterior y siguiente con iconos escalables.

- Inicio editorial con ilustración N3mesisFy, métricas compactas, carrusel horizontal de álbumes y un estado vacío con acciones directas.
- Vistas de canciones, álbumes, artistas y géneros.
- Fichas visuales de álbumes con sus carátulas.\n- Navegación rediseñada y superficies transparentes para evitar bloques de fondo en etiquetas.
- Extracción de portadas incrustadas en los archivos y búsqueda de imágenes de carpeta (`cover.jpg`, `folder.jpg`, `front.jpg`).
- Caché local de carátulas en `~/.musicfy/covers` para evitar volver a extraerlas en cada arranque.
- Favoritos, historial, búsqueda global, menú contextual y reproducción desde las fichas.
- Migración automática de SQLite para conservar las bibliotecas creadas con versiones anteriores.

## Reproducción y formatos

- Reproducción local con Qt Multimedia.
- Metadatos de audio mediante Mutagen.
- Importación de archivos sueltos o carpetas completas.
- Reproducción online de URLs compatibles mediante yt-dlp (sin descarga local).

La compatibilidad final de MP3, FLAC, WAV, OGG, Opus, M4A, AAC, AIFF y WMA depende de los códecs y backends multimedia instalados en el sistema.

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

1. Abre **Añadir música** o **Añadir carpeta** para importar archivos.
2. En **Álbumes**, selecciona una portada para ver sus canciones.
3. En **Artistas** y **Géneros**, abre una ficha para filtrar la colección.
4. Haz doble clic en una canción para reproducirla.
5. Usa el menú contextual para añadir o quitar favoritos, o retirar una pista de N3mesisFy. El archivo original nunca se borra.

La base de datos se guarda en `~/.musicfy/library.sqlite3`. Las carátulas extraídas se guardan en `~/.musicfy/covers`. Los archivos de audio originales no se modifican.

## Uso responsable de fuentes online

N3mesisFy no elimina DRM, no evita controles de acceso y no debe utilizarse para copiar o reproducir contenido sin autorización. Utiliza URLs de material propio, de dominio público, con licencias compatibles o para el que tengas permiso. Respeta siempre las condiciones de la plataforma y los derechos de los titulares.

Algunas fuentes online pueden no ofrecer un flujo reproducible en Qt Multimedia.

## Estructura

```
main.py
requirements.txt
musicfy/
  __init__.py
  app.py
  database.py
  library.py
  online.py
  styles.qss
tests/
  test_database.py
```

## Comprobaciones

```bash
python -m compileall -q main.py musicfy
python -m unittest discover -s tests -v
```
