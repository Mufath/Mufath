"""Community Bonsai state manager and Apple-inspired SVG widget generator."""

from __future__ import annotations

import argparse
import html
import json
import math
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bonsai_art import get_botanical_palette, render_bonsai_illustration

WIB = timezone(timedelta(hours=7))

COOLDOWN_HOURS = 1
WATER_MOISTURE_GAIN = 25
DAILY_MOISTURE_DECAY = 15
BASE_WATER_XP = 10
RESCUE_BONUS_XP = 5

LEVEL_THRESHOLDS: Dict[int, int] = {
    1: 0,
    2: 30,
    3: 80,
    4: 160,
    5: 300,
}

# Toned Apple System semantic colors (dark / light)
STATUS_COLORS: Dict[str, Tuple[str, str]] = {
    "subur": ("#30D158", "#16803C"),
    "segar": ("#0A84FF", "#0066CC"),
    "haus": ("#FF9F0A", "#B45309"),
    "layu": ("#FF453A", "#DC2626"),
}

TRANSLATIONS: Dict[str, Dict[str, Any]] = {
    "en": {
        "widget_title": "Community Bonsai",
        "stage_label": "Stage {level} of 5 · {stage}",
        "growth_label": "Growth",
        "xp_max": "Max",
        "moisture_label": "Moisture",
        "views_label": "Profile views",
        "watered_label": "Watered",
        "lurkers_label": "Just looking",
        "last_watered": "Last watered by @{user} · {rel}",
        "no_waterings": "Waiting for the first watering",
        "cta_label": "Water this bonsai",
        "levels": {
            1: "Sprout",
            2: "Sapling",
            3: "Young Bonsai",
            4: "Blooming Bonsai",
            5: "Ancient Bonsai",
        },
        "health": {
            "subur": "Thriving",
            "segar": "Healthy",
            "haus": "Thirsty",
            "layu": "Wilted",
        },
        "time": {
            "just_now": "just now",
            "m": "{n}m ago",
            "h": "{n}h ago",
            "d": "{n}d ago",
        },
        "comment_cooldown": (
            "Thanks @{user}! You already watered the bonsai recently.\n\n"
            "Please wait about **{minutes} minute(s)** before watering again so it doesn't get overwatered.\n\n"
            "- **Stage:** Lv.{level} ({stage})\n"
            "- **Moisture:** {moisture}% ({health})"
        ),
        "comment_watered_header": "Thanks @{user} for watering the Community Bonsai!",
        "comment_xp": "- **XP gained:** +{xp} XP",
        "comment_rescue": " *(Rescue Bonus for saving a thirsty bonsai)*",
        "comment_level_up": "- **Level up:** The bonsai grew from **Lv.{old}** to **Lv.{new} ({stage})**",
        "comment_level_cur": "- **Current stage:** Lv.{level} ({stage}) — {xp} XP",
        "comment_moisture": "- **Moisture:** {moisture}% ({health})",
        "comment_total": "- **Total community waterings:** {total}x",
        "comment_footer": "This issue was closed automatically. Visit [@Mufath](https://github.com/Mufath) to see the updated bonsai.",
    },
    "id": {
        "widget_title": "Community Bonsai",
        "stage_label": "Tahap {level} dari 5 · {stage}",
        "growth_label": "Pertumbuhan",
        "xp_max": "Maks",
        "moisture_label": "Kelembaban",
        "views_label": "Dilihat",
        "watered_label": "Disiram",
        "lurkers_label": "Cuma liat",
        "last_watered": "Disiram oleh @{user} · {rel}",
        "no_waterings": "Menunggu siraman pertama",
        "cta_label": "Siram bonsai ini",
        "levels": {
            1: "Bibit",
            2: "Tunas",
            3: "Bonsai Muda",
            4: "Bonsai Mekar",
            5: "Bonsai Kuno",
        },
        "health": {
            "subur": "Subur",
            "segar": "Segar",
            "haus": "Haus",
            "layu": "Layu",
        },
        "time": {
            "just_now": "baru saja",
            "m": "{n}m lalu",
            "h": "{n}j lalu",
            "d": "{n}h lalu",
        },
        "comment_cooldown": (
            "Terima kasih @{user}. Bonsai baru saja kamu siram sebelumnya.\n\n"
            "Tunggu sekitar **{minutes} menit** lagi sebelum menyiram ulang.\n\n"
            "- **Tahap:** Lv.{level} ({stage})\n"
            "- **Kelembaban:** {moisture}% ({health})"
        ),
        "comment_watered_header": "Terima kasih @{user} sudah menyiram Community Bonsai.",
        "comment_xp": "- **XP didapat:** +{xp} XP",
        "comment_rescue": " *(Rescue Bonus karena tanaman sedang haus/layu)*",
        "comment_level_up": "- **Level up:** Bonsai tumbuh dari **Lv.{old}** ke **Lv.{new} ({stage})**",
        "comment_level_cur": "- **Tahap saat ini:** Lv.{level} ({stage}) — {xp} XP",
        "comment_moisture": "- **Kelembaban:** {moisture}% ({health})",
        "comment_total": "- **Total siraman komunitas:** {total}x",
        "comment_footer": "Issue ini ditutup otomatis. Kunjungi [@Mufath](https://github.com/Mufath) untuk melihat tampilan terbaru.",
    },
}


