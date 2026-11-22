
import unittest

from app.audit.router import sanitize_csv_cell


class AuditCsvSanitizationTests(unittest.TestCase):

    def test_formula_prefixes_are_sanitized(self):
        dangerous_values = [
            "=SUM(1,2)",
            "+SUM(1,2)",
            "-1+2",
            "@SUM(1,2)",
            "  =SUM(1,2)",
            "\t=SUM(1,2)",
            "\n=SUM(1,2)",
        ]

        for value in dangerous_values:
            with self.subTest(value=value):
                self.assertTrue(
                    sanitize_csv_cell(value).startswith("'")
                )

    def test_normal_values_are_unchanged(self):
        normal_values = [
            "student@example.com",
            "USER_BANNED",
            "192.168.1.1",
            "Normal user agent",
        ]

        for value in normal_values:
            with self.subTest(value=value):
                self.assertEqual(
                    sanitize_csv_cell(value),
                    value,
                )

    def test_none_becomes_empty_string(self):
        self.assertEqual(sanitize_csv_cell(None), "")

    def test_empty_string_remains_empty(self):
        self.assertEqual(sanitize_csv_cell(""), "")


if __name__ == "__main__":
    unittest.main()
