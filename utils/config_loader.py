import json
from pathlib import Path


def _lists_to_tuples(data):
    if isinstance(data, dict):
        return {k: _lists_to_tuples(v) for k, v in data.items()}
    if isinstance(data, list):
        if all(isinstance(x, (int, float)) for x in data):
            return tuple(data)
        return [_lists_to_tuples(v) for v in data]
    return data


def _convert_int_keys(data):
    if isinstance(data, dict):
        items = {}
        for k, v in data.items():
            items[k] = _convert_int_keys(v)
        if items and all(isinstance(k, str) and k.lstrip('-').isdigit() for k in items):
            return {int(k): v for k, v in items.items()}
        return items
    if isinstance(data, list):
        return [_convert_int_keys(v) for v in data]
    return data


class ConfigLoader:
    _configs: dict[str, dict] = {}

    @classmethod
    def load_all(cls, config_dir: str = "configs") -> None:
        cls._configs = {}
        base = Path(config_dir)
        for path in sorted(base.glob("*.json")):
            name = path.stem
            with open(path) as f:
                data = json.load(f)
            data = _lists_to_tuples(data)
            data = _convert_int_keys(data)
            cls._configs[name] = data

    @classmethod
    def get(cls, name: str) -> dict:
        if name not in cls._configs:
            raise KeyError(f"Config '{name}' not loaded")
        return cls._configs[name]

    @classmethod
    def get_all(cls) -> dict[str, dict]:
        return dict(cls._configs)