def default_state(now: Optional[datetime] = None) -> Dict[str, Any]:
    """Create a fresh initial bonsai state."""
    ts = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return {
        "level": 1,
        "xp": 0,
        "moisture": 75,
        "health": "segar",
        "total_waterings": 0,
        "last_known_views": 0,
        "last_watered_at": None,
        "last_watered_by": None,
        "last_decay_date": None,
        "recent_waterers": [],
        "user_cooldowns": {},
        "created_at": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def compute_level(xp: int) -> int:
    """Compute bonsai level (1-5) from cumulative XP."""
    level = 1
    for lvl, threshold in sorted(LEVEL_THRESHOLDS.items()):
        if xp >= threshold:
            level = lvl
    return level


def compute_health(moisture: int) -> str:
    """Determine health status key from moisture percentage (0-100)."""
    if moisture >= 80:
        return "subur"
    if moisture >= 45:
        return "segar"
    if moisture >= 15:
        return "haus"
    return "layu"


def parse_komarev_svg(svg_text: str) -> Optional[int]:
    """Extract integer view count from a Komarev ghpvc SVG response."""
    matches = re.findall(r"<text[^>]*>([^<]+)</text>", svg_text)
    if not matches:
        return None
    raw = matches[-1].strip().replace(",", "").replace(" ", "")
    if not raw.isdigit():
        return None
    return int(raw)


def fetch_komarev_views(username: str = "Mufath", timeout: int = 8) -> Optional[int]:
    """Fetch live view count from Komarev ghpvc badge SVG."""
    url = f"https://komarev.com/ghpvc/?username={username}&style=flat-square"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mufath-Community-Bonsai/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return parse_komarev_svg(body)
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None


def _parse_iso(ts_str: Optional[str]) -> Optional[datetime]:
    if not ts_str:
        return None
    try:
        cleaned = ts_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _format_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _prune_cooldowns(cooldowns: Dict[str, str], now: datetime) -> Dict[str, str]:
    cutoff = now - timedelta(hours=COOLDOWN_HOURS)
    pruned: Dict[str, str] = {}
    for user, ts_str in cooldowns.items():
        parsed = _parse_iso(ts_str)
        if parsed and parsed > cutoff:
            pruned[user] = ts_str
    return pruned


def water_bonsai(
    state: Dict[str, Any],
    username: str,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Apply a watering action by a GitHub user with per-user cooldown."""
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    clean_user = username.strip().lstrip("@") or "anonymous"
    user_key = clean_user.lower()

    cooldowns = _prune_cooldowns(state.get("user_cooldowns", {}), current)
    state["user_cooldowns"] = cooldowns

    last_user_ts = _parse_iso(cooldowns.get(user_key))
    if last_user_ts is not None:
        elapsed = current - last_user_ts
        cooldown_delta = timedelta(hours=COOLDOWN_HOURS)
        if elapsed < cooldown_delta:
            remaining_sec = int((cooldown_delta - elapsed).total_seconds())
            remaining_min = max(1, (remaining_sec + 59) // 60)
            return {
                "status": "cooldown",
                "user": clean_user,
                "remaining_minutes": remaining_min,
                "level": state["level"],
                "xp": state["xp"],
                "moisture": state["moisture"],
                "health": state["health"],
            }

    old_level = int(state.get("level", 1))
    old_moisture = int(state.get("moisture", 75))
    was_needy = old_moisture < 45
    xp_gained = BASE_WATER_XP + (RESCUE_BONUS_XP if was_needy else 0)

    new_moisture = min(100, old_moisture + WATER_MOISTURE_GAIN)
    new_xp = int(state.get("xp", 0)) + xp_gained
    new_level = compute_level(new_xp)
    new_health = compute_health(new_moisture)

    state["moisture"] = new_moisture
    state["xp"] = new_xp
    state["level"] = new_level
    state["health"] = new_health
    state["total_waterings"] = int(state.get("total_waterings", 0)) + 1
    state["last_watered_at"] = _format_iso(current)
    state["last_watered_by"] = clean_user
    cooldowns[user_key] = _format_iso(current)

    recent: List[Dict[str, Any]] = list(state.get("recent_waterers", []))
    recent.insert(
        0,
        {
            "user": clean_user,
            "at": _format_iso(current),
            "xp_gained": xp_gained,
        },
    )
    state["recent_waterers"] = recent[:10]

    return {
        "status": "watered",
        "user": clean_user,
        "xp_gained": xp_gained,
        "rescue_bonus": was_needy,
        "leveled_up": new_level > old_level,
        "old_level": old_level,
        "level": new_level,
        "xp": new_xp,
        "moisture": new_moisture,
        "health": new_health,
        "total_waterings": state["total_waterings"],
    }


def decay_bonsai(
    state: Dict[str, Any],
    now: Optional[datetime] = None,
    force: bool = False,
) -> Dict[str, Any]:
    """Apply daily moisture evaporation (idempotent per WIB calendar day)."""
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    today_wib = current.astimezone(WIB).strftime("%Y-%m-%d")

    if not force and state.get("last_decay_date") == today_wib:
        return {
            "status": "skipped",
            "reason": "already_decayed_today",
            "date": today_wib,
            "moisture": state["moisture"],
            "health": state["health"],
        }

    old_moisture = int(state.get("moisture", 75))
    new_moisture = max(0, old_moisture - DAILY_MOISTURE_DECAY)
    new_health = compute_health(new_moisture)

    state["moisture"] = new_moisture
    state["health"] = new_health
    state["last_decay_date"] = today_wib
    state["user_cooldowns"] = _prune_cooldowns(state.get("user_cooldowns", {}), current)

    return {
        "status": "decayed",
        "date": today_wib,
        "old_moisture": old_moisture,
        "moisture": new_moisture,
        "health": new_health,
    }


def _relative_time(ts_str: Optional[str], now: datetime, lang: str) -> str:
    t = TRANSLATIONS.get(lang, TRANSLATIONS["en"])["time"]
    parsed = _parse_iso(ts_str)
    if parsed is None:
        return "-"
    diff_sec = max(0, int((now - parsed).total_seconds()))
    if diff_sec < 60:
        return t["just_now"]
    minutes = diff_sec // 60
    if minutes < 60:
        return t["m"].format(n=minutes)
    hours = minutes // 60
    if hours < 24:
        return t["h"].format(n=hours)
    return t["d"].format(n=hours // 24)


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _next_level_progress(level: int, xp: int, max_word: str) -> Tuple[float, str]:
    if level >= 5:
        return 100.0, f"{xp} XP · {max_word}"
    cur_floor = LEVEL_THRESHOLDS[level]
    next_target = LEVEL_THRESHOLDS[level + 1]
    span = max(1, next_target - cur_floor)
    pct = max(0.0, min(100.0, ((xp - cur_floor) / span) * 100.0))
    return pct, f"{xp} / {next_target} XP"


def render_svg_card(
    state: Dict[str, Any],
    theme: str = "dark",
    lang: str = "en",
    now: Optional[datetime] = None,
) -> str:
    """Generate a calm Apple-style 800x256 Community Bonsai SVG widget."""
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    is_dark = theme == "dark"
    tr = TRANSLATIONS.get(lang, TRANSLATIONS["en"])

    level = max(1, min(5, int(state.get("level", 1))))
    xp = max(0, int(state.get("xp", 0)))
    moisture = max(0, min(100, int(state.get("moisture", 75))))
    health = state.get("health") or compute_health(moisture)
    if health not in STATUS_COLORS:
        health = compute_health(moisture)

    total_waterings = max(0, int(state.get("total_waterings", 0)))
    raw_views = max(0, int(state.get("last_known_views", 0)))
    views = max(raw_views, total_waterings)
    lurkers = max(0, views - total_waterings)
    care_pct = (total_waterings / views * 100.0) if views > 0 else 0.0

    stage_name = tr["levels"].get(level, tr["levels"][1])
    health_label = tr["health"].get(health, tr["health"]["segar"])
    status_color = STATUS_COLORS[health][0 if is_dark else 1]

    xp_pct, xp_label = _next_level_progress(level, xp, tr["xp_max"])
    xp_bar_w = round(176 * (xp_pct / 100.0), 1)
    share_bar_w = round(456 * (total_waterings / views), 1) if views > 0 else 0.0
    if total_waterings > 0 and share_bar_w < 6.0:
        share_bar_w = 6.0

    # Apple System neutral ramps (Graphite dark / Paper light) + single blue accent.
    if is_dark:
        shell_bg = "#1C1C1E"
        card_bg = "#2C2C2E"
        track_bg = "#3A3A3C"
        hairline = "rgba(255,255,255,0.09)"
        text_primary = "#F5F5F7"
        text_secondary = "#A1A1A6"
        text_muted = "#8E8E93"
        accent = "#0A84FF"
    else:
        shell_bg = "#F5F5F7"
        card_bg = "#FFFFFF"
        track_bg = "#E5E5EA"
        hairline = "rgba(0,0,0,0.08)"
        text_primary = "#1D1D1F"
        text_secondary = "#515154"
        text_muted = "#6E6E73"
        accent = "#0066CC"

    botanical_palette = get_botanical_palette(health, theme)
    illustration = render_bonsai_illustration(level=level, health=health, theme=theme)
    stage_text = tr["stage_label"].format(level=level, stage=stage_name)

    last_user = state.get("last_watered_by")
    if last_user:
        rel = _relative_time(state.get("last_watered_at"), current, lang)
        subtitle = tr["last_watered"].format(
            user=_truncate(str(last_user), 18),
            rel=rel,
        )
    else:
        subtitle = tr["no_waterings"]

    # Moisture circular gauge math (r=22 -> C = 2*pi*22 = 138.23)
    ring_r = 22
    ring_c = 2 * math.pi * ring_r
    ring_offset = ring_c * (1.0 - (moisture / 100.0))
    status_dot_x = round(784 - (len(health_label) * 7.0) - 10, 1)

    title_text = html.escape(f"Community Bonsai Lv.{level} {stage_name}")
    desc_text = html.escape(
        f"Moisture {moisture}%, Status {health_label}, "
        f"Views {views}, Watered {total_waterings}, Just looking {lurkers}."
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="256" viewBox="0 0 800 256" fill="none" role="img" aria-labelledby="bonsai-title bonsai-desc">
  <title id="bonsai-title">{title_text}</title>
  <desc id="bonsai-desc">{desc_text}</desc>
  <defs>
    <clipPath id="scene-clip">
      <rect x="16" y="16" width="264" height="224" rx="12"/>
    </clipPath>
  </defs>
  <style>
    text {{
      font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Segoe UI', Helvetica, Arial, sans-serif;
    }}
    .num {{
      font-variant-numeric: tabular-nums;
    }}
    .enter-bar {{
      transform-box: fill-box;
      transform-origin: left center;
      animation: growX 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
    }}
    @keyframes growX {{
      from {{ transform: scaleX(0); }}
      to {{ transform: scaleX(1); }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      * {{ animation: none !important; }}
    }}
  </style>

  <!-- Outer Apple Card Shell (radius 28, padding 16 -> nested radius 12) -->
  <rect x="0.5" y="0.5" width="799" height="255" rx="28" fill="{shell_bg}" stroke="{hairline}"/>

  <!-- Left Botanical Habitat Scene -->
  <g clip-path="url(#scene-clip)">
    <rect x="16" y="16" width="264" height="224" fill="{botanical_palette.scene_bg}"/>
    <g transform="translate(16 24)">
      {illustration}
    </g>
    <text x="32" y="36" font-size="12" font-weight="500" fill="{text_secondary}">{html.escape(stage_text)}</text>
  </g>
  <rect x="16.5" y="16.5" width="263" height="223" rx="12" stroke="{hairline}" fill="none"/>

  <!-- Right Telemetry Column -->
  <!-- Header -->
  <text x="296" y="36" font-size="17" font-weight="600" fill="{text_primary}">{html.escape(tr['widget_title'])}</text>
  <circle cx="{status_dot_x}" cy="31" r="3.5" fill="{status_color}"/>
  <text x="784" y="35" text-anchor="end" font-size="13" font-weight="500" fill="{text_secondary}">{html.escape(health_label)}</text>
  <text x="296" y="55" font-size="13" font-weight="400" fill="{text_secondary}">{html.escape(subtitle)}</text>

  <!-- Middle Asymmetric Metric Row -->
  <!-- Left Hero Card: Moisture Ring + Tabular Readout -->
  <rect x="296" y="72" width="268" height="84" rx="12" fill="{card_bg}" stroke="{hairline}"/>
  <circle cx="336" cy="114" r="{ring_r}" stroke="{track_bg}" stroke-width="5" fill="none"/>
  <circle cx="336" cy="114" r="{ring_r}" stroke="{status_color}" stroke-width="5" stroke-linecap="round"
    stroke-dasharray="{ring_c:.2f}" stroke-dashoffset="{ring_offset:.2f}" transform="rotate(-90 336 114)" fill="none"/>
  <path d="M336 106.5s-4.5 4.9-4.5 7.6a4.5 4.5 0 0 0 9 0c0-2.7-4.5-7.6-4.5-7.6Z" stroke="{status_color}" stroke-width="1.5" stroke-linejoin="round" fill="none"/>
  <text x="376" y="114" font-size="28" font-weight="500" fill="{text_primary}" letter-spacing="-0.02em" class="num">{moisture}%</text>
  <text x="376" y="133" font-size="12" font-weight="400" fill="{text_secondary}">{html.escape(tr['moisture_label'])} · {html.escape(health_label)}</text>

  <!-- Right Compact Card: Growth XP -->
  <rect x="576" y="72" width="208" height="84" rx="12" fill="{card_bg}" stroke="{hairline}"/>
  <text x="592" y="96" font-size="12" font-weight="400" fill="{text_secondary}">{html.escape(tr['growth_label'])}</text>
  <text x="768" y="96" text-anchor="end" font-size="12" font-weight="400" fill="{text_muted}" class="num">{html.escape(xp_label)}</text>
  <text x="592" y="121" font-size="15" font-weight="500" fill="{text_primary}">Lv. {level} · {html.escape(stage_name)}</text>
  <rect x="592" y="135" width="176" height="6" rx="3" fill="{track_bg}"/>
  <rect x="592" y="135" width="{xp_bar_w}" height="6" rx="3" fill="{accent}" class="enter-bar"/>

  <!-- Bottom Grouped Card: Visitor Views vs Care Share -->
  <rect x="296" y="168" width="488" height="72" rx="12" fill="{card_bg}" stroke="{hairline}"/>
  <text x="312" y="194" font-size="12" font-weight="400" fill="{text_secondary}">{html.escape(tr['views_label'])} <tspan font-size="14" font-weight="500" fill="{text_primary}" class="num" dx="4">{views:,}</tspan></text>
  <text x="536" y="194" text-anchor="middle" font-size="12" font-weight="400" fill="{text_secondary}">{html.escape(tr['watered_label'])} <tspan font-size="14" font-weight="500" fill="{accent}" class="num" dx="4">{total_waterings:,}</tspan> <tspan font-size="12" fill="{text_muted}" class="num">({care_pct:.1f}%)</tspan></text>
  <text x="768" y="194" text-anchor="end" font-size="12" font-weight="400" fill="{text_secondary}">{html.escape(tr['lurkers_label'])} <tspan font-size="14" font-weight="500" fill="{text_primary}" class="num" dx="4">{lurkers:,}</tspan></text>

  <rect x="312" y="212" width="456" height="6" rx="3" fill="{track_bg}"/>
  <rect x="312" y="212" width="{share_bar_w}" height="6" rx="3" fill="{accent}" class="enter-bar"/>
</svg>
"""


def render_cta_button(theme: str = "dark", lang: str = "en") -> str:
    """Generate a restrained Apple-style pill CTA button SVG."""
    is_dark = theme == "dark"
    tr = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    label = html.escape(tr["cta_label"])

    if is_dark:
        bg = "#F5F5F7"
        fg = "#1D1D1F"
        stroke = "rgba(255,255,255,0.12)"
    else:
        bg = "#1D1D1F"
        fg = "#FFFFFF"
        stroke = "rgba(0,0,0,0.08)"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="176" height="38" viewBox="0 0 176 38" fill="none" role="img" aria-label="{label}">
  <style>
    text {{
      font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', Helvetica, Arial, sans-serif;
    }}
  </style>
  <rect x="0.5" y="0.5" width="175" height="37" rx="18.5" fill="{bg}" stroke="{stroke}"/>
  <path d="M27 12.8s-4.2 4.6-4.2 7.1a4.2 4.2 0 0 0 8.4 0c0-2.5-4.2-7.1-4.2-7.1Z" stroke="{fg}" stroke-width="1.5" stroke-linejoin="round" fill="none"/>
  <text x="41" y="23.5" font-size="13" font-weight="500" fill="{fg}">{label}</text>
</svg>
"""


def load_state(path: Path) -> Dict[str, Any]:
    """Load state JSON from disk, falling back to default_state if missing."""
    if not path.exists():
        return default_state()
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    base = default_state()
    base.update(data)
    return base


def save_state(path: Path, state: Dict[str, Any]) -> None:
    """Persist state JSON cleanly with UTF-8 encoding."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def write_cards(
    cards_dir: Path,
    state: Dict[str, Any],
    lang: str = "en",
    now: Optional[datetime] = None,
) -> None:
    """Write dark and light bonsai widget SVGs plus CTA button SVGs into cards_dir."""
    cards_dir.mkdir(parents=True, exist_ok=True)
    for theme in ("dark", "light"):
        svg = render_svg_card(state, theme=theme, lang=lang, now=now)
        (cards_dir / f"bonsai-widget-{theme}.svg").write_text(svg, encoding="utf-8")
        cta = render_cta_button(theme=theme, lang=lang)
        (cards_dir / f"bonsai-cta-{theme}.svg").write_text(cta, encoding="utf-8")


def build_issue_comment(
    result: Dict[str, Any],
    state: Dict[str, Any],
    lang: str = "en",
) -> str:
    """Create a friendly GitHub Issue reply summarizing the watering outcome."""
    tr = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    user = result["user"]
    stage_name = tr["levels"].get(state["level"], tr["levels"][1])
    health_label = tr["health"].get(state["health"], state["health"])

    if result["status"] == "cooldown":
        return tr["comment_cooldown"].format(
            user=user,
            minutes=result["remaining_minutes"],
            level=state["level"],
            stage=stage_name,
            moisture=state["moisture"],
            health=health_label,
        )

    lines = [
        tr["comment_watered_header"].format(user=user),
        "",
        tr["comment_xp"].format(xp=result["xp_gained"])
        + (tr["comment_rescue"] if result.get("rescue_bonus") else ""),
    ]
    if result.get("leveled_up"):
        lines.append(
            tr["comment_level_up"].format(
                old=result["old_level"],
                new=state["level"],
                stage=stage_name,
            )
        )
    else:
        lines.append(
            tr["comment_level_cur"].format(
                level=state["level"],
                stage=stage_name,
                xp=state["xp"],
            )
        )
    lines.extend(
        [
            tr["comment_moisture"].format(moisture=state["moisture"], health=health_label),
            tr["comment_total"].format(total=state["total_waterings"]),
            "",
            tr["comment_footer"],
        ]
    )
    return "\n".join(lines)


def _write_github_output(outputs: Dict[str, str]) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8") as fh:
        for key, value in outputs.items():
            if "\n" in value:
                delimiter = "EOF_BONSAI_OUTPUT"
                fh.write(f"{key}<<{delimiter}\n{value}\n{delimiter}\n")
            else:
                fh.write(f"{key}={value}\n")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Community Bonsai CLI")
    parser.add_argument(
        "--mode",
        choices=("water", "decay", "sync", "render"),
        required=True,
        help="Action to run on the bonsai state.",
    )
    parser.add_argument("--user", default="Mufath", help="GitHub username watering the bonsai.")
    parser.add_argument("--username", default="Mufath", help="GitHub profile username for Komarev views.")
    parser.add_argument("--lang", choices=("en", "id"), default="en", help="Widget language.")
    parser.add_argument("--state", default="data/bonsai_state.json", help="Path to state JSON.")
    parser.add_argument("--cards-dir", default="cards", help="Directory for output SVG cards.")
    parser.add_argument("--force-decay", action="store_true", help="Decay even if already decayed today.")
    parser.add_argument("--no-fetch-views", action="store_true", help="Skip network call to Komarev.")
    args = parser.parse_args(argv)

    state_path = Path(args.state)
    cards_dir = Path(args.cards_dir)
    now = datetime.now(timezone.utc)
    state = load_state(state_path)

    if not args.no_fetch_views and args.mode in ("water", "decay", "sync"):
        live_views = fetch_komarev_views(args.username)
        if live_views is not None:
            state["last_known_views"] = max(int(state.get("last_known_views", 0)), live_views)

    result: Dict[str, Any] = {"mode": args.mode, "status": "ok"}
    comment = ""

    if args.mode == "water":
        result = water_bonsai(state, args.user, now=now)
        comment = build_issue_comment(result, state, lang=args.lang)
    elif args.mode == "decay":
        result = decay_bonsai(state, now=now, force=args.force_decay)
    elif args.mode in ("sync", "render"):
        state["health"] = compute_health(int(state.get("moisture", 75)))
        state["level"] = compute_level(int(state.get("xp", 0)))

    save_state(state_path, state)
    write_cards(cards_dir, state, lang=args.lang, now=now)

    _write_github_output(
        {
            "status": str(result.get("status", "ok")),
            "comment": comment,
        }
    )
    print(
        json.dumps(
            {
                "result": result,
                "state_summary": {
                    "level": state["level"],
                    "xp": state["xp"],
                    "moisture": state["moisture"],
                    "health": state["health"],
                    "total_waterings": state["total_waterings"],
                    "last_known_views": state["last_known_views"],
                },
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
