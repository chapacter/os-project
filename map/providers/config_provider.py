from typing import Optional, Protocol


class ConfigProvider(Protocol):
    def get(self, name: str) -> Optional[dict]:
        ...

    def get_realm_config(self, realm_id: str) -> Optional[dict]:
        ...

    def get_room_templates(self) -> dict:
        ...

    def get_room_variants(self) -> dict:
        ...
