# N3mesisFy

Reproductor musical de escritorio para Windows y Linux, desarrollado con **Python + PyQt6**. Su identidad visual parte de N3mesis Launcher: superficies oscuras, bordes finos e iluminación cian.

## Versión 0.6.0

### Biblioteca
- Biblioteca local con canciones, álbumes, artistas, géneros, favoritos e historial.
- Metadatos y carátulas incrustadas mediante Mutagen.
- Caché de portadas en `~/.musicfy/covers`.
- Búsqueda con retardo breve para no reconstruir la vista en cada pulsación.
- Inicio orientado a escuchar: álbum destacado con reproducción directa, carrusel de escuchado recientemente, álbumes de la biblioteca y playlists.
- Botón de reproducción al pasar el cursor por las carátulas.
- Vistas dinámicas de añadidos recientemente y más reproducidas, basadas en la actividad local.
- Importación de archivos y carpetas mediante un hilo de trabajo; el análisis no bloquea la interfaz.
- Inserción de la biblioteca en lotes SQLite y actualización de tabla con repintado suspendido.

### Reproductor
- Pantalla de reproducción ampliada con portada, metadatos, controles, barra de progreso y pestaña de letras incrustadas.
- Visualizador espectral en tiempo real a partir de buffers PCM decodificados (requiere Qt 6.8+ y backend FFmpeg).
- Cola reordenable mediante arrastrar y soltar, con opción para retirar pistas de la cola.
- Reproducción local con Qt Multimedia.
- Anterior, siguiente, reproducir y pausar.
- Barra de progreso y volumen.
- Aleatorio sin repetir pistas hasta completar una vuelta de la cola.
- Repetición desactivada / repetir cola / repetir una pista.
- Temporizador de apagado configurable.
- ReplayGain para ajustar el volumen según la etiqueta de ganancia incluida en cada archivo.
- Atajos de teclado: Espacio (reproducir/pausar), Ctrl+F (buscar), Ctrl+O (importar música), Ctrl+L (reproductor ampliado), Ctrl+J (cola) y Ctrl+Shift+S (temporizador).
- Vista de la cola de reproducción.
- Carátula y metadatos de la pista actual.
- Las letras se leen desde etiquetas incrustadas en archivos compatibles; no se descargan letras desde servicios externos.

El ecualizador gráfico de 10 bandas y el crossfade real siguen pendientes. Qt Multimedia no ofrece esos efectos integrados en QMediaPlayer; requieren una etapa DSP o un motor de audio con mezcla de señales. ReplayGain no sustituye a un ecualizador.

### Playlists M3U
- Crear y eliminar playlists desde la aplicación.
- Importar archivos `.m3u` y `.m3u8`.
- Exportar playlists en formato M3U8 UTF-8.
- Conserva el orden, título, artista y duración EXTINF.
- Resuelve rutas relativas respecto al archivo M3U.
- Mantiene entradas a archivos locales que no estén disponibles en ese momento.
- Las URLs de streaming se omiten en el importador local actual.

Las canciones añadidas desde una playlist se vinculan a la biblioteca cuando existen localmente; sus metadatos se leen en segundo plano.

## Requisitos
- Python 3.10 o posterior.
- PyQt6 6.8 o posterior con Qt Multimedia.
- Mutagen.
- yt-dlp para resolver las URLs online compatibles.

## Instalación en Windows

```powershell
git clone https://github.com/Ocelote9547/MusicFy.git
cd MusicFy
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Para actualizar una copia ya clonada (incluida la dependencia Qt 6.8+ del visualizador):

```powershell
git pull origin main
python -m pip install -r requirements.txt --upgrade
python main.py
```

## Linux

```bash
git clone https://github.com/Ocelote9547/MusicFy.git
cd MusicFy
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

## Atajos de teclado
- `Espacio`: reproducir / pausar (excepto cuando el foco está en un campo de texto).
- `Ctrl+F`: enfocar búsqueda.
- `Ctrl+O`: importar archivos de audio.
- `Ctrl+L`: abrir reproducción ampliada.
- `Ctrl+J`: mostrar cola.
- `Ctrl+Shift+S`: configurar temporizador de apagado.

## Módulos principales
- `musicfy/app.py`: ventana, biblioteca, navegación y conexiones del reproductor.
- `musicfy/player_widgets.py`: visualizador espectral PCM y pantalla de reproducción ampliada.
- `musicfy/playlists.py`: importación y exportación M3U/M3U8.
- `musicfy/library.py`: lectura de metadatos y escaneo en segundo plano.

## Datos locales
La base de datos se almacena en `~/.musicfy/library.sqlite3`. Las carátulas en caché se guardan en `~/.musicfy/covers`. Las playlists se conservan en SQLite; los archivos M3U importados y exportados siguen siendo archivos independientes.

## Uso responsable de fuentes online
Utiliza únicamente contenido propio, de dominio público, con licencia compatible o para el que tengas permiso, y cuando la fuente permita expresamente la reproducción externa. N3mesisFy no elimina DRM ni descarga automáticamente audio protegido.

## Comprobaciones

```bash
python -m compileall -q main.py musicfy tests
python -m unittest discover -s tests -v
```
