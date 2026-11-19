"""Unit tests for Community Bonsai state logic and SVG rendering."""

from __future__ import annotations

import sys
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import bonsai  # noqa: E402
import bonsai_art  # noqa: E402


class TestBonsaiArt(unittest.TestCase):
    def test_stage_grids_dimensions(self) -> None:
        self.assertEqual(set(bonsai_art.STAGE_GRIDS.keys()), {1, 2, 3, 4, 5})
        for level, grid in bonsai_art.STAGE_GRIDS.items():
            self.assertEqual(len(grid), bonsai_art.GRID_HEIGHT, f"Level {level} row count mismatch")
            for idx, row in enumerate(grid):
                self.assertEqual(
                    len(row),
                    bonsai_art.GRID_WIDTH,
                    f"Level {level} row {idx} width mismatch",
                )


class TestBonsaiState(unittest.TestCase):
    def test_compute_health_boundaries(self) -> None:
        self.assertEqual(bonsai.compute_health(100), "subur")
        self.assertEqual(bonsai.compute_health(80), "subur")
        self.assertEqual(bonsai.compute_health(79), "segar")
        self.assertEqual(bonsai.compute_health(45), "segar")
        self.assertEqual(bonsai.compute_health(44), "haus")
        self.assertEqual(bonsai.compute_health(15), "haus")
        self.assertEqual(bonsai.compute_health(14), "layu")
        self.assertEqual(bonsai.compute_health(0), "layu")

    def test_compute_level_thresholds(self) -> None:
        self.assertEqual(bonsai.compute_level(0), 1)
        self.assertEqual(bonsai.compute_level(29), 1)
        self.assertEqual(bonsai.compute_level(30), 2)
        self.assertEqual(bonsai.compute_level(80), 3)
        self.assertEqual(bonsai.compute_level(160), 4)
        self.assertEqual(bonsai.compute_level(300), 5)
        self.assertEqual(bonsai.compute_level(999), 5)

    def test_water_and_cooldown(self) -> None:
        t0 = datetime(2026, 11, 19, 10, 0, tzinfo=timezone.utc)
        state = bonsai.default_state(now=t0)
        res1 = bonsai.water_bonsai(state, "Alice", now=t0)
        self.assertEqual(res1["status"], "watered")
        self.assertEqual(res1["xp_gained"], 10)
        self.assertEqual(state["moisture"], 100)
        self.assertEqual(state["health"], "subur")
        self.assertEqual(state["total_waterings"], 1)

        # Within 1-hour cooldown should be blocked.
        res_cd = bonsai.water_bonsai(state, "alice", now=t0 + timedelta(minutes=20))
        self.assertEqual(res_cd["status"], "cooldown")
        self.assertEqual(res_cd["remaining_minutes"], 40)
        self.assertEqual(state["total_waterings"], 1)

        # After cooldown expires, another user or same user can water again.
        res2 = bonsai.water_bonsai(state, "Alice", now=t0 + timedelta(hours=1, minutes=1))
        self.assertEqual(res2["status"], "watered")
        self.assertEqual(state["total_waterings"], 2)

    def test_rescue_bonus_and_level_up(self) -> None:
        t0 = datetime(2026, 11, 19, 10, 0, tzinfo=timezone.utc)
        state = bonsai.default_state(now=t0)
        state["moisture"] = 20
        state["xp"] = 20
        res = bonsai.water_bonsai(state, "Bob", now=t0)
        self.assertTrue(res["rescue_bonus"])
        self.assertEqual(res["xp_gained"], 15)
        self.assertTrue(res["leveled_up"])
        self.assertEqual(state["level"], 2)
        self.assertEqual(state["moisture"], 45)
        self.assertEqual(state["health"], "segar")

    def test_decay_idempotent_per_wib_day(self) -> None:
        t0 = datetime(2026, 11, 19, 17, 5, tzinfo=timezone.utc)  # 00:05 WIB Nov 20
        state = bonsai.default_state(now=t0)
        res1 = bonsai.decay_bonsai(state, now=t0)
        self.assertEqual(res1["status"], "decayed")
        self.assertEqual(state["moisture"], 60)

        res2 = bonsai.decay_bonsai(state, now=t0 + timedelta(hours=2))
        self.assertEqual(res2["status"], "skipped")
        self.assertEqual(state["moisture"], 60)

        res3 = bonsai.decay_bonsai(state, now=t0 + timedelta(days=1))
        self.assertEqual(res3["status"], "decayed")
        self.assertEqual(state["moisture"], 45)

    def test_parse_komarev_svg(self) -> None:
        sample = '<svg><g><text x="40" y="14">Profile views</text><text x="86" y="14">1,234</text></g></svg>'
        self.assertEqual(bonsai.parse_komarev_svg(sample), 1234)
        self.assertIsNone(bonsai.parse_komarev_svg("<svg></svg>"))

    def test_render_svg_card_valid_xml_all_variants(self) -> None:
        now = datetime(2026, 11, 19, 12, 0, tzinfo=timezone.utc)
        for level in (1, 2, 3, 4, 5):
            for health, moisture in (("subur", 90), ("segar", 65), ("haus", 30), ("layu", 5)):
                state = bonsai.default_state(now=now)
                state["level"] = level
                state["xp"] = bonsai.LEVEL_THRESHOLDS[level]
                state["moisture"] = moisture
                state["health"] = health
                state["last_known_views"] = 120
                state["total_waterings"] = 18
                state["last_watered_by"] = "user<script>&"
                state["last_watered_at"] = "2026-11-19T11:30:00Z"

                for theme in ("dark", "light"):
                    for lang in ("en", "id"):
                        svg = bonsai.render_svg_card(state, theme=theme, lang=lang, now=now)
                        root = ET.fromstring(svg)
                        self.assertTrue(root.tag.endswith("svg"))
                        self.assertIn("120", svg)
                        self.assertIn("18", svg)
                        self.assertIn("102", svg)  # lurkers = 120 - 18
                        self.assertNotIn("<script>", svg)

        en_comment = bonsai.build_issue_comment(
            {"status": "watered", "user": "Bob", "xp_gained": 10, "rescue_bonus": False, "leveled_up": False},
            bonsai.default_state(now=now),
            lang="en",
        )
        self.assertIn("Thanks @Bob", en_comment)
        id_comment = bonsai.build_issue_comment(
            {"status": "watered", "user": "Bob", "xp_gained": 10, "rescue_bonus": False, "leveled_up": False},
            bonsai.default_state(now=now),
            lang="id",
        )
        self.assertIn("Terima kasih @Bob", id_comment)


if __name__ == "__main__":
    unittest.main()
