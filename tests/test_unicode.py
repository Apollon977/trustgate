import unittest

from trustgate.unicode import find_hidden


def tags(s):
    return "".join(chr(0xE0000 + ord(c)) for c in s)


class HiddenUnicodeTests(unittest.TestCase):
    def test_clean_text(self):
        self.assertEqual(find_hidden('{"a": "plain ascii", "b": "café ✓"}'), [])

    def test_tag_characters_are_decoded(self):
        runs = find_hidden("line one\nvisible" + tags("hidden note") + " text")
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].kind, "tags")
        self.assertEqual(runs[0].line, 2)
        self.assertEqual(runs[0].column, 8)
        self.assertIn("hidden note", runs[0].detail)

    def test_bidi_and_zero_width(self):
        runs = find_hidden("a\u202eb\u200b\u200bc")
        self.assertEqual([r.kind for r in runs], ["bidi", "zero-width"])
        self.assertEqual(runs[1].count, 2)
        self.assertIn("U+200B", runs[1].detail)

    def test_leading_bom_ignored_but_inner_bom_reported(self):
        self.assertEqual(find_hidden("\ufeffok"), [])
        self.assertEqual(len(find_hidden("o\ufeffk")), 1)


if __name__ == "__main__":
    unittest.main()
