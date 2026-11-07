import contextlib
import io
import json
import os
import tempfile
import unittest

from trustgate.cli import main

from helpers import TempRepo

REPO = {
    ".vscode/tasks.json": {"tasks": [{"label": "x", "command": "node x.js", "runOptions": {"runOn": "folderOpen"}}]},
    "package.json": {"scripts": {"prepare": "husky"}},
}


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        try:
            code = main(argv)
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue()


class CliTests(unittest.TestCase):
    def test_text_and_exit_codes(self):
        with TempRepo(REPO) as root:
            code, out = run(["scan", str(root), "--no-color"])
            self.assertEqual(code, 1)
            self.assertIn("TG100 vscode-folder-open-task", out)
            self.assertIn("Summary: 1 high, 1 low", out)
            code, _ = run(["scan", str(root), "--fail-on", "critical"])
            self.assertEqual(code, 0)

    def test_json(self):
        with TempRepo(REPO) as root:
            code, out = run(["scan", str(root), "-f", "json", "--min-severity", "medium"])
        doc = json.loads(out)
        self.assertEqual(code, 1)
        self.assertEqual(doc["summary"]["high"], 1)
        self.assertEqual([f["rule"] for f in doc["findings"]], ["TG100"])

    def test_sarif_to_file(self):
        with TempRepo(REPO) as root, tempfile.TemporaryDirectory() as out_dir:
            target = os.path.join(out_dir, "r.sarif")
            run(["scan", str(root), "-f", "sarif", "-o", target])
            with open(target, encoding="utf-8") as fh:
                doc = json.load(fh)
        self.assertEqual(doc["version"], "2.1.0")
        run_ = doc["runs"][0]
        ids = [r["id"] for r in run_["tool"]["driver"]["rules"]]
        for res in run_["results"]:
            self.assertEqual(ids[res["ruleIndex"]], res["ruleId"])
            self.assertIn("trustgate/v1", res["partialFingerprints"])
        self.assertEqual({r["level"] for r in run_["results"]}, {"error", "note"})

    def test_usage_errors(self):
        self.assertEqual(run(["scan", "/definitely/not/here"])[0], 2)
        self.assertEqual(run(["scan", ".", "--ignore", "TG999"])[0], 2)
        self.assertEqual(run(["scan", ".", "--fail-on", "nope"])[0], 2)
        self.assertEqual(run([])[0], 2)

    def test_rules_listing(self):
        code, out = run(["rules"])
        self.assertEqual(code, 0)
        self.assertIn("TG500", out)

    def test_home_scan(self):
        files = {".claude/settings.json": {"hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": "x"}]}]}},
                 ".config/Code/User/settings.json": {"terminal.integrated.env.linux": {"BASH_ENV": "/tmp/x"}}}
        with TempRepo(files) as home:
            from trustgate.scanner import scan_home
            result = scan_home(str(home))
        self.assertEqual(sorted(f.rule_id for f in result.findings), ["TG102", "TG200"])


if __name__ == "__main__":
    unittest.main()
