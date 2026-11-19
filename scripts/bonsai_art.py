"""Layered botanical vector Bonsai artwork across 5 growth stages and 4 health states."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class BotanicalPalette:
    """Color tokens for the bonsai scene matched to health state and theme."""

    sky_top: str
    sky_mid: str
    sky_bot: str
    sky_accent: str
    sill: str
    sill_edge: str
    pot_body: str
    pot_rim: str
    pot_shadow: str
    soil: str
    moss: str
    trunk_dark: str
    trunk_mid: str
    trunk_hi: str
    leaf_dark: str
    leaf_mid: str
    leaf_hi: str
    blossom: str
    blossom_center: str
    stone: str


def get_botanical_palette(health: str, theme: str) -> BotanicalPalette:
    """Return Apple Weather-inspired sky and botanical tones for health & theme."""
    is_dark = theme == "dark"

    sill = "#2A2420" if is_dark else "#D8CEC0"
    sill_edge = "#1E1916" if is_dark else "#C5B9A8"
    pot_body = "#3A3F45" if is_dark else "#ECEAE4"
    pot_rim = "#4C525A" if is_dark else "#F8F7F4"
    pot_shadow = "#23272C" if is_dark else "#C9C5BC"
    stone = "#525860" if is_dark else "#9CA3AF"

    if health == "layu":
        return BotanicalPalette(
            sky_top="#23252A" if is_dark else "#6D7885",
            sky_mid="#2D3036" if is_dark else "#8B97A4",
            sky_bot="#3A3D44" if is_dark else "#B6C0CA",
            sky_accent="#9CA3AF" if is_dark else "#E5E7EB",
            sill=sill,
            sill_edge=sill_edge,
            pot_body=pot_body,
            pot_rim=pot_rim,
            pot_shadow=pot_shadow,
            soil="#5C4735" if is_dark else "#7D624B",
            moss="#6B5E42" if is_dark else "#8C7D5A",
            trunk_dark="#4A382B",
            trunk_mid="#69503E",
            trunk_hi="#856853",
            leaf_dark="#6E4E2E",
            leaf_mid="#946B3E",
            leaf_hi="#B58954",
            blossom="#D4A373",
            blossom_center="#8C5E34",
            stone=stone,
        )
    if health == "haus":
        return BotanicalPalette(
            sky_top="#2B2118" if is_dark else "#C27D44",
            sky_mid="#3E2E20" if is_dark else "#DBA16B",
            sky_bot="#523D2B" if is_dark else "#F0CAA1",
            sky_accent="#FBBF24" if is_dark else "#FFF3D6",
            sill=sill,
            sill_edge=sill_edge,
            pot_body=pot_body,
            pot_rim=pot_rim,
            pot_shadow=pot_shadow,
            soil="#4D3B2C" if is_dark else "#735842",
            moss="#627834" if is_dark else "#7D9644",
            trunk_dark="#4D3728",
            trunk_mid="#70513B",
            trunk_hi="#8F6A4E",
            leaf_dark="#4E6629",
            leaf_mid="#728F3B",
            leaf_hi="#93B252",
            blossom="#F2C14E",
            blossom_center="#B57C14",
            stone=stone,
        )
    if health == "subur":
        return BotanicalPalette(
            sky_top="#132238" if is_dark else "#3D82C4",
            sky_mid="#1D3554" if is_dark else "#6AA8DE",
            sky_bot="#2B4B72" if is_dark else "#AED4F2",
            sky_accent="#93C5FD" if is_dark else "#FFF8DC",
            sill=sill,
            sill_edge=sill_edge,
            pot_body=pot_body,
            pot_rim=pot_rim,
            pot_shadow=pot_shadow,
            soil="#33261D" if is_dark else "#543D2D",
            moss="#2E7D4F" if is_dark else "#40916C",
            trunk_dark="#472E1E",
            trunk_mid="#6D4830",
            trunk_hi="#8F6244",
            leaf_dark="#1B5E3A",
            leaf_mid="#2D8A56",
            leaf_hi="#49B675",
            blossom="#F48FB1",
            blossom_center="#FFF3F7",
            stone=stone,
        )
    # Default: "segar" (Healthy)
    return BotanicalPalette(
        sky_top="#16253A" if is_dark else "#4A8AC6",
        sky_mid="#223854" if is_dark else "#76B0E0",
        sky_bot="#304E70" if is_dark else "#B7D9F4",
        sky_accent="#BAE6FD" if is_dark else "#FFFDF0",
        sill=sill,
        sill_edge=sill_edge,
        pot_body=pot_body,
        pot_rim=pot_rim,
        pot_shadow=pot_shadow,
        soil="#3B2C22" if is_dark else "#5E4636",
        moss="#3B7A57" if is_dark else "#529471",
        trunk_dark="#4A3222",
        trunk_mid="#6E4B33",
        trunk_hi="#8F6447",
        leaf_dark="#236342",
        leaf_mid="#35885B",
        leaf_hi="#52AA7A",
        blossom="#F9A8D4",
        blossom_center="#FFFFFF",
        stone=stone,
    )


def _render_pot_and_sill(p: BotanicalPalette, wide: bool = False) -> str:
    """Render the wooden desk sill, contact shadow, and glazed stoneware pot."""
    if wide:
        return f"""
    <rect x="0" y="184" width="264" height="32" fill="{p.sill}"/>
    <line x1="0" y1="184" x2="264" y2="184" stroke="{p.sill_edge}" stroke-width="1"/>
    <ellipse cx="132" cy="186" rx="56" ry="5" fill="rgba(0,0,0,0.22)"/>
    <!-- Wide Stoneware Pot -->
    <path d="M84 156 L180 156 L172 182 Q170 185 166 185 L98 185 Q94 185 92 182 Z" fill="{p.pot_body}"/>
    <path d="M148 156 L180 156 L172 182 Q170 185 166 185 L146 185 Z" fill="{p.pot_shadow}" opacity="0.45"/>
    <rect x="78" y="150" width="108" height="7" rx="3" fill="{p.pot_rim}"/>
    <rect x="96" y="184" width="14" height="3" rx="1" fill="{p.pot_shadow}"/>
    <rect x="154" y="184" width="14" height="3" rx="1" fill="{p.pot_shadow}"/>
    <ellipse cx="132" cy="150" rx="46" ry="4" fill="{p.soil}"/>
    <ellipse cx="114" cy="149" rx="16" ry="3" fill="{p.moss}" opacity="0.85"/>
    <ellipse cx="150" cy="150" rx="14" ry="2.5" fill="{p.moss}" opacity="0.7"/>"""

    return f"""
    <rect x="0" y="184" width="264" height="32" fill="{p.sill}"/>
    <line x1="0" y1="184" x2="264" y2="184" stroke="{p.sill_edge}" stroke-width="1"/>
    <ellipse cx="132" cy="186" rx="46" ry="5" fill="rgba(0,0,0,0.22)"/>
    <!-- Ceramic Pot -->
    <path d="M92 154 L172 154 L164 181 Q162 185 158 185 L106 185 Q102 185 100 181 Z" fill="{p.pot_body}"/>
    <path d="M144 154 L172 154 L164 181 Q162 185 158 185 L142 185 Z" fill="{p.pot_shadow}" opacity="0.45"/>
    <rect x="86" y="148" width="92" height="7" rx="3" fill="{p.pot_rim}"/>
    <rect x="104" y="184" width="12" height="3" rx="1" fill="{p.pot_shadow}"/>
    <rect x="148" y="184" width="12" height="3" rx="1" fill="{p.pot_shadow}"/>
    <ellipse cx="132" cy="148" rx="38" ry="4" fill="{p.soil}"/>
    <ellipse cx="122" cy="148" rx="14" ry="2.5" fill="{p.moss}" opacity="0.8"/>"""


def _leaf_cluster(cx: float, cy: float, rx: float, ry: float, p: BotanicalPalette) -> str:
    """Render a three-tone layered foliage pad with sunlit top highlight."""
    return (
        f'<ellipse cx="{cx}" cy="{cy + 3}" rx="{rx}" ry="{ry}" fill="{p.leaf_dark}"/>'
        f'<ellipse cx="{cx - 2}" cy="{cy}" rx="{rx * 0.92:.1f}" ry="{ry * 0.88:.1f}" fill="{p.leaf_mid}"/>'
        f'<ellipse cx="{cx - rx * 0.16:.1f}" cy="{cy - ry * 0.28:.1f}" rx="{rx * 0.62:.1f}" ry="{ry * 0.48:.1f}" fill="{p.leaf_hi}"/>'
    )


def _blossom(cx: float, cy: float, r: float, p: BotanicalPalette) -> str:
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{p.blossom}"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r * 0.38:.1f}" fill="{p.blossom_center}"/>'
    )


def render_bonsai_illustration(level: int, health: str, theme: str) -> str:
    """Return an Apple Weather-inspired sky and botanical vector SVG group."""
    lvl = max(1, min(5, level))
    p = get_botanical_palette(health, theme)
    is_dark = theme == "dark"

    if is_dark:
        sky_detail = f"""
    <circle cx="218" cy="46" r="14" fill="{p.sky_accent}" opacity="0.16"/>
    <circle cx="218" cy="46" r="6.5" fill="{p.sky_accent}" opacity="0.85"/>
    <circle cx="221" cy="44" r="5.8" fill="{p.sky_top}"/>
    <circle cx="56" cy="52" r="1.1" fill="#FFFFFF" opacity="0.65"/>
    <circle cx="174" cy="34" r="1.3" fill="#FFFFFF" opacity="0.55"/>
    <circle cx="92" cy="68" r="0.9" fill="#FFFFFF" opacity="0.45"/>"""
    else:
        sky_detail = f"""
    <circle cx="214" cy="44" r="24" fill="{p.sky_accent}" opacity="0.28"/>
    <circle cx="214" cy="44" r="12" fill="{p.sky_accent}" opacity="0.72"/>
    <ellipse cx="72" cy="66" rx="34" ry="11" fill="#FFFFFF" opacity="0.24"/>
    <ellipse cx="92" cy="62" rx="22" ry="9" fill="#FFFFFF" opacity="0.26"/>
    <ellipse cx="196" cy="86" rx="28" ry="8" fill="#FFFFFF" opacity="0.18"/>"""

    sky_bg = f"""
    <defs>
      <linearGradient id="apple-sky" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="{p.sky_top}"/>
        <stop offset="52%" stop-color="{p.sky_mid}"/>
        <stop offset="100%" stop-color="{p.sky_bot}"/>
      </linearGradient>
    </defs>
    <rect x="0" y="0" width="264" height="190" fill="url(#apple-sky)"/>{sky_detail}"""
    base = f"{sky_bg}{_render_pot_and_sill(p, wide=(lvl >= 4))}"

    if lvl == 1:
        tree = f"""
    <!-- Stage 1: Sprout -->
    <path d="M132 148 C131 134 136 122 133 108" stroke="{p.trunk_dark}" stroke-width="6" stroke-linecap="round" fill="none"/>
    <path d="M131 148 C130 134 135 122 132 108" stroke="{p.trunk_mid}" stroke-width="4" stroke-linecap="round" fill="none"/>
    <path d="M130 146 C129 134 133 124 131 112" stroke="{p.trunk_hi}" stroke-width="1.5" stroke-linecap="round" fill="none"/>
    <path d="M133 114 C118 112 108 100 112 91 C124 91 133 101 133 114 Z" fill="{p.leaf_mid}"/>
    <path d="M132 110 C121 107 115 99 116 93 C124 94 130 101 132 110 Z" fill="{p.leaf_hi}"/>
    <path d="M133 109 C145 104 156 108 154 117 C144 120 135 115 133 109 Z" fill="{p.leaf_dark}"/>
    <path d="M134 109 C144 106 152 109 151 115 C143 117 137 113 134 109 Z" fill="{p.leaf_mid}"/>
    {_leaf_cluster(132, 96, 15, 9, p)}"""
    elif lvl == 2:
        tree = f"""
    <!-- Stage 2: Sapling -->
    <path d="M130 148 C122 134 142 122 136 104 C132 94 126 88 130 78" stroke="{p.trunk_dark}" stroke-width="8" stroke-linecap="round" fill="none"/>
    <path d="M129 148 C121 134 141 122 135 104 C131 94 125 88 129 78" stroke="{p.trunk_mid}" stroke-width="5.5" stroke-linecap="round" fill="none"/>
    <path d="M127 146 C120 134 137 122 132 106" stroke="{p.trunk_hi}" stroke-width="1.8" stroke-linecap="round" fill="none"/>
    <path d="M134 112 C120 108 110 104 104 98" stroke="{p.trunk_mid}" stroke-width="4" stroke-linecap="round" fill="none"/>
    {_leaf_cluster(102, 95, 20, 11, p)}
    {_leaf_cluster(132, 74, 24, 13, p)}"""
    elif lvl == 3:
        tree = f"""
    <!-- Stage 3: Young Bonsai -->
    <path d="M136 148 C126 136 116 128 124 112 C132 98 144 92 132 76 C126 68 128 62 132 56" stroke="{p.trunk_dark}" stroke-width="11" stroke-linecap="round" fill="none"/>
    <path d="M135 148 C125 136 115 128 123 112 C131 98 143 92 131 76 C125 68 127 62 131 56" stroke="{p.trunk_mid}" stroke-width="8" stroke-linecap="round" fill="none"/>
    <path d="M132 146 C122 135 114 128 121 114" stroke="{p.trunk_hi}" stroke-width="2.2" stroke-linecap="round" fill="none"/>
    <path d="M122 114 C106 110 94 104 86 96" stroke="{p.trunk_mid}" stroke-width="5" stroke-linecap="round" fill="none"/>
    <path d="M136 94 C150 90 162 86 172 80" stroke="{p.trunk_mid}" stroke-width="4.5" stroke-linecap="round" fill="none"/>
    {_leaf_cluster(86, 92, 24, 12, p)}
    {_leaf_cluster(172, 78, 22, 11, p)}
    {_leaf_cluster(132, 54, 30, 15, p)}"""
    elif lvl == 4:
        tree = f"""
    <!-- Stage 4: Blooming Bonsai -->
    <path d="M138 150 C124 140 112 130 120 112 C128 96 146 90 134 72 C128 62 126 56 130 48" stroke="{p.trunk_dark}" stroke-width="13" stroke-linecap="round" fill="none"/>
    <path d="M136 150 C122 140 110 130 118 112 C126 96 144 90 132 72 C126 62 124 56 128 48" stroke="{p.trunk_mid}" stroke-width="9.5" stroke-linecap="round" fill="none"/>
    <path d="M132 148 C119 138 109 130 116 114" stroke="{p.trunk_hi}" stroke-width="2.6" stroke-linecap="round" fill="none"/>
    <path d="M118 114 C100 108 86 102 74 92" stroke="{p.trunk_mid}" stroke-width="5.5" stroke-linecap="round" fill="none"/>
    <path d="M136 92 C154 88 170 84 184 76" stroke="{p.trunk_mid}" stroke-width="5" stroke-linecap="round" fill="none"/>
    {_leaf_cluster(74, 88, 26, 13, p)}
    {_leaf_cluster(184, 74, 25, 13, p)}
    {_leaf_cluster(118, 60, 22, 12, p)}
    {_leaf_cluster(136, 48, 32, 15, p)}
    {_blossom(66, 84, 3.2, p)}
    {_blossom(82, 82, 2.6, p)}
    {_blossom(124, 43, 3.2, p)}
    {_blossom(146, 44, 2.8, p)}
    {_blossom(178, 69, 3.0, p)}
    {_blossom(194, 72, 2.5, p)}"""
    else:
        tree = f"""
    <!-- Stage 5: Ancient Bonsai -->
    <ellipse cx="148" cy="147" rx="16" ry="7" fill="{p.stone}"/>
    <path d="M124 150 C116 142 108 134 116 114 C124 96 148 92 138 72 C130 58 124 52 130 42" stroke="{p.trunk_dark}" stroke-width="15" stroke-linecap="round" fill="none"/>
    <path d="M122 150 C114 142 106 134 114 114 C122 96 146 92 136 72 C128 58 122 52 128 42" stroke="{p.trunk_mid}" stroke-width="11" stroke-linecap="round" fill="none"/>
    <path d="M118 148 C110 140 105 133 112 116" stroke="{p.trunk_hi}" stroke-width="3" stroke-linecap="round" fill="none"/>
    <path d="M124 148 C134 144 144 145 152 150" stroke="{p.trunk_mid}" stroke-width="5" stroke-linecap="round" fill="none"/>
    <path d="M114 114 C94 108 78 102 64 92" stroke="{p.trunk_mid}" stroke-width="6" stroke-linecap="round" fill="none"/>
    <path d="M138 90 C158 86 176 82 194 74" stroke="{p.trunk_mid}" stroke-width="5.5" stroke-linecap="round" fill="none"/>
    <path d="M130 68 C144 62 156 58 166 54" stroke="{p.trunk_mid}" stroke-width="4" stroke-linecap="round" fill="none"/>
    {_leaf_cluster(64, 88, 28, 14, p)}
    {_leaf_cluster(194, 72, 28, 14, p)}
    {_leaf_cluster(164, 52, 22, 11, p)}
    {_leaf_cluster(110, 62, 24, 12, p)}
    {_leaf_cluster(132, 42, 34, 16, p)}
    {_blossom(56, 83, 3.2, p)}
    {_blossom(74, 82, 2.8, p)}
    {_blossom(118, 38, 3.4, p)}
    {_blossom(144, 37, 3.0, p)}
    {_blossom(168, 48, 2.6, p)}
    {_blossom(188, 66, 3.2, p)}
    {_blossom(204, 70, 2.6, p)}"""

    return f"{base}{tree}"
