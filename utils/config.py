import configparser
import os

CONFIG_FILE = "../config.ini"

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

    screen_w, screen_h = get_screen_resolution()
    config["Display"]["screen_width"] = str(screen_w)
    config["Display"]["screen_height"] = str(screen_h)

    if "mode" not in config["Window"]:
        config["Window"]["mode"] = "fullscreen"

    if "width" not in config["Window"]:
        config["Window"]["width"] = str(screen_w)
        config["Window"]["height"] = str(screen_h)

    if "scale" not in config["Window"]:
        config["Window"]["scale"] = str(calculate_initial_scale(screen_w, screen_h))

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
    width = config.getint("Display", "screen_width", fallback=1920)
    height = config.getint("Display", "screen_height", fallback=1080)
    return width, height


def get_scale():
    return config.getfloat("Window", "scale", fallback=1.0)


def set_scale(scale):
    config["Window"]["scale"] = str(scale)
    save_config()


def calculate_initial_scale(screen_w, screen_h):
    max_room_height_tiles = 16
    from utils.settings import TILESIZE

    max_room_height_px = max_room_height_tiles * TILESIZE
    scale = screen_h / max_room_height_px
    return scale
