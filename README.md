# IRMotionExtraction
An IR camera designed to detect motion in blood vessels 

## Configuration database

`ConfigDb` provides a shared in-memory configuration dictionary with JSON
persistence and per-key update callbacks:

```python
from motion_extraction.ConfigDb import ConfigDb

config = ConfigDb.get_instance()
config.load_from_json("motion_extraction/configs/defaults.json")
config.register_callback("input", lambda key, value: print(key, value))
config.update_value("input", 1)
config.save_to_json()
```

Use `create_value(key, value)` to add a new key and `remove_value(key)` to
remove one. Updating or removing a missing key raises `KeyError`. Callbacks are
invoked as `callback(key, new_value)` after an update.
