"""Pixel-art Bonsai stage definitions and run-length SVG renderer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

GRID_WIDTH = 28
GRID_HEIGHT = 24

# Each stage is a 24x28 character grid sharing the same pot base (rows 18-23).
# Legend:
#   . = transparent
#   P/p/q = ceramic pot (rim/body/shadow)
#   S = soil, M = moss
#   T/t/d = trunk & branches (highlight/mid/shadow)
#   L/l/g = foliage (highlight/mid/shadow)
#   B = blossom accent (stages 4-5)
STAGE_GRIDS: Dict[int, List[str]] = {
    1: [
        "............................",
        "............................",
        "............................",
        "............................",
        "............................",
        "............................",
        "............................",
        "............................",
        "............................",
        "............................",
        "............................",
        ".............LL.............",
        "...........LLllL............",
        "..........Lllg.lL...........",
        "............g.T.ll..........",
        ".............Tt.............",
        ".............td.............",
        "............Ttd.............",
        ".........SSSSSSSSSS.........",
        "........PPPPPPPPPPPP........",
        "........pppppppppppq........",
        ".........ppppppppqq.........",
        ".........ppppppppqq.........",
        "..........pp....qq..........",
    ],
    2: [
        "............................",
        "............................",
        "............................",
        "............................",
        "............................",
        "............................",
        "............................",
        ".............LLLL...........",
        "...........LLllllLL.........",
        "..........Lllggggll.........",
        "......LLL..gg.Tt.g..........",
        ".....LlllL...Ttd............",
        ".....llgg...Ttd.............",
        "......gg...Ttd..............",
        "........Ttdtd...............",
        ".........Ttd................",
        "..........Ttd...............",
        ".........TTtd...............",
        ".........SSSSSSSSSS.........",
        "........PPPPPPPPPPPP........",
        "........pppppppppppq........",
        ".........ppppppppqq.........",
        ".........ppppppppqq.........",
        "..........pp....qq..........",
    ],
    3: [
        "............................",
        "............................",
        "............................",
        ".............LLLLLL.........",
        "...........LLllllllLL.......",
        "..........LllggggggllL......",
        "....LLLL...ggggTttggg.......",
        "...LllllL.....Ttd...........",
        "..LllggllL...Ttd....LLLL....",
        "...gggTtt...Ttd....LllllL...",
        "......Ttd..Ttd.....llggll...",
        ".......TtdTtd......ggTtgg...",
        "........Tttd........Ttd.....",
        ".........Ttd.......Ttd......",
        "..........Ttd....TTtd.......",
        "...........TtdTTttd.........",
        "............TTTTtd..........",
        "..........MMTTTTtdMM........",
        ".........SSSSSSSSSS.........",
        "........PPPPPPPPPPPP........",
        "........pppppppppppq........",
        ".........ppppppppqq.........",
        ".........ppppppppqq.........",
        "..........pp....qq..........",
    ],
    4: [
        "............LLLL............",
        "..........LLllllLL..........",
        ".........LllBllBllL.........",
        "....LLL...lggggggl...LLL....",
        "...LlllL..ggTttTgg..LllBL...",
        "..LllBllL...Ttd....LllgglL..",
        "...lgggg...Ttd..LL..gggTtd..",
        "....Ttt...Ttd..LllL...Ttd...",
        ".....Ttd.Ttd...lBgl..Ttd....",
        "......Ttdtd.....Ttd.Ttd.....",
        "...LLL.Ttd......TtdTtd......",
        "..LllBLTtd.......Tttd.......",
        "..llgglTtd.......Ttd........",
        "...ggTttd.......Ttd.........",
        "......Ttd......Ttd..........",
        ".......Ttd...TTtd...........",
        ".......MTTTtTttdMM..........",
        "......MMMTTTTTTdMMM.........",
        "........SSSSSSSSSSSS........",
        ".......PPPPPPPPPPPPPP.......",
        ".......ppppppppppppqq.......",
        "........ppppppppppqq........",
        "........ppppppppppqq........",
        ".........pp......qq.........",
    ],
    5: [
        "..........LLLLLLLL..........",
        "........LLllBlllBlLL........",
        ".......LlllgggggglllL.......",
        "..LLLL..lggggTttgggl..LLLL..",
        ".LllBlL..gggTtdTggg..LllBlL.",
        ".llggllL...Ttd.Ttd..Lllggll.",
        "..gggTtt..Ttd...Ttd..ggTtt..",
        ".....Ttd.Ttd..LL.Ttd..Ttd...",
        "......Ttdtd..LllL.TtdTtd....",
        ".LLL...Ttd...lBgl..Tttd.LLL.",
        "LllBL..Ttd...ggTtd.Ttd.LllBL",
        "llggl.Ttd.....Ttd..Ttd.llggl",
        ".ggTtttd......Ttd.Ttd...ggTt",
        "...Tttd.......TtdTtd.....Ttd",
        "....Ttd........Tttd.....Ttd.",
        "....MTtd......TTtd....TTtd..",
        "....MMTTTtTTTtttddTTTTtdMM..",
        "...MMMMTTTTTTTTTdddTTTTMMM..",
        "........SSSSSSSSSSSS........",
        ".......PPPPPPPPPPPPPP.......",
        ".......ppppppppppppqq.......",
        "........ppppppppppqq........",
        "........ppppppppppqq........",
        ".........pp......qq.........",
    ],
}


@dataclass(frozen=True)
class BonsaiPalette:
    """Color palette tailored to health state and theme."""

    pot_rim: str
    pot_body: str
    pot_shadow: str
    soil: str
    moss: str
    trunk_hi: str
    trunk_mid: str
    trunk_dark: str
    leaf_hi: str
    leaf_mid: str
    leaf_dark: str
    blossom: str


def get_palette(health: str, theme: str) -> BonsaiPalette:
    """Return pixel-art colors for the given health status and light/dark theme."""
    is_dark = theme == "dark"
    pot_rim = "#38BDF8" if is_dark else "#0284C7"
    pot_body = "#1E3A5F" if is_dark else "#0369A1"
    pot_shadow = "#10233B" if is_dark else "#075985"

    if health == "layu":
        return BonsaiPalette(
            pot_rim=pot_rim,
            pot_body=pot_body,
            pot_shadow=pot_shadow,
            soil="#926C44",
            moss="#7C6F49",
            trunk_hi="#8C6D53",
            trunk_mid="#6E523C",
            trunk_dark="#4E3828",
            leaf_hi="#D99B4E",
            leaf_mid="#B57933",
            leaf_dark="#805121",
            blossom="#F59E0B",
        )
    if health == "haus":
        return BonsaiPalette(
            pot_rim=pot_rim,
            pot_body=pot_body,
            pot_shadow=pot_shadow,
            soil="#7B5836",
            moss="#65A30D",
            trunk_hi="#A1724E",
            trunk_mid="#7D5436",
            trunk_dark="#543622",
            leaf_hi="#A3E635",
            leaf_mid="#65A30D",
            leaf_dark="#4D7C0F",
            blossom="#FBBF24",
        )
    if health == "subur":
        return BonsaiPalette(
            pot_rim=pot_rim,
            pot_body=pot_body,
            pot_shadow=pot_shadow,
            soil="#4A3222",
            moss="#22C55E",
            trunk_hi="#A9744F",
            trunk_mid="#855637",
            trunk_dark="#593722",
            leaf_hi="#4ADE80",
            leaf_mid="#22C55E",
            leaf_dark="#15803D",
            blossom="#F472B6",
        )
    # Default: "segar"
    return BonsaiPalette(
        pot_rim=pot_rim,
        pot_body=pot_body,
        pot_shadow=pot_shadow,
        soil="#573B28",
        moss="#34D399",
        trunk_hi="#A4704B",
        trunk_mid="#7F5335",
        trunk_dark="#563520",
        leaf_hi="#6EE7B7",
        leaf_mid="#10B981",
        leaf_dark="#047857",
        blossom="#38BDF8",
    )


def _palette_map(palette: BonsaiPalette) -> Dict[str, str]:
    return {
        "P": palette.pot_rim,
        "p": palette.pot_body,
        "q": palette.pot_shadow,
        "S": palette.soil,
        "M": palette.moss,
        "T": palette.trunk_hi,
        "t": palette.trunk_mid,
        "d": palette.trunk_dark,
        "L": palette.leaf_hi,
        "l": palette.leaf_mid,
        "g": palette.leaf_dark,
        "B": palette.blossom,
    }


def render_bonsai_pixels(
    level: int,
    health: str,
    theme: str,
    origin_x: int = 38,
    origin_y: int = 36,
    pixel_size: int = 7,
) -> str:
    """Render the bonsai stage into run-length merged SVG <rect> elements."""
    clamped_level = max(1, min(5, level))
    grid = STAGE_GRIDS[clamped_level]
    cmap = _palette_map(get_palette(health, theme))

    rects: List[str] = []
    for row_idx, row in enumerate(grid):
        col = 0
        while col < len(row):
            ch = row[col]
            if ch == "." or ch not in cmap:
                col += 1
                continue
            end_col = col + 1
            while end_col < len(row) and row[end_col] == ch:
                end_col += 1
            span = end_col - col
            x = origin_x + col * pixel_size
            y = origin_y + row_idx * pixel_size
            w = span * pixel_size
            rects.append(
                f'<rect x="{x}" y="{y}" width="{w}" height="{pixel_size}" fill="{cmap[ch]}"/>'
            )
            col = end_col

    return "\n    ".join(rects)
