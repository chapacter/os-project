import configparser
import os

CONFIG_FILE = "config.ini"

config = configparser.ConfigParser()

WINDOW_MODES = ["fullscreen", "borderless", "windowed"]


def get_screen_resolution():
    import pygame

    info = pygame.display.Info()
    return info.current_w, info.current_h


def load_config():
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    else:
        config["Window"] = {}
        config["Display"] = {}
        config["Audio"] = {}
        config["Game"] = {}

    if "Window" not in config:
        config["Window"] = {}
    if "Display" not in config:
        config["Display"] = {}
    if "Audio" not in config:
        config["Audio"] = {}
    if "Game" not in config:
        config["Game"] = {}

    screen_w, screen_h = get_screen_resolution()
    config["Display"]["screen_width"] = str(screen_w)
    config["Display"]["screen_height"] = str(screen_h)

    if "display" not in config["Display"]:
        config["Display"]["display"] = "0"

    if "mode" not in config["Window"]:
        config["Window"]["mode"] = "fullscreen"

    if "width" not in config["Window"]:
        config["Window"]["width"] = str(screen_w)
        config["Window"]["height"] = str(screen_h)

    if "scale" not in config["Window"]:
        config["Window"]["scale"] = str(calculate_initial_scale(screen_w, screen_h))

    if "music_volume" not in config["Audio"]:
        config["Audio"]["music_volume"] = "0.5"
    if "sfx_volume" not in config["Audio"]:
        config["Audio"]["sfx_volume"] = "0.5"

    if "Game" not in config:
        config["Game"] = {}
    if "language" not in config["Game"]:
        config["Game"]["language"] = "ru"
    if "font" not in config["Game"]:
        config["Game"]["font"] = "0"

    save_config()
    return config


def save_config():
    with open(CONFIG_FILE, "w") as f:
        config.write(f)


def get_window_mode():
    return config.get("Window", "mode", fallback="fullscreen")


def set_window_mode(mode):
    if mode in WINDOW_MODES:
        config["Window"]["mode"] = mode
        save_config()


def get_window_size():
    width = config.getint("Window", "width", fallback=1280)
    height = config.getint("Window", "height", fallback=720)
    return width, height


def set_window_size(width, height):
    config["Window"]["width"] = str(width)
    config["Window"]["height"] = str(height)
    save_config()


def get_next_window_mode():
    current = get_window_mode()
    idx = WINDOW_MODES.index(current)
    next_mode = WINDOW_MODES[(idx + 1) % len(WINDOW_MODES)]
    return next_mode


def get_screen_size():
    try:
        return get_display_resolution()
    except Exception:
        width = config.getint("Display", "screen_width", fallback=1920)
        height = config.getint("Display", "screen_height", fallback=1080)
        return width, height


def get_scale():
    return config.getfloat("Window", "scale", fallback=1.0)


def set_scale(scale):
    config["Window"]["scale"] = str(scale)
    save_config()


def get_music_volume():
    return config.getfloat("Audio", "music_volume", fallback=0.7)


def set_music_volume(volume):
    config["Audio"]["music_volume"] = str(volume)
    save_config()


def get_sfx_volume():
    return config.getfloat("Audio", "sfx_volume", fallback=0.8)


def set_sfx_volume(volume):
    config["Audio"]["sfx_volume"] = str(volume)
    save_config()


def calculate_initial_scale(screen_w, screen_h):
    max_room_height_tiles = 16
    from utils.settings import TILESIZE

    max_room_height_px = max_room_height_tiles * TILESIZE
    scale = screen_h / max_room_height_px
    return scale


def get(section, key, fallback=None):
    return config.get(section, key, fallback=fallback)


def get_display():
    return config.getint("Display", "display", fallback=0)


def set_display(display_index):
    num_displays = get_num_displays()
    if 0 <= display_index < num_displays:
        config["Display"]["display"] = str(display_index)
        save_config()


def get_num_displays():
    import pygame

    return pygame.display.get_num_displays()


def get_display_resolution(display_index=None):
    import pygame

    if display_index is None:
        display_index = get_display()
    desktop_sizes = pygame.display.get_desktop_sizes()
    if 0 <= display_index < len(desktop_sizes):
        return desktop_sizes[display_index]
    return desktop_sizes[0] if desktop_sizes else (1920, 1080)


def get_language():
    return config.get("Game", "language", fallback="ru")


def set_language(locale):
    if "Game" not in config:
        config["Game"] = {}
    if locale in ["en", "ru"]:
        config["Game"]["language"] = locale
        save_config()


def get_font():
    return config.get("Game", "font", fallback="0")


def set_font(font_value):
    if "Game" not in config:
        config["Game"] = {}

    font_str = str(font_value)

    if font_str.isdigit():
        idx = int(font_str)
        if 0 <= idx <= 2:
            config["Game"]["font"] = font_str
            save_config()
    else:
        config["Game"]["font"] = font_str
        save_config()
