import json
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, Union


Callback = Callable[[str, Any], None]
ConfigPath = Union[str, Path]


class ConfigDb:
    _instance: Optional["ConfigDb"] = None
    _instance_lock = Lock()

    def __new__(cls) -> "ConfigDb":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self) -> None:
        with self._instance_lock:
            if getattr(self, "_initialized", False):
                return

            self.values: Dict[str, Any] = {}
            self.callbacks: Dict[str, List[Callback]] = {}
            self.file_path: Optional[Path] = None
            self._lock = Lock()
            self._initialized = True

    @staticmethod
    def get_instance() -> "ConfigDb":
        return ConfigDb()

    def create_value(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self.values:
                raise KeyError(f"Configuration key already exists: {key}")
            self.values[key] = value
            self.callbacks.setdefault(key, [])

    def remove_value(self, key: str) -> Any:
        with self._lock:
            if key not in self.values:
                raise KeyError(f"Configuration key does not exist: {key}")
            value = self.values.pop(key)
            self.callbacks.pop(key, None)
            return value

    def update_value(self, key: str, value: Any) -> None:
        with self._lock:
            if key not in self.values:
                raise KeyError(f"Configuration key does not exist: {key}")
            self.values[key] = value
            callbacks = tuple(self.callbacks.get(key, ()))

        for callback in callbacks:
            callback(key, value)

    def register_callback(self, key: str, callback: Callback) -> None:
        if not callable(callback):
            raise TypeError("callback must be callable")

        with self._lock:
            self.values.setdefault(key, None)
            self.callbacks.setdefault(key, []).append(callback)

    def load_from_json(self, path: ConfigPath) -> None:
        config_path = Path(path)
        with config_path.open("r", encoding="utf-8") as config_file:
            loaded_values = json.load(config_file)

        if not isinstance(loaded_values, dict):
            raise ValueError("The JSON configuration must contain an object")

        with self._lock:
            for key in self.callbacks:
                loaded_values.setdefault(key, None)
            self.values.clear()
            self.values.update(loaded_values)
            for key in self.values:
                self.callbacks.setdefault(key, [])
            self.file_path = config_path

    def save_to_json(self, path: Optional[ConfigPath] = None) -> None:
        with self._lock:
            config_path = Path(path) if path is not None else self.file_path
            if config_path is None:
                raise ValueError("No config file path has been set")
            values = self.values.copy()

        with config_path.open("w", encoding="utf-8") as config_file:
            json.dump(values, config_file, indent=2)
            config_file.write("\n")

        with self._lock:
            self.file_path = config_path
