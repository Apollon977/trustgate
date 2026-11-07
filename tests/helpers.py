import json
import tempfile
from pathlib import Path


class TempRepo:
    """Context manager that materialises {relative_path: content} into a temp dir."""

    def __init__(self, files):
        self.files = files

    def __enter__(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        for rel, content in self.files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if not isinstance(content, str):
                content = json.dumps(content, indent=2)
            path.write_text(content, encoding="utf-8")
        return root

    def __exit__(self, *exc):
        self._tmp.cleanup()


def rules_of(result):
    return [f.rule_id for f in result.findings]
