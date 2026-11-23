"""Перевірка JSON-профілів у protocols/ за основними правилами schema.json (без сторонніх бібліотек)."""
import json
import re
import unittest
from pathlib import Path

PROTOCOLS = Path(__file__).resolve().parents[1] / "protocols"
CMD_RE = re.compile(r"^0x[0-9A-Fa-f]{2}$")
VIN_RE = re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b")


def profiles():
    return sorted(p for p in PROTOCOLS.rglob("*.json") if p.name != "schema.json")


class ProfilesTest(unittest.TestCase):
    def test_schema_is_json(self):
        json.loads((PROTOCOLS / "schema.json").read_text(encoding="utf-8"))

    def test_has_profiles(self):
        self.assertTrue(profiles())

    def test_profiles_valid(self):
        schema = json.loads((PROTOCOLS / "schema.json").read_text(encoding="utf-8"))
        vendors = schema["properties"]["canbox"]["properties"]["vendor"]["enum"]
        statuses = schema["properties"]["status"]["enum"]
        for path in profiles():
            with self.subTest(profile=path.relative_to(PROTOCOLS).as_posix()):
                raw = path.read_text(encoding="utf-8")
                self.assertIsNone(VIN_RE.search(raw), "профіль схожий на такий, що містить VIN")
                data = json.loads(raw)
                for key in schema["required"]:
                    self.assertIn(key, data)
                self.assertEqual(data["schema_version"], 1)
                for key in ("make", "model", "years"):
                    self.assertIsInstance(data["vehicle"][key], str)
                self.assertIn(data["canbox"]["vendor"], vendors)
                self.assertIn(data["status"], statuses)
                self.assertIsInstance(data["frames"], list)
                for frame in data["frames"]:
                    self.assertRegex(frame["cmd_type"], CMD_RE)
                    self.assertIsInstance(frame["name"], str)
                    for field in frame["fields"]:
                        self.assertIsInstance(field["name"], str)
                        self.assertGreaterEqual(field["byte"], 0)
                        if "bit" in field:
                            self.assertIn(field["bit"], range(8))


if __name__ == "__main__":
    unittest.main()
