import ast
import re
import unittest
from pathlib import Path

import trustgate
from trustgate.models import RULES

ROOT = Path(__file__).resolve().parent.parent


class MetaTests(unittest.TestCase):
    def test_versions_match(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn(f'version = "{trustgate.__version__}"', pyproject)
        self.assertIn(f"## [{trustgate.__version__}]", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))

    def test_every_rule_is_documented(self):
        docs = (ROOT / "docs" / "rules.md").read_text(encoding="utf-8")
        documented = set(re.findall(r"^\| (TG\d{3}) \|", docs, re.M))
        self.assertEqual(documented, set(RULES))

    def test_every_rule_has_a_test(self):
        test_files = [
            p for p in (ROOT / "tests").glob("test_*.py") if p.name not in ("test_meta.py", "test_cli.py")
        ]
        test_text = "\n".join(p.read_text(encoding="utf-8") for p in test_files)
        untested = [rule_id for rule_id in sorted(RULES) if rule_id not in test_text]
        self.assertEqual(untested, [], f"Rules with no test asserting their id: {untested}")

    def test_source_parses_as_python_3_10(self):
        for path in (ROOT / "trustgate").rglob("*.py"):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path), feature_version=(3, 10))


if __name__ == "__main__":
    unittest.main()
