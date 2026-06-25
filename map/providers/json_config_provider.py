from utils.config_loader import ConfigLoader


class JsonConfigProvider:
    def get(self, name: str) -> dict:
        return ConfigLoader.get(name)

    def get_realm_config(self, realm_id: str) -> dict:
        all_configs = ConfigLoader.get("realm_config")
        return all_configs.get(realm_id, {})

    def get_room_templates(self) -> dict:
        return ConfigLoader.get("room_templates")

    def get_room_variants(self) -> dict:
        return ConfigLoader.get("room_variants")
