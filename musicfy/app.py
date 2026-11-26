from __future__ import annotations

import hashlib
from functools import partial
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import (
    QAction,
    QColor,
    QFont,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QStackedWidget,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from musicfy.database import MusicDatabase
from musicfy.library import read_audio_file, scan_folder
from musicfy.online import OnlineResolver


def draw_vector_icon(painter: QPainter, name: str, color: str, size: int) -> None:
    """Paint consistent outline icons without emoji fonts or external assets."""
    painter.save()
    painter.scale(size / 24.0, size / 24.0)
    pen = QPen(QColor(color))
    pen.setWidthF(1.8)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()

    if name == "home":
        path.moveTo(3, 10.5); path.lineTo(12, 3); path.lineTo(21, 10.5)
        path.moveTo(5.5, 9.5); path.lineTo(5.5, 21); path.lineTo(10, 21)
        path.lineTo(10, 15); path.lineTo(14, 15); path.lineTo(14, 21)
        path.lineTo(18.5, 21); path.lineTo(18.5, 9.5)
        painter.drawPath(path)
    elif name == "tracks":
        painter.drawRoundedRect(4, 3, 16, 18, 2, 2)
        for y, end in ((8, 16), (12, 16), (16, 14)):
            painter.drawLine(8, y, end, y)
            painter.drawEllipse(6, y - .5, 1, 1)
    elif name == "albums":
        painter.drawRoundedRect(3, 3, 18, 18, 3, 3)
        painter.drawEllipse(7, 7, 10, 10)
        painter.drawEllipse(10.5, 10.5, 3, 3)
    elif name == "artist":
        painter.drawEllipse(8, 3, 8, 8)
        path.moveTo(4, 21); path.cubicTo(4.5, 16.5, 7, 14.5, 12, 14.5)
        path.cubicTo(17, 14.5, 19.5, 16.5, 20, 21)
        painter.drawPath(path)
    elif name == "genres":
        for y, knob_x in ((6, 8), (12, 16), (18, 10)):
            painter.drawLine(3, y, 21, y)
            painter.setBrush(QColor("#0d1117"))
            painter.drawEllipse(knob_x - 2, y - 2, 4, 4)
            painter.setBrush(Qt.BrushStyle.NoBrush)
    elif name == "star":
        points = [(12, 2.5), (14.8, 8.5), (21.3, 9.3), (16.5, 13.8),
                  (17.7, 20.5), (12, 17.2), (6.3, 20.5), (7.5, 13.8),
                  (2.7, 9.3), (9.2, 8.5)]
        path.moveTo(*points[0])
        for point in points[1:]: path.lineTo(*point)
        path.closeSubpath()
        painter.drawPath(path)
    elif name == "history":
        painter.drawEllipse(3, 3, 18, 18)
        painter.drawLine(12, 6.5, 12, 12); painter.drawLine(12, 12, 16, 14.5)
        painter.drawLine(3.5, 7, 3.5, 3.5); painter.drawLine(3.5, 3.5, 7, 3.5)
    elif name == "plus":
        painter.drawLine(12, 4, 12, 20); painter.drawLine(4, 12, 20, 12)
    elif name == "folder":
        path.moveTo(2.5, 7); path.lineTo(2.5, 19)
        path.quadTo(2.5, 21, 4.5, 21); path.lineTo(19.5, 21)
        path.quadTo(21.5, 21, 21.5, 19); path.lineTo(21.5, 8.5)
        path.quadTo(21.5, 6.5, 19.5, 6.5); path.lineTo(11, 6.5)
        path.lineTo(8.8, 4); path.lineTo(4.5, 4)
        path.quadTo(2.5, 4, 2.5, 6); path.closeSubpath()
        painter.drawPath(path)
    elif name == "globe":
        painter.drawEllipse(3, 3, 18, 18); painter.drawEllipse(8, 3, 8, 18)
        painter.drawLine(4, 9, 20, 9); painter.drawLine(4, 15, 20, 15)
    elif name == "arrow-right":
        painter.drawLine(4, 12, 20, 12); painter.drawLine(14, 6, 20, 12)
        painter.drawLine(14, 18, 20, 12)
    elif name == "arrow-left":
        painter.drawLine(20, 12, 4, 12); painter.drawLine(10, 6, 4, 12)
        painter.drawLine(10, 18, 4, 12)
    elif name == "search":
        painter.drawEllipse(3, 3, 13, 13); painter.drawLine(15, 15, 21, 21)
    elif name == "music-note":
        path.moveTo(15, 4); path.lineTo(15, 16); path.moveTo(15, 5)
        path.lineTo(21, 3.5); path.lineTo(21, 15)
        painter.drawPath(path); painter.setBrush(QColor(color))
        painter.drawEllipse(9, 14.5, 6, 5); painter.drawEllipse(15, 13.5, 6, 5)
    elif name == "play":
        path.moveTo(7, 4); path.lineTo(20, 12); path.lineTo(7, 20); path.closeSubpath()
        painter.setBrush(QColor(color)); painter.drawPath(path)
    elif name == "pause":
        painter.setBrush(QColor(color)); painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(6, 4, 4.5, 16, 1, 1)
        painter.drawRoundedRect(13.5, 4, 4.5, 16, 1, 1)
    elif name == "previous":
        painter.setBrush(QColor(color)); painter.setPen(Qt.PenStyle.NoPen)
        path.moveTo(19, 5); path.lineTo(8, 12); path.lineTo(19, 19); path.closeSubpath()
        painter.drawPath(path); painter.drawRoundedRect(4, 5, 2.2, 14, 1, 1)
    elif name == "next":
        painter.setBrush(QColor(color)); painter.setPen(Qt.PenStyle.NoPen)
        path.moveTo(5, 5); path.lineTo(16, 12); path.lineTo(5, 19); path.closeSubpath()
        painter.drawPath(path); painter.drawRoundedRect(18, 5, 2.2, 14, 1, 1)

    painter.restore()


class IconGlyph(QLabel):
    """Small vector glyph used consistently throughout MusicFy."""

    def __init__(self, icon_name: str, color: str = "#c9d4e1",
                 size: int = 20, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.icon_name = icon_name
        self.icon_color = color
        self.icon_size = size
        self.setFixedSize(size + 2, size + 2)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def set_icon(self, icon_name: str) -> None:
        self.icon_name = icon_name
        self.update()

    def set_color(self, color: str) -> None:
        self.icon_color = color
        self.update()

    def paintEvent(self, event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.translate((self.width() - self.icon_size) / 2,
                          (self.height() - self.icon_size) / 2)
        draw_vector_icon(painter, self.icon_name, self.icon_color, self.icon_size)
        painter.end()


class IconButton(QPushButton):
    """Button with a vector icon and a label, never a Unicode symbol."""

    def __init__(self, icon_name: str, label: str = "",
                 parent: QWidget | None = None, icon_color: str = "#c9d4e1",
                 icon_size: int = 17) -> None:
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName(label or icon_name.replace("-", " "))
        self._button_layout = QHBoxLayout(self)
        self._button_layout.setContentsMargins(12, 0, 12, 0)
        self._button_layout.setSpacing(9)
        self.icon_widget = IconGlyph(icon_name, icon_color, icon_size, self)
        self._button_layout.addWidget(self.icon_widget, 0, Qt.AlignmentFlag.AlignVCenter)
        self.label_widget = QLabel(label, self)
        self.label_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._button_layout.addWidget(self.label_widget, 0, Qt.AlignmentFlag.AlignVCenter)
        self._button_layout.addStretch(1)
        if not label:
            self._button_layout.setContentsMargins(0, 0, 0, 0)
            self._button_layout.setSpacing(0)

    def set_icon(self, icon_name: str) -> None:
        self.icon_widget.set_icon(icon_name)

    def set_icon_color(self, color: str) -> None:
        self.icon_widget.set_color(color)

    def set_label_color(self, color: str) -> None:
        self.label_widget.setStyleSheet(f"color: {color}; font-weight: 800;")



class CollectionCard(QFrame):
    """Clickable album, artist or genre tile."""

    clicked = pyqtSignal()

    def __init__(
        self,
        title: str,
        subtitle: str,
        cover: QPixmap,
        kind: str = "album",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("collectionCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedWidth(198)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 12)
        layout.setSpacing(8)

        art = QLabel()
        art.setObjectName("collectionCover")
        art.setAlignment(Qt.AlignmentFlag.AlignCenter)
        art.setFixedSize(176, 176)
        art.setPixmap(
            cover.scaled(
                176,
                176,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        art.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(art, 0, Qt.AlignmentFlag.AlignHCenter)

        name = QLabel(title)
        name.setObjectName("collectionTitle")
        name.setWordWrap(True)
        name.setMaximumHeight(38)
        name.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        name.setToolTip(title)
        layout.addWidget(name)

        detail = QLabel(subtitle)
        detail.setObjectName("collectionSubtitle")
        detail.setWordWrap(True)
        detail.setMaximumHeight(30)
        detail.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(detail)

        self.kind = kind

    def mousePressEvent(self, event: Any) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class MusicFyWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MusicFy")
        self.setObjectName("musicFyWindow")
        self.resize(1360, 880)
        self.setMinimumSize(1000, 700)

        self.database = MusicDatabase()
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(0.72)
        self.player.setAudioOutput(self.audio_output)

        self.page_mode = "home"
        self.last_collection_mode = "albums"
        self.active_collection: dict[str, Any] | None = None
        self.visible_tracks: list[dict[str, Any]] = []
        self.queue: list[dict[str, Any]] = []
        self.current_track: dict[str, Any] | None = None
        self.current_index = -1
        self.online_resolver: OnlineResolver | None = None
        self.nav_buttons: dict[str, QPushButton] = {}

        self._build_ui()
        self._connect_player()
        self._load_styles()
        self.refresh_content()

    # ------------------------------------------------------------------
    # Interface
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(15)

        sidebar = self._build_sidebar()
        root_layout.addWidget(sidebar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(5, 3, 3, 0)
        content_layout.setSpacing(15)

        header = QHBoxLayout()
        header_copy = QVBoxLayout()
        eyebrow = QLabel("N3MESIS STUDIO  /  MUSIC PLAYER")
        eyebrow.setObjectName("eyebrow")
        header_copy.addWidget(eyebrow)

        self.page_title = QLabel("Tu espacio musical")
        self.page_title.setObjectName("pageTitle")
        header_copy.addWidget(self.page_title)

        self.page_subtitle = QLabel("Toda tu colección, con un lugar para cada canción.")
        self.page_subtitle.setObjectName("muted")
        header_copy.addWidget(self.page_subtitle)
        header.addLayout(header_copy)
        header.addStretch(1)

        self.online_button = IconButton("globe", "URL online")
        self.online_button.setObjectName("secondaryButton")
        self.online_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.online_button.clicked.connect(self.open_online_url)
        header.addWidget(self.online_button)
        content_layout.addLayout(header)

        action_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setObjectName("searchBox")
        self.search_box.setPlaceholderText("Buscar canciones, álbumes, artistas o géneros...")
        self.search_box.setClearButtonEnabled(True)
        self.search_box.textChanged.connect(self.refresh_content)
        action_row.addWidget(self.search_box, 1)

        add_files_button = IconButton("plus", "Añadir música")
        add_files_button.set_icon_color("#06131b")
        add_files_button.set_label_color("#06131b")
        add_files_button.setObjectName("primaryButton")
        add_files_button.setCursor(Qt.CursorShape.PointingHandCursor)
        add_files_button.clicked.connect(self.add_audio_files)
        action_row.addWidget(add_files_button)

        add_folder_button = IconButton("folder", "Añadir carpeta")
        add_folder_button.setObjectName("secondaryButton")
        add_folder_button.setCursor(Qt.CursorShape.PointingHandCursor)
        add_folder_button.clicked.connect(self.add_music_folder)
        action_row.addWidget(add_folder_button)
        content_layout.addLayout(action_row)

        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self._build_home_page())
        self.content_stack.addWidget(self._build_tracks_page())
        self.content_stack.addWidget(self._build_collections_page())
        content_layout.addWidget(self.content_stack, 1)

        content_layout.addWidget(self._build_player_bar())
        root_layout.addWidget(content, 1)
        self.setCentralWidget(root)
        self.statusBar().showMessage("Listo para descubrir tu música.")

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(214)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(16, 22, 16, 18)
        side_layout.setSpacing(7)

        brand_row = QHBoxLayout()
        brand_mark = IconGlyph("music-note", "#ffffff", 23)
        brand_mark.setObjectName("brandMark")
        brand_mark.setFixedSize(38, 38)
        brand_row.addWidget(brand_mark)

        brand = QLabel("MusicFy")
        brand.setObjectName("brand")
        brand_row.addWidget(brand)
        brand_row.addStretch(1)
        side_layout.addLayout(brand_row)

        brand_caption = QLabel("YOUR MUSIC. YOUR SPACE.")
        brand_caption.setObjectName("eyebrow")
        side_layout.addWidget(brand_caption)
        side_layout.addSpacing(25)

        self._add_nav_group(side_layout, "DESCUBRIR", [
            ("home", "Inicio", "home"),
        ])
        self._add_nav_group(side_layout, "TU COLECCIÓN", [
            ("tracks", "Canciones", "tracks"),
            ("albums", "Álbumes", "albums"),
            ("artist", "Artistas", "artists"),
            ("genres", "Géneros", "genres"),
        ])
        self._add_nav_group(side_layout, "TU MÚSICA", [
            ("star", "Favoritos", "favorites"),
            ("history", "Escuchado recientemente", "history"),
        ])

        side_layout.addStretch(1)

        local_note = QLabel("TU MÚSICA\nSIEMPRE CONTIGO")
        local_note.setObjectName("sidebar_note")
        side_layout.addWidget(local_note)

        version = QLabel("MUSICFY  ·  0.3.1")
        version.setObjectName("version")
        side_layout.addWidget(version)
        return sidebar

    def _add_nav_group(
        self,
        parent_layout: QVBoxLayout,
        heading: str,
        items: list[tuple[str, str, str]],
    ) -> None:
        label = QLabel(heading)
        label.setObjectName("navGroupLabel")
        parent_layout.addWidget(label)
        for icon_name, title, mode in items:
            button = IconButton(icon_name, title)
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.setChecked(mode == "home")
            button.set_icon_color("#111820" if mode == "home" else "#aebac8")
            button.label_widget.setStyleSheet(
                "color: #111820; font-weight: 750;" if mode == "home"
                else "color: #aebac8; font-weight: 650;"
            )
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _checked=False, selected=mode: self.show_page(selected))
            parent_layout.addWidget(button)
            self.nav_buttons[mode] = button
        parent_layout.addSpacing(12)

    def _build_home_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(17)

        # Editorial hero: headline, useful action and custom MusicFy artwork.
        hero = QFrame()
        hero.setObjectName("heroBanner")
        hero.setMinimumHeight(208)
        hero.setMaximumHeight(220)
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(30, 22, 24, 22)
        hero_layout.setSpacing(12)

        copy = QVBoxLayout()
        copy.setSpacing(8)
        hero_kicker = QLabel("TU COLECCIÓN · TU BIBLIOTECA")
        hero_kicker.setObjectName("heroKicker")
        copy.addWidget(hero_kicker)

        hero_title = QLabel("Tu música,\na tu manera.")
        hero_title.setObjectName("heroTitle")
        copy.addWidget(hero_title)

        hero_text = QLabel(
            "Todos tus álbumes, artistas y canciones en un mismo lugar."
        )
        hero_text.setObjectName("heroText")
        hero_text.setWordWrap(True)
        hero_text.setMaximumWidth(440)
        copy.addWidget(hero_text)

        explore = IconButton("arrow-right", "Explorar mi biblioteca")
        explore.set_icon_color("#06131b")
        explore.set_label_color("#06131b")
        explore.setObjectName("heroButton")
        explore.setCursor(Qt.CursorShape.PointingHandCursor)
        explore.clicked.connect(lambda: self.show_page("tracks"))
        copy.addWidget(explore, 0, Qt.AlignmentFlag.AlignLeft)
        copy.addStretch(1)
        hero_layout.addLayout(copy, 1)

        self.hero_artwork = QLabel()
        self.hero_artwork.setObjectName("heroArtwork")
        self.hero_artwork.setFixedSize(205, 150)
        self.hero_artwork.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hero_artwork.setPixmap(
            self._hero_artwork().scaled(
                205,
                150,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.hero_artwork.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        hero_layout.addWidget(
            self.hero_artwork,
            0,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        layout.addWidget(hero)

        # Compact library metrics instead of oversized dashboard tiles.
        stats = QHBoxLayout()
        stats.setSpacing(12)
        self.total_stat = self._make_stat_card("CANCIONES", "0", "tracks")
        self.album_stat = self._make_stat_card("ÁLBUMES", "0", "albums")
        self.artist_stat = self._make_stat_card("ARTISTAS", "0", "artist")
        self.favorites_stat = self._make_stat_card("FAVORITOS", "0", "star")
        for card in (self.total_stat, self.album_stat, self.artist_stat, self.favorites_stat):
            card.setMinimumHeight(76)
            card.setMaximumHeight(82)
            stats.addWidget(card)
        layout.addLayout(stats)

        self.home_section_header = QWidget()
        section_header = QHBoxLayout(self.home_section_header)
        section_header.setContentsMargins(0, 0, 0, 0)
        section_title = QLabel("Álbumes de tu biblioteca")
        section_title.setObjectName("sectionTitle")
        section_header.addWidget(section_title)
        section_header.addStretch(1)
        all_albums = IconButton("arrow-right", "Ver toda la colección")
        all_albums.setObjectName("textButton")
        all_albums.setCursor(Qt.CursorShape.PointingHandCursor)
        all_albums.clicked.connect(lambda: self.show_page("albums"))
        section_header.addWidget(all_albums)
        layout.addWidget(self.home_section_header)

        # Horizontal album rail, like a modern streaming library.
        self.home_album_scroll = QScrollArea()
        self.home_album_scroll.setObjectName("homeAlbumScroll")
        self.home_album_scroll.setWidgetResizable(True)
        self.home_album_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.home_album_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.home_album_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.home_album_area = QWidget()
        self.home_album_row = QHBoxLayout(self.home_album_area)
        self.home_album_row.setContentsMargins(2, 2, 10, 10)
        self.home_album_row.setSpacing(14)
        self.home_album_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.home_album_scroll.setWidget(self.home_album_area)
        layout.addWidget(self.home_album_scroll, 1)

        # Proper empty state, with real next actions.
        self.home_empty_card = QFrame()
        self.home_empty_card.setObjectName("emptyStateCard")
        self.home_empty_card.setMinimumHeight(176)
        empty_layout = QHBoxLayout(self.home_empty_card)
        empty_layout.setContentsMargins(24, 22, 24, 22)
        empty_layout.setSpacing(19)

        self.home_empty_icon = IconGlyph("albums", "#d8e8f2", 30)
        self.home_empty_icon.setObjectName("emptyStateIcon")
        self.home_empty_icon.setFixedSize(64, 64)
        empty_layout.addWidget(self.home_empty_icon)

        empty_copy = QVBoxLayout()
        empty_copy.setSpacing(6)
        self.home_empty_title = QLabel("Tu biblioteca empieza aquí")
        self.home_empty_title.setObjectName("emptyStateTitle")
        empty_copy.addWidget(self.home_empty_title)

        self.home_empty = QLabel(
            "Añade tus archivos o selecciona una carpeta para reunir toda tu música."
        )
        self.home_empty.setObjectName("emptyState")
        self.home_empty.setWordWrap(True)
        self.home_empty.setMaximumWidth(490)
        empty_copy.addWidget(self.home_empty)
        empty_copy.addStretch(1)
        empty_layout.addLayout(empty_copy, 1)

        empty_actions = QVBoxLayout()
        empty_actions.setSpacing(8)
        empty_files_button = IconButton("plus", "Añadir canciones")
        empty_files_button.set_icon_color("#06131b")
        empty_files_button.set_label_color("#06131b")
        empty_files_button.setObjectName("primaryButton")
        empty_files_button.setCursor(Qt.CursorShape.PointingHandCursor)
        empty_files_button.clicked.connect(self.add_audio_files)
        empty_actions.addWidget(empty_files_button)

        empty_folder_button = IconButton("folder", "Elegir carpeta")
        empty_folder_button.setObjectName("secondaryButton")
        empty_folder_button.setCursor(Qt.CursorShape.PointingHandCursor)
        empty_folder_button.clicked.connect(self.add_music_folder)
        empty_actions.addWidget(empty_folder_button)
        empty_layout.addLayout(empty_actions)
        layout.addWidget(self.home_empty_card, 1)
        return page

    def _build_tracks_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        detail_row = QHBoxLayout()
        self.back_button = IconButton("arrow-left", "Volver a la colección")
        self.back_button.setObjectName("textButton")
        self.back_button.clicked.connect(self.return_from_detail)
        self.back_button.hide()
        detail_row.addWidget(self.back_button)
        detail_row.addStretch(1)
        self.result_count = QLabel("0 pistas")
        self.result_count.setObjectName("muted")
        detail_row.addWidget(self.result_count)
        layout.addLayout(detail_row)

        self.table = QTableWidget(0, 5)
        self.table.setObjectName("trackTable")
        self.table.setHorizontalHeaderLabels(["TÍTULO", "ARTISTA", "ÁLBUM", "DURACIÓN", "FAV"])
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(56)
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
        layout.addWidget(self.table, 1)
        return page

    def _build_collections_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setObjectName("collectionScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.collection_area = QWidget()
        self.collection_grid = QGridLayout(self.collection_area)
        self.collection_grid.setContentsMargins(2, 2, 8, 16)
        self.collection_grid.setHorizontalSpacing(14)
        self.collection_grid.setVerticalSpacing(15)
        self.collection_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(self.collection_area)
        return scroll

    def _build_player_bar(self) -> QFrame:
        player_bar = QFrame()
        player_bar.setObjectName("playerBar")
        player_layout = QVBoxLayout(player_bar)
        player_layout.setContentsMargins(14, 10, 14, 10)
        player_layout.setSpacing(7)

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

        controls = QHBoxLayout()
        self.cover_placeholder = QLabel()
        self.cover_placeholder.setObjectName("coverPlaceholder")
        self.cover_placeholder.setFixedSize(50, 50)
        self.cover_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_placeholder.setPixmap(self._icon_pixmap("music-note", "#d8e8f2", 25))
        controls.addWidget(self.cover_placeholder)

        current = QVBoxLayout()
        self.now_title = QLabel("Selecciona una canción")
        self.now_title.setObjectName("nowTitle")
        self.now_artist = QLabel("Tu música aparecerá aquí")
        self.now_artist.setObjectName("muted")
        current.addWidget(self.now_title)
        current.addWidget(self.now_artist)
        controls.addLayout(current)
        controls.addStretch(1)

        self.previous_button = IconButton("previous")
        self.previous_button.setObjectName("controlButton")
        self.previous_button.setFixedSize(38, 38)
        self.previous_button.clicked.connect(lambda: self.skip_track(-1))
        controls.addWidget(self.previous_button)

        self.play_button = IconButton("play")
        self.play_button.setObjectName("playButton")
        self.play_button.set_icon_color("#07131b")
        self.play_button.setFixedSize(44, 44)
        self.play_button.clicked.connect(self.toggle_playback)
        controls.addWidget(self.play_button)

        self.next_button = IconButton("next")
        self.next_button.setObjectName("controlButton")
        self.next_button.setFixedSize(38, 38)
        self.next_button.clicked.connect(lambda: self.skip_track(1))
        controls.addWidget(self.next_button)
        controls.addStretch(1)

        volume_label = QLabel("VOL")
        volume_label.setObjectName("eyebrow")
        controls.addWidget(volume_label)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setObjectName("volumeSlider")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(72)
        self.volume_slider.setFixedWidth(105)
        self.volume_slider.valueChanged.connect(
            lambda value: self.audio_output.setVolume(value / 100)
        )
        controls.addWidget(self.volume_slider)
        player_layout.addLayout(controls)
        return player_bar

    def _make_stat_card(self, heading: str, value: str, icon_name: str) -> QFrame:
        card = QFrame()
        card.setObjectName("statCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(13, 11, 13, 11)
        layout.setSpacing(10)
        icon = IconGlyph(icon_name, "#d6e4ef", 21)
        icon.setObjectName("statIcon")
        layout.addWidget(icon)
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        title = QLabel(heading)
        title.setObjectName("eyebrow")
        number = QLabel(value)
        number.setObjectName("statValue")
        text_layout.addWidget(title)
        text_layout.addWidget(number)
        layout.addLayout(text_layout)
        layout.addStretch(1)
        card.value_label = number  # type: ignore[attr-defined]
        return card

    def _load_styles(self) -> None:
        stylesheet = Path(__file__).with_name("styles.qss")
        try:
            self.setStyleSheet(stylesheet.read_text(encoding="utf-8"))
        except OSError:
            self.statusBar().showMessage("No se ha podido cargar styles.qss.")

    # ------------------------------------------------------------------
    # Navigation and content
    # ------------------------------------------------------------------
    def show_page(self, mode: str) -> None:
        self.page_mode = mode
        self.active_collection = None
        self.back_button.hide()

        for key, button in self.nav_buttons.items():
            selected = key == mode
            button.setChecked(selected)
            button.set_icon_color("#101820" if selected else "#aab6c4")
            button.label_widget.setStyleSheet(
                "color: #101820; font-weight: 750;" if selected
                else "color: #aab6c4; font-weight: 650;"
            )

        page_details = {
            "home": ("Tu espacio musical", "Toda tu colección, con un lugar para cada canción.", 0),
            "tracks": ("Todas las canciones", "Tu biblioteca completa, lista para reproducir.", 1),
            "albums": ("Tus álbumes", "Colecciones completas, con sus portadas originales.", 2),
            "artists": ("Artistas", "Explora tu música por intérprete.", 2),
            "genres": ("Géneros", "Encuentra el sonido que te apetece escuchar.", 2),
            "favorites": ("Tus favoritos", "Las canciones que quieres tener siempre a mano.", 1),
            "history": ("Escuchado recientemente", "Vuelve a lo que estabas disfrutando.", 1),
        }
        title, subtitle, stack_index = page_details.get(mode, page_details["home"])
        self.page_title.setText(title)
        self.page_subtitle.setText(subtitle)
        self.content_stack.setCurrentIndex(stack_index)
        self.refresh_content()

    def show_collection_detail(self, kind: str, record: dict[str, Any]) -> None:
        self.last_collection_mode = self.page_mode
        self.active_collection = {"kind": kind, **record}
        self.page_mode = "detail"
        self.content_stack.setCurrentIndex(1)
        self.back_button.show()

        if kind == "album":
            title = str(record.get("album") or "Álbum")
            subtitle = f'{record.get("artist", "Artista desconocido")}  ·  {record.get("track_count", 0)} canciones'
        elif kind == "artist":
            title = str(record.get("artist") or "Artista")
            subtitle = f'{record.get("album_count", 0)} álbumes  ·  {record.get("track_count", 0)} canciones'
        else:
            title = str(record.get("genre") or "Género")
            subtitle = f'{record.get("track_count", 0)} canciones'
        self.page_title.setText(title)
        self.page_subtitle.setText(subtitle)
        self.refresh_content()

    def return_from_detail(self) -> None:
        self.show_page(self.last_collection_mode)

    def refresh_content(self, *_args: Any) -> None:
        all_tracks = self.database.list_tracks("all")
        favorites = self.database.list_tracks("favorites")
        albums = self.database.list_albums()
        artists = self.database.list_artists()

        self.total_stat.value_label.setText(str(len(all_tracks)))  # type: ignore[attr-defined]
        self.album_stat.value_label.setText(str(len(albums)))  # type: ignore[attr-defined]
        self.artist_stat.value_label.setText(str(len(artists)))  # type: ignore[attr-defined]
        self.favorites_stat.value_label.setText(str(len(favorites)))  # type: ignore[attr-defined]

        if self.page_mode == "home":
            self._render_home(albums)
        elif self.page_mode in ("albums", "artists", "genres"):
            self._render_collections()
        elif self.page_mode == "detail":
            collection = self.active_collection or {}
            tracks = self.database.tracks_for_collection(
                str(collection.get("kind", "")),
                str(collection.get("album") or collection.get("artist") or collection.get("genre") or ""),
                str(collection.get("artist")) if collection.get("kind") == "album" else None,
            )
            self._render_tracks(tracks)
        elif self.page_mode == "favorites":
            self._render_tracks(favorites)
        elif self.page_mode == "history":
            self._render_tracks(self.database.list_tracks("history"))
        else:
            self._render_tracks(all_tracks)

    def _render_home(self, albums: list[dict[str, Any]]) -> None:
        query = self.search_box.text().strip().casefold()
        records = albums
        if query:
            records = [
                item for item in albums
                if query in str(item["album"]).casefold()
                or query in str(item["artist"]).casefold()
            ]

        self._clear_layout(self.home_album_row)
        for record in records[:12]:
            card = self._make_collection_card("album", record)
            card.clicked.connect(partial(self.show_collection_detail, "album", record))
            self.home_album_row.addWidget(card)
        self.home_album_row.addStretch(1)

        has_music = bool(self.database.list_tracks("all"))
        has_albums = bool(records)
        show_empty = not has_albums

        self.home_section_header.setVisible(has_albums)
        self.home_album_scroll.setVisible(has_albums)
        self.home_empty_card.setVisible(show_empty)

        if not has_music:
            self.home_empty_icon.set_icon("albums")
            self.home_empty_title.setText("Tu biblioteca empieza aquí")
            self.home_empty.setText(
                "Añade tus archivos o selecciona una carpeta para reunir toda tu música."
            )
        elif not has_albums:
            self.home_empty_icon.set_icon("search")
            self.home_empty_title.setText("No encontramos esos álbumes")
            self.home_empty.setText(
                "Prueba con otro título o artista, o borra la búsqueda para volver a tu colección."
            )

        # In the empty state, make the action card the main content instead of
        # leaving a large, unexplained blank region below the statistics.
        if hasattr(self, "home_empty_card"):
            for child in self.home_empty_card.findChildren(QPushButton):
                child.setVisible(not has_music)

    def _render_collections(self) -> None:
        self._clear_grid(self.collection_grid)
        query = self.search_box.text().strip().casefold()

        if self.page_mode == "albums":
            kind = "album"
            records = self.database.list_albums()
            records = [
                item for item in records
                if not query
                or query in str(item["album"]).casefold()
                or query in str(item["artist"]).casefold()
            ]
        elif self.page_mode == "artists":
            kind = "artist"
            records = self.database.list_artists()
            records = [
                item for item in records
                if not query or query in str(item["artist"]).casefold()
            ]
        else:
            kind = "genre"
            records = self.database.list_genres()
            records = [
                item for item in records
                if not query or query in str(item["genre"]).casefold()
            ]

        for index, record in enumerate(records):
            card = self._make_collection_card(kind, record)
            card.clicked.connect(partial(self.show_collection_detail, kind, record))
            self.collection_grid.addWidget(card, index // 4, index % 4)

        if not records:
            empty = QLabel(
                "No hay resultados para esta búsqueda."
                if query else "Todavía no hay contenido. Añade música para llenar tu biblioteca."
            )
            empty.setObjectName("emptyState")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setMinimumHeight(180)
            self.collection_grid.addWidget(empty, 0, 0, 1, 4)

    def _make_collection_card(
        self,
        kind: str,
        record: dict[str, Any],
    ) -> CollectionCard:
        if kind == "album":
            title = str(record.get("album") or "Álbum desconocido")
            subtitle = f'{record.get("artist", "Artista desconocido")}  ·  {record.get("track_count", 0)} canciones'
        elif kind == "artist":
            title = str(record.get("artist") or "Artista desconocido")
            subtitle = f'{record.get("album_count", 0)} álbumes  ·  {record.get("track_count", 0)} canciones'
        else:
            title = str(record.get("genre") or "Sin género")
            subtitle = f'{record.get("track_count", 0)} canciones'
        cover = self._cover_pixmap(record.get("cover_path"), title)
        return CollectionCard(title, subtitle, cover, kind)

    @staticmethod
    def _clear_layout(layout: Any) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    @staticmethod
    def _clear_grid(grid: QGridLayout) -> None:
        MusicFyWindow._clear_layout(grid)

    @staticmethod
    def _hero_artwork() -> QPixmap:
        pixmap = QPixmap(420, 260)
        pixmap.fill(QColor("#0d1d27"))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        background = QLinearGradient(0, 0, 420, 260)
        background.setColorAt(0, QColor("#123f56"))
        background.setColorAt(0.55, QColor("#102c3a"))
        background.setColorAt(1, QColor("#0b151c"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(background)
        painter.drawRoundedRect(0, 0, 420, 260, 28, 28)

        # Vinyl disc with subtle grooves and a lavender highlight.
        painter.setBrush(QColor("#0a111d"))
        painter.setPen(QColor(196, 215, 255, 42))
        painter.drawEllipse(218, 28, 206, 206)
        for inset in (12, 23, 35, 47, 61):
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QColor(185, 205, 250, 25))
            painter.drawEllipse(218 + inset, 28 + inset, 206 - inset * 2, 206 - inset * 2)
        painter.setBrush(QColor("#12aee9"))
        painter.setPen(QColor(220, 230, 255, 110))
        painter.drawEllipse(297, 107, 48, 48)
        painter.setBrush(QColor("#0d2633"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(314, 124, 14, 14)

        # Overlapping sleeve gives the composition a real album-art cue.
        sleeve = QLinearGradient(40, 20, 195, 230)
        sleeve.setColorAt(0, QColor("#a4e5f9"))
        sleeve.setColorAt(0.48, QColor("#1688b4"))
        sleeve.setColorAt(1, QColor("#103747"))
        painter.setBrush(sleeve)
        painter.setPen(QColor(235, 242, 255, 135))
        painter.drawRoundedRect(48, 32, 150, 190, 12, 12)
        painter.setPen(QColor(255, 255, 255, 35))
        painter.setBrush(QColor(255, 255, 255, 22))
        painter.drawEllipse(115, 10, 160, 160)
        painter.setPen(QColor("#f4f7ff"))
        painter.setFont(QFont("Segoe UI", 54, QFont.Weight.Bold))
        painter.drawText(76, 142, "M")
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(78, 173, "MUSICFY")
        painter.end()
        return pixmap

    def _cover_pixmap(self, cover_path: str | None, seed: str) -> QPixmap:
        if cover_path:
            pixmap = QPixmap(str(cover_path))
            if not pixmap.isNull():
                return pixmap
        return self._placeholder_cover(seed)

    @staticmethod
    def _icon_pixmap(icon_name: str, color: str, size: int = 24) -> QPixmap:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        draw_vector_icon(painter, icon_name, color, size)
        painter.end()
        return pixmap

    @staticmethod
    def _placeholder_cover(seed: str) -> QPixmap:
        digest = hashlib.sha1(seed.encode("utf-8", errors="replace")).digest()
        hue = int.from_bytes(digest[:2], "big") % 360
        base = QColor.fromHsv(hue, 125, 100)
        light = QColor.fromHsv(hue, 105, 155)
        pixmap = QPixmap(512, 512)
        pixmap.fill(QColor("#111a25"))

        painter = QPainter(pixmap)
        gradient = QLinearGradient(0, 0, 512, 512)
        gradient.setColorAt(0, light)
        gradient.setColorAt(1, base.darker(190))
        painter.fillRect(0, 0, 512, 512, gradient)
        painter.setPen(QColor(255, 255, 255, 28))
        painter.setBrush(QColor(255, 255, 255, 18))
        painter.drawEllipse(285, -95, 330, 330)
        painter.drawEllipse(-130, 330, 330, 330)
        painter.setPen(QColor(255, 255, 255, 225))
        painter.setFont(QFont("Segoe UI", 112, QFont.Weight.Bold))
        letters = "".join(part[0] for part in seed.split()[:2]).upper() or "MF"
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, letters)
        painter.end()
        return pixmap

    # ------------------------------------------------------------------
    # Local library management
    # ------------------------------------------------------------------
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
        self.statusBar().showMessage("Analizando archivos y carátulas…")
        tracks = scan_folder(folder)
        for track in tracks:
            self.database.save_track(track)
        self.refresh_content()
        self.statusBar().showMessage(
            f"Se han añadido o actualizado {len(tracks)} canciones.", 6000
        )

    def _import_paths(self, paths: list[str]) -> None:
        imported = 0
        for path in paths:
            track = read_audio_file(path)
            if track is not None:
                self.database.save_track(track)
                imported += 1
        self.refresh_content()
        self.statusBar().showMessage(
            f"Se han añadido o actualizado {imported} canciones.", 6000
        )

    def _render_tracks(self, tracks: list[dict[str, Any]]) -> None:
        query = self.search_box.text().strip().casefold()
        if query:
            tracks = [
                track for track in tracks
                if any(
                    query in str(track.get(key) or "").casefold()
                    for key in ("title", "artist", "album", "genre")
                )
            ]

        self.visible_tracks = tracks
        self.table.setRowCount(0)
        for row, track in enumerate(tracks):
            self.table.insertRow(row)
            title_item = QTableWidgetItem(str(track["title"]))
            title_item.setData(Qt.ItemDataRole.UserRole, track["path"])
            pixmap = self._cover_pixmap(track.get("cover_path"), str(track["title"]))
            title_item.setIcon(QIcon(pixmap.scaled(
                38, 38,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )))
            self.table.setItem(row, 0, title_item)
            self.table.setItem(row, 1, QTableWidgetItem(str(track["artist"])))
            self.table.setItem(row, 2, QTableWidgetItem(str(track["album"])))

            duration_item = QTableWidgetItem(self.format_time(track["duration"]))
            duration_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, duration_item)

            favorite_item = QTableWidgetItem("")
            if track["is_favorite"]:
                favorite_item.setIcon(QIcon(self._icon_pixmap("star", "#13aee8", 16)))
            favorite_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, favorite_item)

        self.result_count.setText(f"{len(tracks)} canciones")

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------
    def _connect_player(self) -> None:
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)
        self.player.playbackStateChanged.connect(self.update_play_button)
        self.player.mediaStatusChanged.connect(self.handle_media_status)
        self.player.errorOccurred.connect(self.handle_player_error)

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

        cover = self._cover_pixmap(track.get("cover_path"), title)
        self.cover_placeholder.setPixmap(cover.scaled(
            50, 50,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        ))
        self.cover_placeholder.setText("")

        if track.get("url"):
            source = QUrl(str(track["url"]))
        else:
            source = QUrl.fromLocalFile(str(track["path"]))
            self.database.mark_played(str(track["path"]))
            if self.page_mode == "history":
                self.refresh_content()

        self.player.setSource(source)
        self.player.play()
        self.statusBar().showMessage(f"Reproduciendo: {title}", 5000)

    def toggle_playback(self) -> None:
        state = self.player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        elif self.current_track is not None:
            self.player.play()
        elif self.visible_tracks:
            self.queue = list(self.visible_tracks)
            self.current_index = 0
            self.play_track(self.queue[0])

    def skip_track(self, offset: int) -> None:
        if not self.queue:
            tracks = self.database.list_tracks("all")
            if not tracks:
                return
            self.queue = tracks
            self.current_index = 0 if offset > 0 else len(self.queue) - 1
        else:
            self.current_index = (self.current_index + offset) % len(self.queue)
        self.play_track(self.queue[self.current_index])

    def handle_media_status(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia and self.queue:
            self.skip_track(1)

    def update_play_button(self, state: QMediaPlayer.PlaybackState) -> None:
        self.play_button.set_icon(
            "pause" if state == QMediaPlayer.PlaybackState.PlayingState else "play"
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

    # ------------------------------------------------------------------
    # Track actions and online entry point
    # ------------------------------------------------------------------
    def show_track_menu(self, position: Any) -> None:
        row = self.table.rowAt(position.y())
        if row < 0 or row >= len(self.visible_tracks):
            return
        track = self.visible_tracks[row]
        path = str(track["path"])

        menu = QMenu(self)
        play_action = QAction("Reproducir", self)
        play_action.triggered.connect(lambda: self.play_track_from_path(path))
        menu.addAction(play_action)

        favorite_text = "Quitar de favoritos" if track["is_favorite"] else "Añadir a favoritos"
        favorite_action = QAction(favorite_text, self)
        favorite_action.triggered.connect(
            lambda: self.toggle_favorite(path, not bool(track["is_favorite"]))
        )
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
        self.refresh_content()

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
            self.refresh_content()

    def open_online_url(self) -> None:
        url, accepted = QInputDialog.getText(
            self,
            "Reproducción online",
            "Pega la URL de una fuente de audio compatible:",
        )
        if not accepted or not url.strip():
            return
        if not url.strip().startswith(("https://", "http://")):
            QMessageBox.warning(
                self, "URL no válida", "Introduce una dirección http:// o https://."
            )
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
        self.online_resolver.finished.connect(
            lambda: self.online_button.setEnabled(True)
        )
        self.online_resolver.start()

    def play_online_result(self, track: dict[str, Any]) -> None:
        self.queue = []
        self.current_index = -1
        self.current_track = track
        self.now_title.setText(track["title"])
        self.now_artist.setText(track["artist"])
        self.cover_placeholder.setPixmap(self._placeholder_cover(track["title"]).scaled(
            50, 50,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        ))
        self.cover_placeholder.setText("")
        self.position_slider.setValue(0)
        self.position_label.setText("0:00")
        self.duration_label.setText(self.format_time(track.get("duration", 0)))
        self.player.setSource(QUrl(track["url"]))
        self.player.play()
        self.statusBar().showMessage(
            f"Reproducción online: {track['title']}", 6000
        )

    def online_failed(self, message: str) -> None:
        self.statusBar().showMessage(
            "No se ha podido abrir la fuente online.", 6000
        )
        QMessageBox.warning(
            self,
            "No se puede reproducir",
            "No se ha podido resolver esta URL. Puede que la fuente no permita "
            "reproducción externa o que el formato no sea compatible.\n\n"
            + message[:1200],
        )

    def handle_player_error(
        self,
        _error: QMediaPlayer.Error,
        error_string: str,
    ) -> None:
        if error_string:
            self.statusBar().showMessage(
                f"Error de reproducción: {error_string}", 8000
            )

    def closeEvent(self, event: Any) -> None:
        if self.online_resolver and self.online_resolver.isRunning():
            self.online_resolver.quit()
            self.online_resolver.wait(1500)
        self.database.close()
        super().closeEvent(event)
