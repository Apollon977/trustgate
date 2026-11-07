import unittest

from trustgate.textutil import line_of, load_jsonc, shorten, strip_jsonc


class JsoncTests(unittest.TestCase):
    def test_comments_and_trailing_commas(self):
        text = """{
  // line comment
  "a": "http://keep//this", /* block
  comment */ "b": [1, 2,],
}"""
        self.assertEqual(load_jsonc(text), {"a": "http://keep//this", "b": [1, 2]})

    def test_escaped_quotes_inside_strings(self):
        self.assertEqual(load_jsonc('{"cmd": "echo \\"/* not a comment */\\"",}'),
                         {"cmd": 'echo "/* not a comment */"'})

    def test_bom_is_ignored(self):
        self.assertEqual(load_jsonc('\ufeff{"x": 1}'), {"x": 1})

    def test_newlines_preserved(self):
        text = '{\n/* a\nb */\n"k": 1}'
        self.assertEqual(strip_jsonc(text).count("\n"), text.count("\n"))

    def test_invalid_raises(self):
        with self.assertRaises(ValueError):
            load_jsonc("{nope}")

    def test_line_of_and_shorten(self):
        self.assertEqual(line_of("a\nb\nc", "c"), 3)
        self.assertEqual(line_of("a", "zzz", 7), 7)
        self.assertEqual(shorten("x" * 200, 10), "xxxxxxx...")
        self.assertEqual(shorten("a \n  b"), "a b")


if __name__ == "__main__":
    unittest.main()
