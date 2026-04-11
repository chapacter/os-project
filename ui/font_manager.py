import os

import pygame

from ui.locale_manager import locale_manager

FONTS = {
    0: {"name": "retro", "path": "assets/Retro-Gaming.ttf"},
    1: {"name": "system", "path": None},
    2: {"name": "adys", "path": "assets/ADYS.ttf"},
}

DEFAULT_FONT_KEY = "0"


class FontManager:
    _fonts_cache = {}
    _current_font_key = DEFAULT_FONT_KEY
    _current_font = None

    @classmethod
    def init(cls, locale=None, font=None):
        locale_manager.init(locale)
        cls.set_font(font or DEFAULT_FONT_KEY)

    @classmethod
    def set_font(cls, font_value):
        font_str = str(font_value)

        if font_str.isdigit():
            idx = int(font_str)
            if 0 <= idx <= 2:
                cls._current_font_key = font_str
            else:
                cls._current_font_key = DEFAULT_FONT_KEY
        else:
            cls._current_font_key = font_str

        cls._fonts_cache.clear()

        font_info = cls._get_font_info(cls._current_font_key)
        if font_info:
            path = font_info.get("path")
            if path is None:
                cls._current_font = pygame.font.Font(None, 24)
            else:
                try:
                    cls._current_font = pygame.font.Font(path, 24)
                except Exception:
                    cls._current_font = pygame.font.Font(None, 24)
        else:
            try:
                if os.path.exists(font_str):
                    cls._current_font = pygame.font.Font(font_str, 24)
                else:
                    cls._current_font = pygame.font.Font(None, 24)
            except Exception:
                cls._current_font = pygame.font.Font(None, 24)

        cls._fonts_cache.clear()

    @classmethod
    def _get_font_info(cls, font_key):
        if font_key.isdigit():
            return FONTS.get(int(font_key))
        for info in FONTS.values():
            if info["name"] == font_key:
                return info
        return None

    @classmethod
    def get_font_key(cls):
        return cls._current_font_key

    @classmethod
    def get_font_name(cls):
        info = cls._get_font_info(cls._current_font_key)
        if info:
            return info["name"]
        return cls._current_font_key

    @classmethod
    def get_font(cls, size):
        if size not in cls._fonts_cache:
            font_key = cls._current_font_key
            font_info = cls._get_font_info(font_key)
            if font_info:
                path = font_info.get("path")
                if path is None:
                    cls._fonts_cache[size] = pygame.font.Font(None, size)
                else:
                    cls._fonts_cache[size] = pygame.font.Font(path, size)
            else:
                try:
                    if os.path.exists(font_key):
                        cls._fonts_cache[size] = pygame.font.Font(font_key, size)
                    else:
                        cls._fonts_cache[size] = pygame.font.Font(None, size)
                except Exception:
                    cls._fonts_cache[size] = pygame.font.Font(None, size)
        return cls._fonts_cache[size]

    @classmethod
    def set_locale(cls, locale):
        locale_manager.set_locale(locale)

    @classmethod
    def get_locale(cls):
        return locale_manager.get_locale()

    @classmethod
    def get_supported_locales(cls):
        return locale_manager.get_supported_locales()

    @classmethod
    def t(cls, key):
        return locale_manager.t(key)

    @classmethod
    def render(
            cls, text, size, color, shadow=None, outline=None, align="left", antialias=True
    ):
        font = cls.get_font(size)

        result_surf = None

        if outline:
            if isinstance(outline, tuple):
                outline_color = outline
            else:
                outline_color = (0, 0, 0)

            outline_surf = font.render(text, antialias, outline_color)
            text_surf = font.render(text, antialias, color)

            ow, oh = outline_surf.get_size()

            result_surf = pygame.Surface((ow + 2, oh + 2), pygame.SRCALPHA)
            result_surf.blit(outline_surf, (1, 0))
            result_surf.blit(outline_surf, (0, 1))
            result_surf.blit(outline_surf, (2, 1))
            result_surf.blit(outline_surf, (1, 2))
            result_surf.blit(text_surf, (1, 1))
        else:
            result_surf = font.render(text, antialias, color)

        if shadow:
            if shadow is True:
                shadow_color = (0, 0, 0)
            else:
                shadow_color = shadow

            shadow_surf = cls._render_shadow_layer(text, size, shadow_color)

            final_w = max(shadow_surf.get_width(), result_surf.get_width())
            final_h = max(shadow_surf.get_height(), result_surf.get_height())

            combined = pygame.Surface((final_w, final_h), pygame.SRCALPHA)
            combined.blit(shadow_surf, (0, 0))
            combined.blit(result_surf, (0, 0))
            result_surf = combined

        return result_surf

    @classmethod
    def _render_shadow_layer(cls, text, size, color):
        font = cls.get_font(size)
        return font.render(text, True, color)

    @classmethod
    def render_shadow(cls, text, size, color, shadow_offset=2, shadow_color=(0, 0, 0)):
        font = cls.get_font(size)

        text_surf = font.render(text, True, color)
        shadow_surf = font.render(text, True, shadow_color)

        tw, th = text_surf.get_size()
        sw, sh = shadow_surf.get_size()

        result = pygame.Surface(
            (sw + shadow_offset, sh + shadow_offset), pygame.SRCALPHA
        )
        result.blit(shadow_surf, (shadow_offset, shadow_offset))
        result.blit(text_surf, (0, 0))

        return result

    @classmethod
    def render_outline(cls, text, size, color, outline_color=(0, 0, 0), border=1):
        font = cls.get_font(size)

        text_surf = font.render(text, True, color)

        tw, th = text_surf.get_size()
        bw, bh = tw + border * 2, th + border * 2

        result = pygame.Surface((bw, bh), pygame.SRCALPHA)

        for dx in range(-border, border + 1):
            for dy in range(-border, border + 1):
                if dx * dx + dy * dy <= border * border:
                    outline_surf = font.render(text, True, outline_color)
                    result.blit(outline_surf, (dx + border, dy + border))

        result.blit(text_surf, (border, border))

        return result

    @classmethod
    def render_glow(cls, text, size, color, glow_color=(255, 215, 0), intensity=2):
        font = cls.get_font(size)
        antialias = True

        text_surf = font.render(text, antialias, color)

        tw, th = text_surf.get_size()
        glow_radius = size // 4

        result = pygame.Surface(
            (tw + glow_radius * 2 + glow_radius, th + glow_radius * 2 + glow_radius),
            pygame.SRCALPHA,
        )

        for i in range(intensity, 0, -1):
            glow_surf = font.render(text, antialias, glow_color)
            scaled = pygame.transform.scale(
                glow_surf, (tw + i * glow_radius, th + i * glow_radius)
            )
            scaled_scaled = pygame.transform.smoothscale(
                scaled, (tw + glow_radius * 2, th + glow_radius * 2)
            )
            result.blit(
                scaled_scaled,
                (
                    glow_radius - i * glow_radius // 2,
                    glow_radius - i * glow_radius // 2,
                ),
            )

        result.blit(text_surf, (glow_radius, glow_radius))

        return result

    @classmethod
    def get_text_size(cls, text, size):
        font = cls.get_font(size)
        return font.size(text)


font_manager = FontManager()
