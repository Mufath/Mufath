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

from bonsai_art import (
    get_botanical_palette,
    render_bonsai_foreground,
    render_sky_and_far_peaks,
)

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
    """Generate an 800x272 Apple Immersive Depth-Effect + Visual Indicators Bonsai widget."""
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
    lurker_pct = 100.0 - care_pct if views > 0 else 0.0

    stage_name = tr["levels"].get(level, tr["levels"][1])
    health_label = tr["health"].get(health, tr["health"]["segar"])
    status_color = STATUS_COLORS[health][0 if is_dark else 1]

    xp_pct, xp_label = _next_level_progress(level, xp, tr["xp_max"])
    xp_bar_w = round(174 * (xp_pct / 100.0), 1)

    # Apple Storage-style proportional bar (432px total width inside 464px card, 2px gap)
    if views > 0 and total_waterings > 0 and lurkers > 0:
        watered_w = max(12.0, round(430 * (total_waterings / views), 1))
        watered_w = min(418.0, watered_w)
        lurker_x = 338 + watered_w + 2.0
        lurker_w = max(12.0, round(770 - lurker_x, 1))
    elif total_waterings > 0:
        watered_w = 432.0
        lurker_x = 770.0
        lurker_w = 0.0
    else:
        watered_w = 0.0
        lurker_x = 338.0
        lurker_w = 432.0

    # Apple HIG dark (Sequoia Graphite) & light (iOS Paper) surface tokens.
    if is_dark:
        shell_top = "#242529"
        shell_bot = "#1B1C20"
        card_top = "#2F3034"
        card_bot = "#27282B"
        bevel_top = "rgba(255,255,255,0.20)"
        bevel_bot = "rgba(255,255,255,0.05)"
        card_bevel_top = "rgba(255,255,255,0.14)"
        card_bevel_bot = "rgba(255,255,255,0.04)"
        track_bg = "#3A3A3D"
        lurker_seg = "#545458"
        text_primary = "#F5F5F7"
        text_secondary = "#AEAEB2"
        text_muted = "#8E8E93"
        accent = "#0A84FF"
        pill_bg = "rgba(255,255,255,0.07)"
        depth_op_top = "0.55"
        depth_op_mid = "0.38"
        depth_op_bot = "0.14"
    else:
        shell_top = "#F5F5F7"
        shell_bot = "#EBEBF0"
        card_top = "#FFFFFF"
        card_bot = "#FAFAFC"
        bevel_top = "rgba(255,255,255,0.95)"
        bevel_bot = "rgba(0,0,0,0.09)"
        card_bevel_top = "rgba(255,255,255,0.90)"
        card_bevel_bot = "rgba(0,0,0,0.07)"
        track_bg = "#E5E5EA"
        lurker_seg = "#D1D1D6"
        text_primary = "#1D1D1F"
        text_secondary = "#515154"
        text_muted = "#6E6E73"
        accent = "#0071E3"
        pill_bg = "rgba(0,0,0,0.05)"
        depth_op_top = "0.82"
        depth_op_mid = "0.62"
        depth_op_bot = "0.24"

    palette = get_botanical_palette(health, theme)
    sky_far = render_sky_and_far_peaks(palette, theme=theme)
    bonsai_fg = render_bonsai_foreground(level=level, health=health, theme=theme)
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

    # Apple Fitness ring math (r=24 -> C = 150.80)
    ring_r = 24
    ring_c = 2 * math.pi * ring_r
    ring_offset = ring_c * (1.0 - (moisture / 100.0))

    pill_w = max(84, len(health_label) * 8 + 30)
    pill_x = 786 - pill_w
    pill_dot_x = pill_x + 13
    pill_text_x = pill_x + 24

    visitor_header = "Visitor activity" if lang == "en" else "Aktivitas pengunjung"
    views_suffix = f"{views:,} total"

    title_text = html.escape(f"Community Bonsai Lv.{level} {stage_name}")
    desc_text = html.escape(
        f"Moisture {moisture}%, Status {health_label}, "
        f"Views {views}, Watered {total_waterings}, Just looking {lurkers}."
    )

    watered_rect = (
        f'<rect x="338" y="206" width="{watered_w}" height="10" rx="5" fill="{accent}" class="enter-bar"/>'
        if watered_w > 0
        else ""
    )
    lurker_rect = (
        f'<rect x="{lurker_x}" y="206" width="{lurker_w}" height="10" rx="5" fill="{lurker_seg}"/>'
        if lurker_w > 0
        else ""
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="272" viewBox="0 0 800 272" fill="none" role="img" aria-labelledby="bonsai-title bonsai-desc">
  <title id="bonsai-title">{title_text}</title>
  <desc id="bonsai-desc">{desc_text}</desc>
  <defs>
    <linearGradient id="shell-surf" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{shell_top}"/>
      <stop offset="100%" stop-color="{shell_bot}"/>
    </linearGradient>
    <linearGradient id="shell-bevel" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{bevel_top}"/>
      <stop offset="100%" stop-color="{bevel_bot}"/>
    </linearGradient>
    <linearGradient id="card-surf" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{card_top}"/>
      <stop offset="100%" stop-color="{card_bot}"/>
    </linearGradient>
    <linearGradient id="card-bevel" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{card_bevel_top}"/>
      <stop offset="100%" stop-color="{card_bevel_bot}"/>
    </linearGradient>
    <linearGradient id="app-icon-grad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#34C759"/>
      <stop offset="100%" stop-color="#248A3D"/>
    </linearGradient>
    <linearGradient id="depth-num-grad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="{depth_op_top}"/>
      <stop offset="65%" stop-color="#FFFFFF" stop-opacity="{depth_op_mid}"/>
      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="{depth_op_bot}"/>
    </linearGradient>
    <clipPath id="scene-clip">
      <rect x="14" y="14" width="292" height="244" rx="24"/>
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

  <!-- Outer Apple Chassis (rx 38, padding 14 -> inner viewport rx 24) -->
  <rect x="0.5" y="0.5" width="799" height="271" rx="38" fill="url(#shell-surf)" stroke="url(#shell-bevel)"/>

  <!-- Left Immersive Depth-Effect Alpine Viewport (Daytime in Light, Starry Night in Dark) -->
  <g clip-path="url(#scene-clip)">
    <g transform="translate(14 14)">
      {sky_far}

      <!-- Giant translucent moisture readout positioned high & clear above/behind canopy tips -->
      <text x="146" y="102" text-anchor="middle" font-size="74" font-weight="700" letter-spacing="-0.04em" fill="url(#depth-num-grad)" class="num">{moisture}%</text>

      <!-- Foreground alpine ridges & Bonsai sitting gracefully below/overlapping bottom edge -->
      {bonsai_fg}

      <!-- Top-left calm stage tag & inner glass edge vignette -->
      <text x="18" y="26" font-size="11.5" font-weight="600" fill="rgba(255,255,255,0.88)">{html.escape(stage_text)}</text>
      <rect x="0" y="0" width="292" height="244" fill="url(#glass-vignette)"/>
    </g>
  </g>
  <rect x="14.5" y="14.5" width="291" height="243" rx="24" stroke="url(#card-bevel)" fill="none"/>

  <!-- Right Apple Visual Indicators -->
  <!-- Header with App Icon Tile -->
  <rect x="322" y="18" width="32" height="32" rx="8" fill="url(#app-icon-grad)"/>
  <path d="M332 39c1-6.5 5-10.5 11.5-11.5-1 6.5-5 10.5-11.5 11.5Z" fill="#FFFFFF"/>
  <path d="M332 39l5-5" stroke="#248A3D" stroke-width="1.3" stroke-linecap="round"/>
  <text x="364" y="32" font-size="15.5" font-weight="600" fill="{text_primary}">{html.escape(tr['widget_title'])}</text>
  <text x="364" y="48" font-size="12" font-weight="400" fill="{text_secondary}">{html.escape(subtitle)}</text>

  <!-- Status Capsule -->
  <rect x="{pill_x}" y="21" width="{pill_w}" height="26" rx="13" fill="{pill_bg}" stroke="{card_bevel_bot}"/>
  <circle cx="{pill_dot_x}" cy="34" r="3.5" fill="{status_color}"/>
  <text x="{pill_text_x}" y="38" font-size="12" font-weight="500" fill="{text_primary}">{html.escape(health_label)}</text>

  <!-- Middle Asymmetric Row -->
  <!-- Apple Fitness Tinted Moisture Ring Card -->
  <rect x="322" y="64" width="246" height="94" rx="16" fill="url(#card-surf)" stroke="url(#card-bevel)"/>
  <circle cx="368" cy="111" r="{ring_r}" stroke="{status_color}" stroke-opacity="0.20" stroke-width="6" fill="none"/>
  <circle cx="368" cy="111" r="{ring_r}" stroke="{status_color}" stroke-width="6" stroke-linecap="round"
    stroke-dasharray="{ring_c:.2f}" stroke-dashoffset="{ring_offset:.2f}" transform="rotate(-90 368 111)" fill="none"/>
  <path d="M368 103s-4.5 4.9-4.5 7.6a4.5 4.5 0 0 0 9 0c0-2.7-4.5-7.6-4.5-7.6Z" stroke="{status_color}" stroke-width="1.5" stroke-linejoin="round" fill="none"/>
  <text x="408" y="112" font-size="30" font-weight="600" fill="{text_primary}" letter-spacing="-0.02em" class="num">{moisture}%</text>
  <text x="408" y="131" font-size="12" font-weight="400" fill="{text_secondary}">{html.escape(tr['moisture_label'])} · {html.escape(health_label)}</text>

  <!-- Apple Growth Progress Card -->
  <rect x="580" y="64" width="206" height="94" rx="16" fill="url(#card-surf)" stroke="url(#card-bevel)"/>
  <text x="596" y="88" font-size="12" font-weight="400" fill="{text_secondary}">{html.escape(tr['growth_label'])}</text>
  <text x="770" y="88" text-anchor="end" font-size="12" font-weight="400" fill="{text_muted}" class="num">{html.escape(xp_label)}</text>
  <text x="596" y="115" font-size="16" font-weight="600" fill="{text_primary}">Lv. {level} · {html.escape(stage_name)}</text>
  <rect x="596" y="132" width="174" height="8" rx="4" fill="{track_bg}"/>
  <rect x="596" y="132" width="{xp_bar_w}" height="8" rx="4" fill="{accent}" class="enter-bar"/>

  <!-- Bottom Card: Apple Storage-Style Visitor Care Bar -->
  <rect x="322" y="170" width="464" height="88" rx="16" fill="url(#card-surf)" stroke="url(#card-bevel)"/>
  <text x="338" y="194" font-size="12.5" font-weight="500" fill="{text_primary}">{html.escape(visitor_header)}</text>
  <text x="770" y="194" text-anchor="end" font-size="12" font-weight="400" fill="{text_secondary}" class="num">{html.escape(views_suffix)}</text>

  {watered_rect}
  {lurker_rect}

  <circle cx="342" cy="233" r="3.5" fill="{accent}"/>
  <text x="352" y="237" font-size="11.5" font-weight="400" fill="{text_secondary}">{html.escape(tr['watered_label'])} <tspan font-weight="500" fill="{text_primary}" class="num">{total_waterings:,} ({care_pct:.1f}%)</tspan></text>
  <circle cx="512" cy="233" r="3.5" fill="{lurker_seg}"/>
  <text x="522" y="237" font-size="11.5" font-weight="400" fill="{text_secondary}">{html.escape(tr['lurkers_label'])} <tspan font-weight="500" fill="{text_primary}" class="num">{lurkers:,} ({lurker_pct:.1f}%)</tspan></text>
</svg>
"""


def render_cta_button(theme: str = "dark", lang: str = "en") -> str:
    """Generate an Apple.com-inspired primary pill CTA button SVG."""
    is_dark = theme == "dark"
    tr = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    label = html.escape(tr["cta_label"])

    bg_top = "#1890FF" if is_dark else "#0077ED"
    bg_bot = "#0A84FF" if is_dark else "#0066CC"
    bevel = "rgba(255,255,255,0.28)"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="180" height="38" viewBox="0 0 180 38" fill="none" role="img" aria-label="{label}">
  <defs>
    <linearGradient id="cta-grad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{bg_top}"/>
      <stop offset="100%" stop-color="{bg_bot}"/>
    </linearGradient>
    <linearGradient id="cta-rim" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{bevel}"/>
      <stop offset="100%" stop-color="rgba(255,255,255,0.04)"/>
    </linearGradient>
  </defs>
  <style>
    text {{
      font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', Helvetica, Arial, sans-serif;
    }}
  </style>
  <rect x="0.5" y="0.5" width="179" height="37" rx="18.5" fill="url(#cta-grad)" stroke="url(#cta-rim)"/>
  <path d="M29 12.8s-4.2 4.6-4.2 7.1a4.2 4.2 0 0 0 8.4 0c0-2.5-4.2-7.1-4.2-7.1Z" stroke="#FFFFFF" stroke-width="1.5" stroke-linejoin="round" fill="none"/>
  <text x="43" y="23.5" font-size="13" font-weight="500" fill="#FFFFFF">{label}</text>
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
