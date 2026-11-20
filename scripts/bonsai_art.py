"""Full-bleed 800x272 alpine sky panorama and layered botanical vector Bonsai artwork."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BotanicalPalette:
    """Color tokens for the full-bleed alpine bonsai world."""

    sky_top: str
    sky_bot: str
    sky_accent: str
    peak_far: str
    peak_dark: str
    peak_lit: str
    ridge_front: str
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
    """Return morning/daytime (light) or twilight/night (dark) alpine & botanical tones."""
    is_dark = theme == "dark"

    pot_body = "#3A3F45" if is_dark else "#EFECE6"
    pot_rim = "#4E555E" if is_dark else "#FAF8F5"
    pot_shadow = "#23272C" if is_dark else "#C6C0B6"
    stone = "#525860" if is_dark else "#8B95A1"

    if not is_dark:
        # Light Mode: Crisp morning / daytime alpine sky & sunlit peaks
        if health == "layu":
            return BotanicalPalette(
                sky_top="#5E6D7D",
                sky_bot="#B5C1CD",
                sky_accent="#F1F5F9",
                peak_far="#8492A0",
                peak_dark="#525F6C",
                peak_lit="#B2BECA",
                ridge_front="#3B4752",
                pot_body=pot_body,
                pot_rim=pot_rim,
                pot_shadow=pot_shadow,
                soil="#7A624E",
                moss="#8C7E5A",
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
                sky_top="#AE6B38",
                sky_bot="#ECC398",
                sky_accent="#FFF5D6",
                peak_far="#AD7D54",
                peak_dark="#755033",
                peak_lit="#D4A57C",
                ridge_front="#523722",
                pot_body=pot_body,
                pot_rim=pot_rim,
                pot_shadow=pot_shadow,
                soil="#6E533E",
                moss="#7A9442",
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
                sky_top="#296BB0",
                sky_bot="#A9D7F7",
                sky_accent="#FFF9DB",
                peak_far="#6697C2",
                peak_dark="#396287",
                peak_lit="#9BC3E4",
                ridge_front="#254461",
                pot_body=pot_body,
                pot_rim=pot_rim,
                pot_shadow=pot_shadow,
                soil="#543D2D",
                moss="#3D9468",
                trunk_dark="#472E1E",
                trunk_mid="#6D4830",
                trunk_hi="#96684A",
                leaf_dark="#1E6840",
                leaf_mid="#31965E",
                leaf_hi="#53C482",
                blossom="#F48FB1",
                blossom_center="#FFF3F7",
                stone=stone,
            )
        # Light "segar"
        return BotanicalPalette(
            sky_top="#3173B8",
            sky_bot="#B5DCF7",
            sky_accent="#FFFBEB",
            peak_far="#6E9BC4",
            peak_dark="#41688C",
            peak_lit="#A2C7E4",
            ridge_front="#2A4966",
            pot_body=pot_body,
            pot_rim=pot_rim,
            pot_shadow=pot_shadow,
            soil="#5E4636",
            moss="#4E916E",
            trunk_dark="#4A3222",
            trunk_mid="#6E4B33",
            trunk_hi="#926649",
            leaf_dark="#236342",
            leaf_mid="#35885B",
            leaf_hi="#52AA7A",
            blossom="#F9A8D4",
            blossom_center="#FFFFFF",
            stone=stone,
        )

    # Dark Mode: Starry twilight alpine sky & moonlit peaks
    if health == "layu":
        return BotanicalPalette(
            sky_top="#13161A",
            sky_bot="#252B33",
            sky_accent="#9CA3AF",
            peak_far="#1D2228",
            peak_dark="#12151A",
            peak_lit="#434B56",
            ridge_front="#0E1115",
            pot_body=pot_body,
            pot_rim=pot_rim,
            pot_shadow=pot_shadow,
            soil="#524032",
            moss="#665A40",
            trunk_dark="#453428",
            trunk_mid="#664E3D",
            trunk_hi="#856955",
            leaf_dark="#6B4D2E",
            leaf_mid="#8F673D",
            leaf_hi="#B08452",
            blossom="#D4A373",
            blossom_center="#8C5E34",
            stone=stone,
        )
    if health == "haus":
        return BotanicalPalette(
            sky_top="#181512",
            sky_bot="#342B22",
            sky_accent="#FBBF24",
            peak_far="#27211B",
            peak_dark="#17130F",
            peak_lit="#614F3D",
            ridge_front="#110E0B",
            pot_body=pot_body,
            pot_rim=pot_rim,
            pot_shadow=pot_shadow,
            soil="#4D3B2C",
            moss="#627834",
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
            sky_top="#0A1A23",
            sky_bot="#1B3C48",
            sky_accent="#BAE6FD",
            peak_far="#152E37",
            peak_dark="#0C1B21",
            peak_lit="#466E7A",
            ridge_front="#091419",
            pot_body=pot_body,
            pot_rim=pot_rim,
            pot_shadow=pot_shadow,
            soil="#33261D",
            moss="#2E7D4F",
            trunk_dark="#472E1E",
            trunk_mid="#6D4830",
            trunk_hi="#96684A",
            leaf_dark="#1E6840",
            leaf_mid="#31965E",
            leaf_hi="#53C482",
            blossom="#F48FB1",
            blossom_center="#FFF3F7",
            stone=stone,
        )
    return BotanicalPalette(
        sky_top="#0C1D25",
        sky_bot="#1F414E",
        sky_accent="#BAE6FD",
        peak_far="#18333D",
        peak_dark="#0D1D24",
        peak_lit="#4B7380",
        ridge_front="#0A151A",
        pot_body=pot_body,
        pot_rim=pot_rim,
        pot_shadow=pot_shadow,
        soil="#3B2C22",
        moss="#3B7A57",
        trunk_dark="#4A3222",
        trunk_mid="#6E4B33",
        trunk_hi="#926649",
        leaf_dark="#236342",
        leaf_mid="#35885B",
        leaf_hi="#52AA7A",
        blossom="#F9A8D4",
        blossom_center="#FFFFFF",
        stone=stone,
    )


def render_sky_and_far_peaks(p: BotanicalPalette, theme: str = "dark") -> str:
    """Render continuous 800x272 alpine sky & distant misty ridges."""
    is_dark = theme == "dark"
    if is_dark:
        celestial = f"""
    <circle cx="256" cy="48" r="14" fill="{p.sky_accent}" opacity="0.14"/>
    <circle cx="256" cy="48" r="7" fill="{p.sky_accent}" opacity="0.88"/>
    <circle cx="259" cy="46" r="6.2" fill="{p.sky_top}"/>
    <circle cx="54" cy="58" r="1.0" fill="#FFFFFF" opacity="0.50"/>
    <circle cx="122" cy="36" r="0.8" fill="#FFFFFF" opacity="0.40"/>
    <circle cx="204" cy="52" r="1.1" fill="#FFFFFF" opacity="0.45"/>
    <circle cx="420" cy="42" r="0.9" fill="#FFFFFF" opacity="0.35"/>
    <circle cx="628" cy="32" r="1.0" fill="#FFFFFF" opacity="0.40"/>
    <circle cx="742" cy="54" r="0.8" fill="#FFFFFF" opacity="0.32"/>"""
    else:
        celestial = f"""
    <circle cx="254" cy="48" r="24" fill="{p.sky_accent}" opacity="0.28"/>
    <circle cx="254" cy="48" r="12" fill="{p.sky_accent}" opacity="0.82"/>
    <ellipse cx="78" cy="68" rx="36" ry="10" fill="#FFFFFF" opacity="0.26"/>
    <ellipse cx="98" cy="64" rx="22" ry="8" fill="#FFFFFF" opacity="0.28"/>
    <ellipse cx="486" cy="54" rx="44" ry="11" fill="#FFFFFF" opacity="0.16"/>"""

    return f"""
    <defs>
      <linearGradient id="alpine-sky" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="{p.sky_top}"/>
        <stop offset="100%" stop-color="{p.sky_bot}"/>
      </linearGradient>
      <radialGradient id="glass-vignette" cx="35%" cy="48%" r="72%">
        <stop offset="62%" stop-color="#000000" stop-opacity="0"/>
        <stop offset="100%" stop-color="#000000" stop-opacity="{'0.34' if is_dark else '0.14'}"/>
      </radialGradient>
    </defs>
    <rect x="0" y="0" width="800" height="272" fill="url(#alpine-sky)"/>
    {celestial}
    <!-- Continuous far alpine silhouette spanning all 800px -->
    <path d="M0 210 L68 164 L132 190 L216 156 L296 188 L398 148 L504 184 L624 142 L722 178 L800 154 L800 272 L0 272 Z" fill="{p.peak_far}" opacity="0.74"/>"""


def _render_foreground_mountains_and_pot(p: BotanicalPalette, wide: bool = False) -> str:
    """Render continuous foreground mountain ridges + Bonsai pot centered at cx=152."""
    mountains = f"""
    <!-- Left chiseled ridge -->
    <path d="M0 202 L48 168 L112 204 L0 272 Z" fill="{p.peak_dark}"/>
    <path d="M48 168 L22 192 L46 200 L58 184 Z" fill="{p.peak_lit}" opacity="0.60"/>
    <!-- Mid-right continuous chiseled alpine ridge spanning behind the glass cards -->
    <path d="M192 208 L266 158 L352 196 L464 152 L572 194 L692 146 L800 186 L800 272 L152 272 Z" fill="{p.peak_dark}"/>
    <path d="M266 158 L238 188 L262 196 L278 178 Z" fill="{p.peak_lit}" opacity="0.65"/>
    <path d="M464 152 L434 184 L460 192 L476 172 Z" fill="{p.peak_lit}" opacity="0.45"/>
    <path d="M692 146 L658 182 L688 190 L706 168 Z" fill="{p.peak_lit}" opacity="0.50"/>
    <!-- Continuous foreground terrace -->
    <path d="M0 226 Q152 204 336 222 Q580 242 800 220 L800 272 L0 272 Z" fill="{p.ridge_front}"/>
    <ellipse cx="152" cy="222" rx="58" ry="7.5" fill="{p.peak_dark}"/>
    <ellipse cx="152" cy="222" rx="48" ry="4.5" fill="rgba(0,0,0,0.34)"/>"""

    # Pot centered at cx=152 (264-wide coords shifted by +20, +38 -> pot base at y=222)
    if wide:
        pot = f"""
    <g transform="translate(20 38)">
      <path d="M84 156 L180 156 L172 182 Q170 185 166 185 L98 185 Q94 185 92 182 Z" fill="{p.pot_body}"/>
      <path d="M148 156 L180 156 L172 182 Q170 185 166 185 L146 185 Z" fill="{p.pot_shadow}" opacity="0.45"/>
      <rect x="78" y="150" width="108" height="7" rx="3" fill="{p.pot_rim}"/>
      <rect x="96" y="184" width="14" height="3" rx="1" fill="{p.pot_shadow}"/>
      <rect x="154" y="184" width="14" height="3" rx="1" fill="{p.pot_shadow}"/>
      <ellipse cx="132" cy="150" rx="46" ry="4" fill="{p.soil}"/>
      <ellipse cx="114" cy="149" rx="16" ry="3" fill="{p.moss}" opacity="0.85"/>
      <ellipse cx="150" cy="150" rx="14" ry="2.5" fill="{p.moss}" opacity="0.7"/>
    </g>"""
    else:
        pot = f"""
    <g transform="translate(20 38)">
      <path d="M92 154 L172 154 L164 181 Q162 185 158 185 L106 185 Q102 185 100 181 Z" fill="{p.pot_body}"/>
      <path d="M144 154 L172 154 L164 181 Q162 185 158 185 L142 185 Z" fill="{p.pot_shadow}" opacity="0.45"/>
      <rect x="86" y="148" width="92" height="7" rx="3" fill="{p.pot_rim}"/>
      <rect x="104" y="184" width="12" height="3" rx="1" fill="{p.pot_shadow}"/>
      <rect x="148" y="184" width="12" height="3" rx="1" fill="{p.pot_shadow}"/>
      <ellipse cx="132" cy="148" rx="38" ry="4" fill="{p.soil}"/>
      <ellipse cx="122" cy="148" rx="14" ry="2.5" fill="{p.moss}" opacity="0.8"/>
    </g>"""

    return f"{mountains}{pot}"


def _leaf_cluster(cx: float, cy: float, rx: float, ry: float, p: BotanicalPalette) -> str:
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


def render_bonsai_foreground(level: int, health: str, theme: str) -> str:
    """Render foreground ridges and bonsai tree centered at cx=152 inside 800x272 canvas."""
    lvl = max(1, min(5, level))
    p = get_botanical_palette(health, theme)
    base = _render_foreground_mountains_and_pot(p, wide=(lvl >= 4))

    if lvl == 1:
        tree = f"""
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
    <path d="M130 148 C122 134 142 122 136 104 C132 94 126 88 130 78" stroke="{p.trunk_dark}" stroke-width="8" stroke-linecap="round" fill="none"/>
    <path d="M129 148 C121 134 141 122 135 104 C131 94 125 88 129 78" stroke="{p.trunk_mid}" stroke-width="5.5" stroke-linecap="round" fill="none"/>
    <path d="M127 146 C120 134 137 122 132 106" stroke="{p.trunk_hi}" stroke-width="1.8" stroke-linecap="round" fill="none"/>
    <path d="M134 112 C120 108 110 104 104 98" stroke="{p.trunk_mid}" stroke-width="4" stroke-linecap="round" fill="none"/>
    {_leaf_cluster(102, 95, 20, 11, p)}
    {_leaf_cluster(132, 74, 24, 13, p)}"""
    elif lvl == 3:
        tree = f"""
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

    return f'{base}<g transform="translate(20 38)">{tree}</g>'


def render_bonsai_illustration(level: int, health: str, theme: str) -> str:
    """Combined scene helper."""
    p = get_botanical_palette(health, theme)
    return f"{render_sky_and_far_peaks(p, theme=theme)}{render_bonsai_foreground(level, health, theme)}"
