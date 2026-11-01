import importlib.util
import pathlib
import unittest

_PATH = pathlib.Path(__file__).resolve().parent.parent / "oh-my-timer.py"
_spec = importlib.util.spec_from_file_location("oh_my_timer", _PATH)
omt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(omt)


class ParseDurationTest(unittest.TestCase):
    def test_valid(self):
        cases = {
            "25": 1500,
            "1": 60,
            "90s": 90,
            "25m": 1500,
            "1m30s": 90,
            "1h": 3600,
            "1h5m": 3900,
            "1h0m10s": 3610,
            " 10S ": 10,
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(omt.parse_duration(text), expected)

    def test_invalid(self):
        for text in ["", "abc", "10x", "m", "1.5m", "-5", "30s1m", "5 m"]:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    omt.parse_duration(text)

    def test_zero(self):
        for text in ["0", "0s", "0m0s"]:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    omt.parse_duration(text)


class FormatAndStateTest(unittest.TestCase):
    def test_format(self):
        self.assertEqual(omt.format_time(1500), "25:00")
        self.assertEqual(omt.format_time(5), "00:05")
        self.assertEqual(omt.format_time(3661), "1:01:01")

    def test_state_flow(self):
        t = omt.Timer(60)
        self.assertEqual(t.menu(), ["Start", "Quit"])
        self.assertTrue(t.activate())  # Start
        self.assertEqual(t.state, omt.RUNNING)
        self.assertEqual(t.menu(), ["Pause", "Quit"])
        t.activate()  # Pause
        self.assertEqual(t.state, omt.PAUSED)
        self.assertEqual(t.menu(), ["Resume", "Quit"])
        t.activate()  # Resume
        self.assertEqual(t.state, omt.RUNNING)
        t.end_at = 0  # force expiry
        self.assertTrue(t.tick())
        self.assertFalse(t.tick())  # beeps only once
        self.assertEqual(t.menu(), ["Restart", "Quit"])
        t.activate()  # Restart
        self.assertEqual(t.state, omt.RUNNING)
        self.assertAlmostEqual(t.now_remaining(), 60, delta=1)
        t.move(1)
        self.assertFalse(t.activate())  # Quit


if __name__ == "__main__":
    unittest.main()
