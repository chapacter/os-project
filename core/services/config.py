import configparser
import os

import pygame

from utils.settings import TILESIZE

CONFIG_FILE = "config.ini"

WINDOW_MODES = ["fullscreen", "borderless", "windowed"]


def get_screen_resolution():
    info = pygame.display.Info()
    return info.current_w, info.current_h


def calculate_initial_scale(screen_w, screen_h):
    max_room_height_tiles = 32
    max_room_height_px = max_room_height_tiles * TILESIZE
    scale = screen_h / max_room_height_px
    return scale


class ConfigService:
    def __init__(self):
        self._config = configparser.ConfigParser()

    def init(self):
        if os.path.exists(CONFIG_FILE):
            self._config.read(CONFIG_FILE)
        else:
            self._config["Window"] = {}
            self._config["Display"] = {}
            self._config["Audio"] = {}
            self._config["Game"] = {}

        if "Window" not in self._config:
            self._config["Window"] = {}
        if "Display" not in self._config:
            self._config["Display"] = {}
        if "Audio" not in self._config:
            self._config["Audio"] = {}
        if "Game" not in self._config:
            self._config["Game"] = {}

        screen_w, screen_h = get_screen_resolution()
        self._config["Display"]["screen_width"] = str(screen_w)
        self._config["Display"]["screen_height"] = str(screen_h)

        if "display" not in self._config["Display"]:
            self._config["Display"]["display"] = "0"

        if "mode" not in self._config["Window"]:
            self._config["Window"]["mode"] = "fullscreen"

        if "width" not in self._config["Window"]:
            self._config["Window"]["width"] = str(screen_w)
            self._config["Window"]["height"] = str(screen_h)

        if "scale" not in self._config["Window"]:
            self._config["Window"]["scale"] = str(calculate_initial_scale(screen_w, screen_h))

        if "music_volume" not in self._config["Audio"]:
            self._config["Audio"]["music_volume"] = "0.5"
        if "menu_music_volume" not in self._config["Audio"]:
            self._config["Audio"]["menu_music_volume"] = "0.8"
        if "dungeon_music_volume" not in self._config["Audio"]:
            self._config["Audio"]["dungeon_music_volume"] = "0.5"
        if "sfx_volume" not in self._config["Audio"]:
            self._config["Audio"]["sfx_volume"] = "0.5"

        if "Game" not in self._config:
            self._config["Game"] = {}
        if "language" not in self._config["Game"]:
            self._config["Game"]["language"] = "ru"
        if "font" not in self._config["Game"]:
            self._config["Game"]["font"] = "0"

        self._save()

    def _save(self):
        with open(CONFIG_FILE, "w") as f:
            self._config.write(f)

    def get_window_mode(self):
        return self._config.get("Window", "mode", fallback="fullscreen")

    def set_window_mode(self, mode):
        if mode in WINDOW_MODES:
            self._config["Window"]["mode"] = mode
            self._save()

    def get_window_size(self):
        width = self._config.getint("Window", "width", fallback=1280)
        height = self._config.getint("Window", "height", fallback=720)
        return width, height

    def set_window_size(self, width, height):
        self._config["Window"]["width"] = str(width)
        self._config["Window"]["height"] = str(height)
        self._save()

    def get_next_window_mode(self):
        current = self.get_window_mode()
        idx = WINDOW_MODES.index(current)
        next_mode = WINDOW_MODES[(idx + 1) % len(WINDOW_MODES)]
        return next_mode

    def get_screen_size(self):
        try:
            return self.get_display_resolution()
        except Exception:
            width = self._config.getint("Display", "screen_width", fallback=1920)
            height = self._config.getint("Display", "screen_height", fallback=1080)
            return width, height

    def get_scale(self):
        return self._config.getfloat("Window", "scale", fallback=1.0)

    def set_scale(self, scale):
        self._config["Window"]["scale"] = str(scale)
        self._save()

    def get_music_volume(self):
        return self._config.getfloat("Audio", "music_volume", fallback=0.5)

    def set_music_volume(self, volume):
        self._config["Audio"]["music_volume"] = str(volume)
        self._save()

    def get_menu_music_volume(self):
        return self._config.getfloat("Audio", "menu_music_volume", fallback=0.5)

    def set_menu_music_volume(self, volume):
        self._config["Audio"]["menu_music_volume"] = str(volume)
        self._save()

    def get_dungeon_music_volume(self):
        return self._config.getfloat("Audio", "dungeon_music_volume", fallback=0.5)

    def set_dungeon_music_volume(self, volume):
        self._config["Audio"]["dungeon_music_volume"] = str(volume)
        self._save()

    def get_sfx_volume(self):
        return self._config.getfloat("Audio", "sfx_volume", fallback=1.0)

    def set_sfx_volume(self, volume):
        self._config["Audio"]["sfx_volume"] = str(volume)
        self._save()

    def get(self, section, key, fallback=None):
        return self._config.get(section, key, fallback=fallback)

    def get_display(self):
        return self._config.getint("Display", "display", fallback=0)

    def set_display(self, display_index):
        num_displays = self.get_num_displays()
        if 0 <= display_index < num_displays:
            self._config["Display"]["display"] = str(display_index)
            self._save()

    def get_num_displays(self):
        return pygame.display.get_num_displays()

    def get_display_resolution(self, display_index=None):
        if display_index is None:
            display_index = self.get_display()
        desktop_sizes = pygame.display.get_desktop_sizes()
        if 0 <= display_index < len(desktop_sizes):
            return desktop_sizes[display_index]
        return desktop_sizes[0] if desktop_sizes else (1920, 1080)

    def get_language(self):
        return self._config.get("Game", "language", fallback="ru")

    def set_language(self, locale):
        if "Game" not in self._config:
            self._config["Game"] = {}
        if locale in ["en", "ru"]:
            self._config["Game"]["language"] = locale
            self._save()

    def get_font(self):
        return self._config.get("Game", "font", fallback="0")

    def set_font(self, font_value):
        if "Game" not in self._config:
            self._config["Game"] = {}

        font_str = str(font_value)

        if font_str.isdigit():
            idx = int(font_str)
            if 0 <= idx <= 2:
                self._config["Game"]["font"] = font_str
                self._save()
        else:
            self._config["Game"]["font"] = font_str
            self._save()
