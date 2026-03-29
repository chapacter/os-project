import os

import pygame

from utils.config import (
    get_music_volume,
    get_sfx_volume,
    set_music_volume,
    set_sfx_volume,
)


class AudioManager:
    def __init__(self):
        self.initialized = False
        self.music_volume = 0.5
        self.sfx_volume = 0.5

        self.sounds = {}
        self.music_playing = False
        self.current_music = None

    def sync_from_config(self):
        self.music_volume = get_music_volume()
        self.sfx_volume = get_sfx_volume()
        if self.initialized:
            pygame.mixer.music.set_volume(self.music_volume)
            for sound in self.sounds.values():
                sound.set_volume(self.sfx_volume)

    def init(self, frequency=44100, size=-16, channels=2, buffer=512):
        try:
            pygame.mixer.init(
                frequency=frequency, size=size, channels=channels, buffer=buffer
            )
            self.initialized = True
            print("Audio initialized successfully")
        except pygame.error as e:
            print(f"Failed to initialize audio: {e}")
            self.initialized = False

    def load_sound(self, name, filepath):
        if not self.initialized:
            print(f"[DEBUG] Cannot load sound '{name}': mixer not initialized")
            return None

        if not os.path.exists(filepath):
            print(f"[DEBUG] Sound file not found: {filepath}")
            return None

        try:
            sound = pygame.mixer.Sound(filepath)
            sound.set_volume(self.sfx_volume)
            self.sounds[name] = sound
            print(f"[DEBUG] Loaded sound: {name} -> {filepath}")
            return sound
        except pygame.error as e:
            print(f"[DEBUG] Failed to load sound {name}: {e}")
            return None

    def play_sound(self, name, loops=0, fade_ms=0):
        if not self.initialized:
            return

        if name in self.sounds:
            try:
                print(f"[DEBUG] Playing sound: {name}")
                self.sounds[name].play(loops=loops, fade_ms=fade_ms)
            except pygame.error as e:
                print(f"[DEBUG] Failed to play sound {name}: {e}")
        else:
            print(f"[DEBUG] Sound not found: {name}")

    def stop_sound(self, name):
        if name in self.sounds:
            self.sounds[name].stop()

    def stop_all_sounds(self):
        for sound in self.sounds.values():
            sound.stop()

    def set_sfx_volume(self, volume):
        self.sfx_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.sfx_volume)

    def adjust_sfx_volume(self, delta):
        new_volume = max(0.0, min(1.0, self.sfx_volume + delta))
        self.sfx_volume = new_volume
        set_sfx_volume(new_volume)
        for sound in self.sounds.values():
            sound.set_volume(new_volume)

    def set_music_volume(self, volume):
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)

    def adjust_music_volume(self, delta):
        new_volume = max(0.0, min(1.0, self.music_volume + delta))
        self.music_volume = new_volume
        set_music_volume(new_volume)
        pygame.mixer.music.set_volume(new_volume)

    def load_music(self, filepath):
        if not self.initialized:
            return False

        if not os.path.exists(filepath):
            print(f"Music file not found: {filepath}")
            return False

        try:
            pygame.mixer.music.load(filepath)
            self.current_music = filepath
            return True
        except pygame.error as e:
            print(f"Failed to load music: {e}")
            return False

    def play_music(self, loops=-1, start=0.0, fade_ms=0):
        if not self.initialized or not self.current_music:
            return

        try:
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(loops=loops, start=start, fade_ms=fade_ms)
            self.music_playing = True
        except pygame.error as e:
            print(f"Failed to play music: {e}")

    def stop_music(self, fade_ms=0):
        if not self.initialized:
            return

        try:
            if fade_ms > 0:
                pygame.mixer.music.fadeout(fade_ms)
            else:
                pygame.mixer.music.stop()
            self.music_playing = False
        except pygame.error as e:
            print(f"Failed to stop music: {e}")

    def pause_music(self):
        if self.initialized and self.music_playing:
            pygame.mixer.music.pause()

    def unpause_music(self):
        if self.initialized and self.music_playing:
            pygame.mixer.music.unpause()

    def set_music_volume(self, volume):
        self.music_volume = max(0.0, min(1.0, volume))
        if self.initialized:
            pygame.mixer.music.set_volume(self.music_volume)

    def is_music_playing(self):
        if self.initialized:
            return pygame.mixer.music.get_busy()
        return False

    def get_music_position(self):
        if self.initialized:
            return pygame.mixer.music.get_pos()
        return 0


class SpatialAudio:
    def __init__(self, audio_manager):
        self.audio = audio_manager
        self.listener_position = (0, 0)

    def set_listener_position(self, x, y):
        self.listener_position = (x, y)

    def calculate_panning(self, source_x):
        if not self.audio.initialized:
            return 0.5, 0.5

        screen_width = 1900
        normalized_x = source_x / screen_width

        left_volume = max(0, 1 - normalized_x * 2)
        right_volume = (
                max(0, normalized_x * 2 - 1) + (1 - abs(normalized_x - 0.5) * 2) * 0.5
        )

        return left_volume, right_volume

    def calculate_distance_volume(self, source_x, source_y):
        import math

        listener_x, listener_y = self.listener_position
        distance = math.sqrt(
            (source_x - listener_x) ** 2 + (source_y - listener_y) ** 2
        )

        max_distance = 500
        volume = max(0, 1 - distance / max_distance)

        return volume

    def play_spatial_sound(self, sound_name, source_x, source_y):
        if sound_name not in self.audio.sounds:
            return

        distance_volume = self.calculate_distance_volume(source_x, source_y)
        left_vol, right_vol = self.calculate_panning(source_x)

        sound = self.audio.sounds[sound_name]
        sound.set_volume(distance_volume * self.audio.sfx_volume)


audio_manager = AudioManager()


def init_audio():
    audio_manager.init()


def load_sound(name, filepath):
    return audio_manager.load_sound(name, filepath)


def play_sound(name, loops=0, fade_ms=0):
    audio_manager.play_sound(name, loops, fade_ms)


def load_music(filepath):
    return audio_manager.load_music(filepath)


def play_music(loops=-1, start=0.0, fade_ms=0):
    audio_manager.play_music(loops, start, fade_ms)


def stop_music(fade_ms=0):
    audio_manager.stop_music(fade_ms)
