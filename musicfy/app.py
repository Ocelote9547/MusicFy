from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QAction
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from musicfy.database import MusicDatabase
from musicfy.library import read_audio_file, scan_folder
from musicfy.online import OnlineResolver


class MusicFyWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MusicFy")
        self.resize(1280, 820)
        self.setMinimumSize(980, 650)

        self.database = MusicDatabase()
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(0.72)
        self.player.setAudioOutput(self.audio_output)

        self.filter_mode = "all"
        self.visible_tracks: list[dict[str, Any]] = []
        self.queue: list[dict[str, Any]] = []
        self.current_track: dict[str, Any] | None = None
        self.current_index = -1
        self.online_resolver: OnlineResolver | None = None

        self._build_ui()
        self._connect_player()
        self._load_styles()
        self.load_library()

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(15)

        # Left navigation rail
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(205)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(16, 22, 16, 18)
        side_layout.setSpacing(8)

        brand = QLabel("MusicFy")
        brand.setObjectName("brand")
        side_layout.addWidget(brand)

        brand_caption = QLabel("MUSIC FOR EVERY MOMENT")
        brand_caption.setObjectName("eyebrow")
        side_layout.addWidget(brand_caption)
        side_layout.addSpacing(28)

        self.nav_buttons: list[QPushButton] = []
        nav_items = [
            ("⌂", "Inicio", "all"),
            ("♫", "Biblioteca", "all"),
            ("★", "Favoritos", "favorites"),
            ("◷", "Historial", "history"),
        ]
        for symbol, label, mode in nav_items:
            button = QPushButton(f"{symbol}    {label}")
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(partial(self.change_filter, mode, button))
            side_layout.addWidget(button)
            self.nav_buttons.append(button)

        self.nav_buttons[0].setChecked(True)
        side_layout.addStretch(1)

        local_note = QLabel("TU MÚSICA
EN TU EQUIPO")
        local_note.setObjectName("sidebar_note")
        side_layout.addWidget(local_note)

        version = QLabel("MUSICFY  ·  0.1.0")
        version.setObjectName("version")
        side_layout.addWidget(version)

        # Main content
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(6, 4, 4, 0)
        content_layout.setSpacing(15)

        header = QHBoxLayout()
        header_text = QVBoxLayout()
        eyebrow = QLabel("N3MESIS STUDIO  /  MUSIC PLAYER")
        eyebrow.setObjectName("eyebrow")
        header_text.addWidget(eyebrow)

        self.page_title = QLabel("Tu biblioteca musical")
        self.page_title.setObjectName("pageTitle")
        header_text.addWidget(self.page_title)

        self.page_subtitle = QLabel("Toda tu música, organizada en un solo lugar.")
        self.page_subtitle.setObjectName("muted")
        header_text.addWidget(self.page_subtitle)
        header.addLayout(header_text)
        header.addStretch(1)

        self.online_button = QPushButton("↗  URL online")
        self.online_button.setObjectName("secondaryButton")
        self.online_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.online_button.clicked.connect(self.open_online_url)
        header.addWidget(self.online_button)
        content_layout.addLayout(header)

        # Search and import actions
        action_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setObjectName("searchBox")
        self.search_box.setPlaceholderText("⌕   Buscar canción, artista o álbum...")
        self.search_box.textChanged.connect(self.load_library)
        action_row.addWidget(self.search_box, 1)

        add_files_button = QPushButton("+  Añadir canciones")
        add_files_button.setObjectName("primaryButton")
        add_files_button.setCursor(Qt.CursorShape.PointingHandCursor)
        add_files_button.clicked.connect(self.add_audio_files)
        action_row.addWidget(add_files_button)

        add_folder_button = QPushButton("Añadir carpeta")
        add_folder_button.setObjectName("secondaryButton")
        add_folder_button.setCursor(Qt.CursorShape.PointingHandCursor)
        add_folder_button.clicked.connect(self.add_music_folder)
        action_row.addWidget(add_folder_button)
        content_layout.addLayout(action_row)

        # Summary cards
        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)
        self.total_stat = self._make_stat_card("CANCIONES", "0")
        self.favorites_stat = self._make_stat_card("FAVORITOS", "0")
        self.history_stat = self._make_stat_card("REPRODUCIDAS", "0")
        stats_row.addWidget(self.total_stat)
        stats_row.addWidget(self.favorites_stat)
        stats_row.addWidget(self.history_stat)
        content_layout.addLayout(stats_row)

        library_header = QHBoxLayout()
        library_title = QLabel("Tus canciones")
        library_title.setObjectName("sectionTitle")
        library_header.addWidget(library_title)
        library_header.addStretch(1)
        self.result_count = QLabel("0 pistas")
        self.result_count.setObjectName("muted")
        library_header.addWidget(self.result_count)
        content_layout.addLayout(library_header)

        self.table = QTableWidget(0, 5)
        self.table.setObjectName("trackTable")
        self.table.setHorizontalHeaderLabels(["TÍTULO", "ARTISTA", "ÁLBUM", "DURACIÓN", "★"])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_track_menu)
        self.table.cellDoubleClicked.connect(self.play_selected_row)

        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setColumnWidth(4, 42)
        content_layout.addWidget(self.table, 1)

        # Persistent mini-player
        player_bar = QFrame()
        player_bar.setObjectName("playerBar")
        player_layout = QVBoxLayout(player_bar)
        player_layout.setContentsMargins(14, 12, 14, 12)
        player_layout.setSpacing(8)

        progress_row = QHBoxLayout()
        self.position_label = QLabel("0:00")
        self.position_label.setObjectName("timeLabel")
        progress_row.addWidget(self.position_label)
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setObjectName("positionSlider")
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.player.setPosition)
        progress_row.addWidget(self.position_slider, 1)
        self.duration_label = QLabel("0:00")
        self.duration_label.setObjectName("timeLabel")
        progress_row.addWidget(self.duration_label)
        player_layout.addLayout(progress_row)

        controls_row = QHBoxLayout()
        self.cover_placeholder = QLabel("♫")
        self.cover_placeholder.setObjectName("coverPlaceholder")
        self.cover_placeholder.setFixedSize(48, 48)
        controls_row.addWidget(self.cover_placeholder)

        current_text = QVBoxLayout()
        self.now_title = QLabel("Selecciona una canción")
        self.now_title.setObjectName("nowTitle")
        self.now_artist = QLabel("Tu música aparecerá aquí")
        self.now_artist.setObjectName("muted")
        current_text.addWidget(self.now_title)
        current_text.addWidget(self.now_artist)
        controls_row.addLayout(current_text)
        controls_row.addStretch(1)

        self.previous_button = QPushButton("⏮")
        self.previous_button.setObjectName("controlButton")
        self.previous_button.clicked.connect(lambda: self.skip_track(-1))
        controls_row.addWidget(self.previous_button)

        self.play_button = QPushButton("▶")
        self.play_button.setObjectName("playButton")
        self.play_button.setFixedSize(42, 42)
        self.play_button.clicked.connect(self.toggle_playback)
        controls_row.addWidget(self.play_button)

        self.next_button = QPushButton("⏭")
        self.next_button.setObjectName("controlButton")
        self.next_button.clicked.connect(lambda: self.skip_track(1))
        controls_row.addWidget(self.next_button)
        controls_row.addStretch(1)

        volume_label = QLabel("VOL")
        volume_label.setObjectName("eyebrow")
        controls_row.addWidget(volume_label)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setObjectName("volumeSlider")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(72)
        self.volume_slider.setFixedWidth(105)
        self.volume_slider.valueChanged.connect(
            lambda value: self.audio_output.setVolume(value / 100)
        )
        controls_row.addWidget(self.volume_slider)
        player_layout.addLayout(controls_row)
        content_layout.addWidget(player_bar)

        root_layout.addWidget(sidebar)
        root_layout.addWidget(content, 1)
        self.setCentralWidget(root)

        self.statusBar().showMessage("Listo para reproducir música.")

    def _make_stat_card(self, heading: str, value: str) -> QFrame:
        card = QFrame()
        card.setObjectName("statCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(3)
        title = QLabel(heading)
        title.setObjectName("eyebrow")
        number = QLabel(value)
        number.setObjectName("statValue")
        layout.addWidget(title)
        layout.addWidget(number)
        card.value_label = number  # type: ignore[attr-defined]
        return card

    def _load_styles(self) -> None:
        stylesheet = Path(__file__).with_name("styles.qss")
        try:
            self.setStyleSheet(stylesheet.read_text(encoding="utf-8"))
        except OSError:
            self.statusBar().showMessage("No se ha podido cargar styles.qss.")

    def _connect_player(self) -> None:
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)
        self.player.playbackStateChanged.connect(self.update_play_button)
        self.player.mediaStatusChanged.connect(self.handle_media_status)
        self.player.errorOccurred.connect(self.handle_player_error)

    def change_filter(self, mode: str, selected_button: QPushButton) -> None:
        self.filter_mode = mode
        for button in self.nav_buttons:
            button.setChecked(button is selected_button)
        titles = {
            "all": ("Tu biblioteca musical", "Toda tu música, organizada en un solo lugar."),
            "favorites": ("Tus favoritos", "Las canciones que quieres tener siempre a mano."),
            "history": ("Reproducidas recientemente", "Vuelve a escuchar lo que estabas disfrutando."),
        }
        title, subtitle = titles.get(mode, titles["all"])
        self.page_title.setText(title)
        self.page_subtitle.setText(subtitle)
        self.load_library()

    def load_library(self, *_args: Any) -> None:
        tracks = self.database.list_tracks(self.filter_mode)
        query = self.search_box.text().strip().casefold()
        if query:
            tracks = [
                track for track in tracks
                if query in track["title"].casefold()
                or query in track["artist"].casefold()
                or query in track["album"].casefold()
            ]

        self.visible_tracks = tracks
        self.table.setRowCount(0)
        for track in tracks:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                track["title"],
                track["artist"],
                track["album"],
                self.format_time(track["duration"]),
                "★" if track["is_favorite"] else "",
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, track["path"])
                if column in (3, 4):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, column, item)

        self.result_count.setText(f"{len(tracks)} pistas")
        all_tracks = self.database.list_tracks("all")
        fav_tracks = self.database.list_tracks("favorites")
        history_tracks = self.database.list_tracks("history")
        self.total_stat.value_label.setText(str(len(all_tracks)))  # type: ignore[attr-defined]
        self.favorites_stat.value_label.setText(str(len(fav_tracks)))  # type: ignore[attr-defined]
        self.history_stat.value_label.setText(str(len(history_tracks)))  # type: ignore[attr-defined]

    def add_audio_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Añadir canciones",
            str(Path.home()),
            "Archivos de audio (*.mp3 *.flac *.wav *.ogg *.opus *.m4a *.aac *.aiff *.wma)",
        )
        self._import_paths(files)

    def add_music_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta musical", str(Path.home())
        )
        if not folder:
            return
        self.statusBar().showMessage("Analizando carpeta musical…")
        tracks = scan_folder(folder)
        for track in tracks:
            self.database.save_track(track)
        self.load_library()
        self.statusBar().showMessage(f"Se han añadido o actualizado {len(tracks)} canciones.", 6000)

    def _import_paths(self, paths: list[str]) -> None:
        imported = 0
        for path in paths:
            track = read_audio_file(path)
            if track is not None:
                self.database.save_track(track)
                imported += 1
        self.load_library()
        self.statusBar().showMessage(f"Se han añadido o actualizado {imported} canciones.", 6000)

    def play_selected_row(self, row: int, _column: int = 0) -> None:
        if not (0 <= row < len(self.visible_tracks)):
            return
        self.queue = list(self.visible_tracks)
        self.current_index = row
        self.play_track(self.queue[row])

    def play_track(self, track: dict[str, Any]) -> None:
        self.current_track = track
        title = str(track.get("title") or "Reproducción")
        artist = str(track.get("artist") or "Artista desconocido")
        self.now_title.setText(title)
        self.now_artist.setText(artist)
        self.now_title.setToolTip(title)
        self.now_artist.setToolTip(artist)
        self.position_slider.setValue(0)
        self.position_label.setText("0:00")
        self.duration_label.setText(self.format_time(track.get("duration", 0)))

        if track.get("url"):
            source = QUrl(str(track["url"]))
        else:
            source = QUrl.fromLocalFile(str(track["path"]))
            self.database.mark_played(str(track["path"]))
            self.load_library()

        self.player.setSource(source)
        self.player.play()
        self.statusBar().showMessage(f"Reproduciendo: {title}", 5000)

    def toggle_playback(self) -> None:
        state = self.player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        elif self.current_track is not None:
            self.player.play()
        else:
            row = self.table.currentRow()
            if row >= 0:
                self.play_selected_row(row)

    def skip_track(self, offset: int) -> None:
        if not self.queue:
            if self.visible_tracks:
                self.queue = list(self.visible_tracks)
                self.current_index = 0 if offset > 0 else len(self.queue) - 1
            else:
                return
        else:
            self.current_index = (self.current_index + offset) % len(self.queue)
        self.play_track(self.queue[self.current_index])

    def handle_media_status(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia and self.queue:
            self.skip_track(1)

    def update_play_button(self, state: QMediaPlayer.PlaybackState) -> None:
        self.play_button.setText(
            "Ⅱ" if state == QMediaPlayer.PlaybackState.PlayingState else "▶"
        )

    def update_position(self, position: int) -> None:
        if not self.position_slider.isSliderDown():
            self.position_slider.setValue(position)
        self.position_label.setText(self.format_time(position / 1000))

    def update_duration(self, duration: int) -> None:
        self.position_slider.setRange(0, max(0, duration))
        self.duration_label.setText(self.format_time(duration / 1000))

    @staticmethod
    def format_time(seconds: float | int | None) -> str:
        total = max(0, int(seconds or 0))
        minutes, remaining = divmod(total, 60)
        return f"{minutes}:{remaining:02d}"

    def show_track_menu(self, position: Any) -> None:
        row = self.table.rowAt(position.y())
        if row < 0:
            return
        path = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        track = next((item for item in self.visible_tracks if item["path"] == path), None)
        if track is None:
            return

        menu = QMenu(self)
        play_action = QAction("Reproducir", self)
        play_action.triggered.connect(lambda: self.play_track_from_path(path))
        menu.addAction(play_action)

        favorite_text = "Quitar de favoritos" if track["is_favorite"] else "Añadir a favoritos"
        favorite_action = QAction(favorite_text, self)
        favorite_action.triggered.connect(lambda: self.toggle_favorite(path, not bool(track["is_favorite"])))
        menu.addAction(favorite_action)

        remove_action = QAction("Retirar de la biblioteca", self)
        remove_action.triggered.connect(lambda: self.remove_from_library(path))
        menu.addSeparator()
        menu.addAction(remove_action)
        menu.exec(self.table.viewport().mapToGlobal(position))

    def play_track_from_path(self, path: str) -> None:
        self.queue = list(self.visible_tracks)
        self.current_index = next(
            (index for index, track in enumerate(self.queue) if track["path"] == path),
            -1,
        )
        track = next((item for item in self.visible_tracks if item["path"] == path), None)
        if track:
            self.play_track(track)

    def toggle_favorite(self, path: str, favorite: bool) -> None:
        self.database.set_favorite(path, favorite)
        self.load_library()

    def remove_from_library(self, path: str) -> None:
        answer = QMessageBox.question(
            self,
            "Retirar canción",
            "¿Quieres retirar esta canción de MusicFy? El archivo original no se borrará.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.database.remove_track(path)
            self.load_library()

    def open_online_url(self) -> None:
        url, accepted = QInputDialog.getText(
            self,
            "Reproducción online",
            "Pega la URL de una fuente de audio compatible:",
        )
        if not accepted or not url.strip():
            return
        if not url.strip().startswith(("https://", "http://")):
            QMessageBox.warning(self, "URL no válida", "Introduce una dirección http:// o https://.")
            return

        consent = QMessageBox.question(
            self,
            "Uso de fuentes online",
            "Continúa únicamente con contenido propio, de dominio público, con licencia compatible "
            "o para el que tengas permiso, y cuando la fuente permita la reproducción externa. "
            "MusicFy no descarga audio ni elimina protecciones. ¿Quieres continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if consent != QMessageBox.StandardButton.Yes:
            return

        self.online_button.setEnabled(False)
        self.statusBar().showMessage("Consultando la fuente online…")
        self.online_resolver = OnlineResolver(url.strip())
        self.online_resolver.resolved.connect(self.play_online_result)
        self.online_resolver.failed.connect(self.online_failed)
        self.online_resolver.finished.connect(lambda: self.online_button.setEnabled(True))
        self.online_resolver.start()

    def play_online_result(self, track: dict[str, Any]) -> None:
        self.queue = []
        self.current_index = -1
        self.current_track = track
        self.now_title.setText(track["title"])
        self.now_artist.setText(track["artist"])
        self.position_slider.setValue(0)
        self.position_label.setText("0:00")
        self.duration_label.setText(self.format_time(track.get("duration", 0)))
        self.player.setSource(QUrl(track["url"]))
        self.player.play()
        self.statusBar().showMessage(f"Reproducción online: {track['title']}", 6000)

    def online_failed(self, message: str) -> None:
        self.statusBar().showMessage("No se ha podido abrir la fuente online.", 6000)
        QMessageBox.warning(
            self,
            "No se puede reproducir",
            "No se ha podido resolver esta URL. Puede que la fuente no permita "
            "reproducción externa o que el formato no sea compatible.\n\n"
            + message[:1200],
        )

    def handle_player_error(self, _error: QMediaPlayer.Error, error_string: str) -> None:
        if error_string:
            self.statusBar().showMessage(f"Error de reproducción: {error_string}", 8000)

    def closeEvent(self, event: Any) -> None:
        if self.online_resolver and self.online_resolver.isRunning():
            self.online_resolver.quit()
            self.online_resolver.wait(1500)
        self.database.close()
        super().closeEvent(event)
