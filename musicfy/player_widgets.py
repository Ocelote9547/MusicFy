from __future__ import annotations

import math
import struct
from typing import Any

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QScrollArea,
    QStackedWidget,
    QFrame,
    QVBoxLayout,
    QWidget,
)


def audio_buffer_levels(buffer: Any, band_count: int = 24) -> list[float]:
    """Return a lightweight logarithmic spectrum from a Qt decoded audio buffer."""
    if not buffer or not buffer.isValid():
        return [0.0] * band_count

    audio_format = buffer.format()
    frames = int(buffer.frameCount())
    channels = max(1, int(audio_format.channelCount()))
    if frames < 32 or audio_format.sampleRate() <= 0:
        return [0.0] * band_count

    byte_count = int(buffer.byteCount())
    try:
        payload = buffer.constData()
    except (AttributeError, TypeError):
        try:
            payload = buffer.data()
        except (AttributeError, TypeError):
            return [0.0] * band_count
    try:
        if hasattr(payload, "asstring"):
            raw = payload.asstring(byte_count)
        else:
            raw = bytes(payload)
    except (TypeError, ValueError, BufferError):
        return [0.0] * band_count
    if len(raw) < byte_count:
        return [0.0] * band_count
    sample_format = audio_format.sampleFormat()
    format_name = getattr(sample_format, "name", str(sample_format)).lower()

    try:
        if "float" in format_name:
            samples = struct.unpack("<" + "f" * (len(raw) // 4), raw[: len(raw) // 4 * 4])
            scale = 1.0
        elif "int16" in format_name:
            samples = struct.unpack("<" + "h" * (len(raw) // 2), raw[: len(raw) // 2 * 2])
            scale = 32768.0
        elif "int32" in format_name:
            samples = struct.unpack("<" + "i" * (len(raw) // 4), raw[: len(raw) // 4 * 4])
            scale = 2147483648.0
        elif "uint8" in format_name:
            samples = tuple(value - 128 for value in raw)
            scale = 128.0
        else:
            return [0.0] * band_count
    except (ValueError, struct.error):
        return [0.0] * band_count

    available_frames = min(frames, len(samples) // channels)
    if available_frames < 32:
        return [0.0] * band_count

    # Decimate to at most 1024 mono samples before the spectrum calculation.
    hop = max(1, available_frames // 1024)
    mono: list[float] = []
    for frame in range(0, available_frames, hop):
        offset = frame * channels
        value = sum(samples[offset : offset + channels]) / channels / scale
        mono.append(max(-1.0, min(1.0, float(value))))
    if len(mono) > 1024:
        mono = mono[:1024]

    count = len(mono)
    sample_rate = float(audio_format.sampleRate())
    effective_sample_rate = sample_rate / hop
    max_frequency = min(16000.0, effective_sample_rate * 0.46)
    min_frequency = min(45.0, max_frequency / 3.0)
    if max_frequency <= min_frequency:
        return [0.0] * band_count

    # Goertzel bins on logarithmically spaced centre frequencies.
    levels: list[float] = []
    for band in range(band_count):
        ratio = (band + 0.5) / band_count
        frequency = min_frequency * ((max_frequency / min_frequency) ** ratio)
        omega = 2.0 * math.pi * frequency * hop / sample_rate
        coefficient = 2.0 * math.cos(omega)
        previous = 0.0
        previous_previous = 0.0
        for sample in mono:
            current = sample + coefficient * previous - previous_previous
            previous_previous = previous
            previous = current
        magnitude_squared = (
            previous * previous
            + previous_previous * previous_previous
            - coefficient * previous * previous_previous
        )
        magnitude = math.sqrt(max(0.0, magnitude_squared)) * 2.0 / count
        levels.append(min(1.0, (magnitude * 3.4) ** 0.72))
    return levels


class SpectrumWidget(QWidget):
    """Low-cost spectrum display fed by decoded PCM from QAudioBufferOutput."""

    def __init__(self, parent: QWidget | None = None, bars: int = 24) -> None:
        super().__init__(parent)
        self.setMinimumHeight(32)
        self.setMinimumWidth(100)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self._levels = [0.035] * bars
        self._playing = False
        self._timer = QTimer(self)
        self._timer.setInterval(34)
        self._timer.timeout.connect(self._decay)
        self._timer.start()

    def set_levels(self, levels: list[float]) -> None:
        if not levels:
            return
        count = len(self._levels)
        if len(levels) == count:
            self._levels = [max(0.025, min(1.0, float(value))) for value in levels]
        else:
            self._levels = [
                max(0.025, min(1.0, float(levels[min(len(levels) - 1, int(i * len(levels) / count))])))
                for i in range(count)
            ]
        self.update()

    def set_playing(self, playing: bool) -> None:
        self._playing = bool(playing)
        if not self._playing:
            self._levels = [max(0.025, value * 0.88) for value in self._levels]
        self.update()

    def _decay(self) -> None:
        if not self._playing:
            self._levels = [max(0.025, value * 0.91) for value in self._levels]
            self.update()

    def paintEvent(self, event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#0b1118"))
        width = self.width()
        height = self.height()
        count = len(self._levels)
        gap = max(2.0, width * 0.008)
        bar_width = max(2.0, (width - gap * (count - 1)) / count)
        baseline = height - 5.0

        for index, level in enumerate(self._levels):
            bar_height = max(3.0, level * (height - 12.0))
            x = index * (bar_width + gap)
            y = baseline - bar_height
            gradient = QLinearGradient(x, y, x, baseline)
            gradient.setColorAt(0.0, QColor("#8be8ff"))
            gradient.setColorAt(0.55, QColor("#12b5e9"))
            gradient.setColorAt(1.0, QColor("#17658b"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(gradient)
            painter.drawRoundedRect(
                QRectF(x, y, bar_width, bar_height),
                bar_width / 2,
                bar_width / 2,
            )
        painter.end()


class NowPlayingDialog(QDialog):
    previousRequested = pyqtSignal()
    playPauseRequested = pyqtSignal()
    nextRequested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Reproduciendo · N3mesisFy")
        self.setObjectName("nowPlayingDialog")
        self.resize(940, 700)
        self.setMinimumSize(760, 580)

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(18)

        top = QHBoxLayout()
        brand = QLabel("N3MESISFY  /  NOW PLAYING")
        brand.setObjectName("eyebrow")
        top.addWidget(brand)
        top.addStretch(1)
        self.artwork_tab = QPushButton("REPRODUCCIÓN")
        self.artwork_tab.setObjectName("playerTab")
        self.artwork_tab.setCheckable(True)
        self.artwork_tab.setChecked(True)
        self.artwork_tab.clicked.connect(lambda: self.content_stack.setCurrentIndex(0))
        top.addWidget(self.artwork_tab)
        self.lyrics_tab = QPushButton("LETRAS")
        self.lyrics_tab.setObjectName("playerTab")
        self.lyrics_tab.setCheckable(True)
        self.lyrics_tab.clicked.connect(lambda: self.content_stack.setCurrentIndex(1))
        top.addWidget(self.lyrics_tab)
        close_button = QPushButton("Cerrar")
        close_button.setObjectName("secondaryButton")
        close_button.clicked.connect(self.close)
        top.addWidget(close_button)
        root.addLayout(top)

        content = QHBoxLayout()
        content.setSpacing(30)

        self.cover = QLabel()
        self.cover.setObjectName("nowPlayingCover")
        self.cover.setFixedSize(330, 330)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content.addWidget(self.cover, 0, Qt.AlignmentFlag.AlignVCenter)

        detail = QVBoxLayout()
        detail.setSpacing(10)
        kicker = QLabel("SONANDO AHORA")
        kicker.setObjectName("heroKicker")
        detail.addWidget(kicker)
        self.title_label = QLabel("Selecciona una canción")
        self.title_label.setObjectName("nowPlayingTitle")
        self.title_label.setWordWrap(True)
        detail.addWidget(self.title_label)
        self.artist_label = QLabel("Tu música aparecerá aquí")
        self.artist_label.setObjectName("nowPlayingArtist")
        self.artist_label.setWordWrap(True)
        detail.addWidget(self.artist_label)
        detail.addStretch(1)
        content.addLayout(detail, 1)

        artwork_page = QWidget()
        artwork_page_layout = QHBoxLayout(artwork_page)
        artwork_page_layout.setContentsMargins(0, 0, 0, 0)
        artwork_page_layout.addLayout(content)

        lyrics_page = QWidget()
        lyrics_page_layout = QVBoxLayout(lyrics_page)
        lyrics_page_layout.setContentsMargins(18, 12, 18, 12)
        lyrics_page_layout.setSpacing(10)
        lyrics_heading = QLabel("LETRAS DE LA CANCIÓN")
        lyrics_heading.setObjectName("eyebrow")
        lyrics_page_layout.addWidget(lyrics_heading)
        lyrics_scroll = QScrollArea()
        lyrics_scroll.setWidgetResizable(True)
        lyrics_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.lyrics_label = QLabel(
            "Las letras incrustadas en el archivo aparecerán aquí."
        )
        self.lyrics_label.setObjectName("lyricsText")
        self.lyrics_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.lyrics_label.setWordWrap(True)
        self.lyrics_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lyrics_scroll.setWidget(self.lyrics_label)
        lyrics_page_layout.addWidget(lyrics_scroll, 1)

        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(artwork_page)
        self.content_stack.addWidget(lyrics_page)
        self.content_stack.currentChanged.connect(self._update_tabs)
        root.addWidget(self.content_stack, 1)

        section_header = QHBoxLayout()
        section_title = QLabel("ESPECTRO EN TIEMPO REAL")
        section_title.setObjectName("eyebrow")
        section_header.addWidget(section_title)
        section_header.addStretch(1)
        self.visualizer_state = QLabel("Esperando audio")
        self.visualizer_state.setObjectName("muted")
        section_header.addWidget(self.visualizer_state)
        root.addLayout(section_header)

        self.visualizer = SpectrumWidget(bars=36)
        self.visualizer.setMinimumHeight(118)
        root.addWidget(self.visualizer)

        progress = QHBoxLayout()
        self.position_label = QLabel("0:00")
        self.position_label.setObjectName("timeLabel")
        progress.addWidget(self.position_label)
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setObjectName("positionSlider")
        self.position_slider.setRange(0, 0)
        progress.addWidget(self.position_slider, 1)
        self.duration_label = QLabel("0:00")
        self.duration_label.setObjectName("timeLabel")
        progress.addWidget(self.duration_label)
        root.addLayout(progress)

        controls = QHBoxLayout()
        controls.addStretch(1)
        self.previous_button = QPushButton("Anterior")
        self.previous_button.setObjectName("secondaryButton")
        self.previous_button.clicked.connect(self.previousRequested.emit)
        controls.addWidget(self.previous_button)
        self.play_button = QPushButton("Reproducir / Pausar")
        self.play_button.setObjectName("primaryButton")
        self.play_button.clicked.connect(self.playPauseRequested.emit)
        controls.addWidget(self.play_button)
        self.next_button = QPushButton("Siguiente")
        self.next_button.setObjectName("secondaryButton")
        self.next_button.clicked.connect(self.nextRequested.emit)
        controls.addWidget(self.next_button)
        controls.addStretch(1)
        root.addLayout(controls)

    def set_track(
        self,
        title: str,
        artist: str,
        cover: QPixmap,
        lyrics: str = "",
    ) -> None:
        self.title_label.setText(title)
        self.artist_label.setText(artist)
        self.set_lyrics(lyrics)
        self.cover.setPixmap(
            cover.scaled(
                330,
                330,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def set_lyrics(self, lyrics: str) -> None:
        clean_lyrics = str(lyrics or "").strip()
        if clean_lyrics:
            self.lyrics_label.setText(clean_lyrics)
        else:
            self.lyrics_label.setText(
                "Este archivo no contiene letras incrustadas.\n\n"
                "Puedes añadirlas a los metadatos del archivo para verlas aquí."
            )

    def _update_tabs(self, index: int) -> None:
        self.artwork_tab.setChecked(index == 0)
        self.lyrics_tab.setChecked(index == 1)

    def set_levels(self, levels: list[float]) -> None:
        self.visualizer.set_levels(levels)
        self.visualizer_state.setText("Audio detectado")

    def set_playing(self, playing: bool) -> None:
        self.visualizer.set_playing(playing)
        self.play_button.setText("Pausar" if playing else "Reproducir")

    def update_position(self, position: int) -> None:
        if not self.position_slider.isSliderDown():
            self.position_slider.setValue(position)
        self.position_label.setText(self._format_time(position))

    def update_duration(self, duration: int) -> None:
        self.position_slider.setRange(0, max(0, duration))
        self.duration_label.setText(self._format_time(duration))

    @staticmethod
    def _format_time(milliseconds: int) -> str:
        seconds = max(0, int(milliseconds / 1000))
        return f"{seconds // 60}:{seconds % 60:02d}"
