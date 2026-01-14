import json
import os
import re
from typing import Any


class Cache:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        os.makedirs(self.root_dir, exist_ok=True)

    def safe_key(self, s: str) -> str:
        # filesystem-safe key
        s = s.strip().lower()
        s = re.sub(r"[^a-z0-9]+", "_", s)
        return s[:180]

    def path(self, rel: str) -> str:
        full = os.path.join(self.root_dir, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        return full

    def get_json(self, rel: str, default=None):
        p = self.path(rel)
        if not os.path.exists(p):
            return default
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_json(self, rel: str, obj: Any):
        p = self.path(rel)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)

    def load_json_file(self, filepath: str, default=None):
        if not os.path.exists(filepath):
            return default
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
