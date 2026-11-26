from __future__ import annotations

import math
import struct
import unittest

from PyQt6.QtCore import QByteArray
from PyQt6.QtMultimedia import QAudioBuffer, QAudioFormat
from PyQt6.QtWidgets import QApplication

from musicfy.player_widgets import SpectrumWidget, audio_buffer_levels


class PlayerWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.qt_app = QApplication.instance() or QApplication([])

    def test_spectrum_is_derived_from_decoded_pcm(self) -> None:
        audio_format = QAudioFormat()
        audio_format.setSampleRate(44100)
        audio_format.setChannelCount(2)
        audio_format.setSampleFormat(QAudioFormat.SampleFormat.Float)

        sample_rate = audio_format.sampleRate()
        frames = 2048
        pcm = bytearray()
        for frame in range(frames):
            value = 0.75 * math.sin(2.0 * math.pi * 440.0 * frame / sample_rate)
            pcm.extend(struct.pack("<ff", value, value))

        buffer = QAudioBuffer(QByteArray(bytes(pcm)), audio_format)
        self.assertTrue(buffer.isValid())

        levels = audio_buffer_levels(buffer, band_count=24)
        self.assertEqual(len(levels), 24)
        self.assertGreater(max(levels), 0.08)
        self.assertTrue(all(0.0 <= level <= 1.0 for level in levels))

    def test_visualizer_accepts_level_updates_and_decays_when_paused(self) -> None:
        widget = SpectrumWidget(bars=12)
        widget.set_levels([0.8] * 12)
        before = list(widget._levels)
        self.assertEqual(len(before), 12)
        self.assertGreater(before[0], 0.5)

        widget.set_playing(False)
        widget._decay()
        self.assertLess(widget._levels[0], before[0])

    def test_empty_audio_buffer_returns_silence(self) -> None:
        buffer = QAudioBuffer()
        self.assertEqual(audio_buffer_levels(buffer, band_count=8), [0.0] * 8)


if __name__ == "__main__":
    unittest.main()
