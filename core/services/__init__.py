from core.event_bus import EventBus
from core.services.audio import AudioService
from core.services.config import ConfigService
from core.services.font import FontService
from core.services.save import SaveService


class ServiceContainer:
    def __init__(self):
        self.config = ConfigService()
        self.audio = AudioService()
        self.font = FontService()
        self.save = SaveService()
        self.event_bus = EventBus()

    def init_all(self):
        self.config.init()
        self.font.init(self.config.get_language(), self.config.get_font())
        self.audio.set_config(self.config)
        self.audio.init()
        self.audio.sync_from_config()
        self.save.init()

    def shutdown(self):
        pass
