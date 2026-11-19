"""Community Bonsai state manager and Apple-inspired SVG widget generator."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bonsai_art import render_bonsai_pixels

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

HEALTH_COLORS: Dict[str, str] = {
    "subur": "#34D399",
    "segar": "#38BDF8",
    "haus": "#FBBF24",
    "layu": "#FB7185",
}

TRANSLATIONS: Dict[str, Dict[str, Any]] = {
    "en": {
        "widget_header": "COMMUNITY BONSAI",
        "stage_prefix": "STAGE",
        "moisture_unit": "MOISTURE",
        "growth_prefix": "Growth",
        "xp_max": "MAX",
        "views_label": "PROFILE VIEWS",
        "watered_label": "WATERED",
        "lurkers_label": "JUST LOOKING",
        "last_watered": "Last watered by @{user} ({rel})",
        "no_waterings": "Waiting for the first drop — click below to water!",
        "levels": {
            1: "Sprout",
            2: "Sapling",
            3: "Young Bonsai",
            4: "Blooming Bonsai",
            5: "Ancient Bonsai",
        },
        "health": {
            "subur": "THRIVING",
            "segar": "HEALTHY",
            "haus": "THIRSTY",
            "layu": "WILTED",
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
        "comment_watered_header": "Thanks @{user} for watering the Community Bonsai! 💧🌱",
        "comment_xp": "- **XP gained:** +{xp} XP",
        "comment_rescue": " *(Rescue Bonus for saving a thirsty bonsai!)*",
        "comment_level_up": "- 🎉 **LEVEL UP!** The bonsai grew from **Lv.{old}** to **Lv.{new} ({stage})**!",
        "comment_level_cur": "- **Current stage:** Lv.{level} ({stage}) — {xp} XP",
        "comment_moisture": "- **Moisture:** {moisture}% ({health})",
        "comment_total": "- **Total community waterings:** {total}x",
        "comment_footer": "This issue was closed automatically. Visit [@Mufath](https://github.com/Mufath) to see the updated widget!",
    },
    "id": {
        "widget_header": "COMMUNITY BONSAI",
        "stage_prefix": "TAHAP",
        "moisture_unit": "AIR",
        "growth_prefix": "Pertumbuhan",
        "xp_max": "MAKS",
        "views_label": "DILIHAT",
        "watered_label": "DISIRAM",
        "lurkers_label": "CUMA LIAT",
        "last_watered": "Disiram terakhir oleh @{user} ({rel})",
        "no_waterings": "Belum ada yang menyiram — klik tombol di bawah!",
        "levels": {
            1: "Bibit",
            2: "Tunas",
            3: "Bonsai Muda",
            4: "Bonsai Mekar",
            5: "Bonsai Kuno",
        },
        "health": {
            "subur": "SUBUR",
            "segar": "SEGAR",
            "haus": "HAUS",
            "layu": "LAYU",
        },
        "time": {
            "just_now": "baru saja",
            "m": "{n}m lalu",
            "h": "{n}j lalu",
            "d": "{n}h lalu",
        },
        "comment_cooldown": (
            "Terima kasih @{user}! Bonsai baru saja kamu siram sebelumnya.\n\n"
            "Tunggu sekitar **{minutes} menit** lagi sebelum menyiram ulang agar tanaman tidak overwatering.\n\n"
            "- **Tahap:** Lv.{level} ({stage})\n"
            "- **Kelembaban:** {moisture}% ({health})"
        ),
        "comment_watered_header": "Terima kasih @{user} sudah menyiram Community Bonsai! 💧🌱",
        "comment_xp": "- **XP didapat:** +{xp} XP",
        "comment_rescue": " *(Rescue Bonus karena tanaman sedang haus/layu!)*",
        "comment_level_up": "- 🎉 **LEVEL UP!** Bonsai tumbuh dari **Lv.{old}** ke **Lv.{new} ({stage})**!",
        "comment_level_cur": "- **Tahap saat ini:** Lv.{level} ({stage}) — {xp} XP",
        "comment_moisture": "- **Kelembaban air:** {moisture}% ({health})",
        "comment_total": "- **Total siraman komunitas:** {total}x",
        "comment_footer": "Issue ini ditutup otomatis. Kunjungi [@Mufath](https://github.com/Mufath) untuk melihat tampilan terbaru!",
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
        return 100.0, f"{xp} XP • {max_word}"
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
    """Generate the Apple-style 800x260 Community Bonsai frosted glass widget SVG."""
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    is_dark = theme == "dark"
    tr = TRANSLATIONS.get(lang, TRANSLATIONS["en"])

    level = max(1, min(5, int(state.get("level", 1))))
    xp = max(0, int(state.get("xp", 0)))
    moisture = max(0, min(100, int(state.get("moisture", 75))))
    health = state.get("health") or compute_health(moisture)
    if health not in HEALTH_COLORS:
        health = compute_health(moisture)

    total_waterings = max(0, int(state.get("total_waterings", 0)))
    raw_views = max(0, int(state.get("last_known_views", 0)))
    views = max(raw_views, total_waterings)
    lurkers = max(0, views - total_waterings)

    stage_name = tr["levels"].get(level, tr["levels"][1])
    health_label = tr["health"].get(health, tr["health"]["segar"])
    health_color = HEALTH_COLORS[health]

    xp_pct, xp_label = _next_level_progress(level, xp, tr["xp_max"])
    xp_bar_w = round(414 * (xp_pct / 100.0), 1)

    last_user = state.get("last_watered_by")
    if last_user:
        rel = _relative_time(state.get("last_watered_at"), current, lang)
        card1_sub = tr["last_watered"].format(
            user=_truncate(str(last_user), 18),
            rel=rel,
        )
    else:
        card1_sub = tr["no_waterings"]

    # Apple StandBy / VisionOS-inspired frosted atmospheric tokens.
    if is_dark:
        mesh_start = "#3B2846"
        mesh_mid = "#20304C"
        mesh_end = "#0F172A"
        bloom_a = "#E19AA8"
        bloom_b = "#38BDF8"
        rim_top = "rgba(255,255,255,0.48)"
        rim_bot = "rgba(255,255,255,0.12)"
        outer_halo = "rgba(255,255,255,0.10)"
        card1_top = "#FFFFFF"
        card1_bot = "#E2E8F0"
        card1_opacity = "0.18"
        card1_border = "rgba(255,255,255,0.34)"
        card1_text = "#FFFFFF"
        card1_muted = "rgba(255,255,255,0.72)"
        card2_top = "#FFFFFF"
        card2_bot = "#94A3B8"
        card2_opacity = "0.08"
        card2_border = "rgba(255,255,255,0.20)"
        card2_text = "#F8FAFC"
        card2_muted = "rgba(255,255,255,0.66)"
        divider_color = "rgba(255,255,255,0.14)"
        track_bg = "rgba(255,255,255,0.18)"
        xp_fill = "#38BDF8"
        icon_box_stroke = "rgba(255,255,255,0.88)"
        hero_text = "#FFFFFF"
        hero_muted = "rgba(255,255,255,0.74)"
    else:
        mesh_start = "#D8A7B1"
        mesh_mid = "#6F88A6"
        mesh_end = "#334E70"
        bloom_a = "#F7CAD4"
        bloom_b = "#7DD3FC"
        rim_top = "rgba(255,255,255,0.94)"
        rim_bot = "rgba(255,255,255,0.38)"
        outer_halo = "rgba(15,23,42,0.10)"
        card1_top = "#FFFFFF"
        card1_bot = "#F8FAFC"
        card1_opacity = "0.95"
        card1_border = "rgba(255,255,255,0.98)"
        card1_text = "#1D1D1F"
        card1_muted = "#6E6E73"
        card2_top = "#FFFFFF"
        card2_bot = "#DCE6F2"
        card2_opacity = "0.68"
        card2_border = "rgba(255,255,255,0.78)"
        card2_text = "#1D1D1F"
        card2_muted = "#475569"
        divider_color = "rgba(29,29,31,0.12)"
        track_bg = "rgba(29,29,31,0.10)"
        xp_fill = "#007AFF"
        icon_box_stroke = "#1D1D1F"
        hero_text = "#FFFFFF"
        hero_muted = "rgba(255,255,255,0.78)"

    pixels_svg = render_bonsai_pixels(
        level=level,
        health=health,
        theme=theme,
        origin_x=76,
        origin_y=30,
        pixel_size=6,
    )

    title_text = html.escape(f"Community Bonsai Lv.{level} {stage_name}")
    desc_text = html.escape(
        f"Moisture {moisture}%, Status {health_label}, "
        f"Views {views}, Watered {total_waterings}, Just Looking {lurkers}."
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="260" viewBox="0 0 800 260" fill="none" role="img" aria-labelledby="bonsai-title bonsai-desc">
  <title id="bonsai-title">{title_text}</title>
  <desc id="bonsai-desc">{desc_text}</desc>
  <defs>
    <linearGradient id="apple-mesh" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{mesh_start}"/>
      <stop offset="48%" stop-color="{mesh_mid}"/>
      <stop offset="100%" stop-color="{mesh_end}"/>
    </linearGradient>
    <radialGradient id="bloom-rose" cx="16%" cy="20%" r="48%">
      <stop offset="0%" stop-color="{bloom_a}" stop-opacity="0.55"/>
      <stop offset="100%" stop-color="{bloom_a}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="bloom-sky" cx="78%" cy="82%" r="55%">
      <stop offset="0%" stop-color="{bloom_b}" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="{bloom_b}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="glass-rim" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{rim_top}"/>
      <stop offset="55%" stop-color="{rim_bot}"/>
      <stop offset="100%" stop-color="{rim_top}"/>
    </linearGradient>
    <linearGradient id="card1-fill" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{card1_top}" stop-opacity="{card1_opacity}"/>
      <stop offset="100%" stop-color="{card1_bot}" stop-opacity="{card1_opacity}"/>
    </linearGradient>
    <linearGradient id="card2-fill" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{card2_top}" stop-opacity="{card2_opacity}"/>
      <stop offset="100%" stop-color="{card2_bot}" stop-opacity="{card2_opacity}"/>
    </linearGradient>
    <clipPath id="shell-clip">
      <rect x="6" y="6" width="788" height="248" rx="34"/>
    </clipPath>
    <filter id="soft-grain" x="0%" y="0%" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="7" result="noise"/>
      <feColorMatrix type="saturate" values="0" in="noise" result="monoNoise"/>
      <feComponentTransfer in="monoNoise" result="alphaNoise">
        <feFuncA type="table" tableValues="0 0.045"/>
      </feComponentTransfer>
    </filter>
  </defs>
  <style>
    text {{
      font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Segoe UI', Helvetica, Arial, sans-serif;
    }}
    .num {{
      font-variant-numeric: tabular-nums;
    }}
    .bar-anim {{
      transform-box: fill-box;
      transform-origin: left center;
      animation: growX 0.85s cubic-bezier(.22,1,.36,1) both;
    }}
    .pulse-dot {{ animation: pulseDot 2.4s ease-in-out infinite; }}
    @keyframes growX {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
    @keyframes pulseDot {{
      0%, 100% {{ opacity: 0.7; }}
      50% {{ opacity: 1; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      * {{ animation: none !important; }}
    }}
  </style>

  <!-- Outer subtle Apple bezel halo -->
  <rect x="2" y="2" width="796" height="256" rx="37" stroke="{outer_halo}" stroke-width="2"/>

  <!-- Main Atmospheric Frosted Widget Shell -->
  <g clip-path="url(#shell-clip)">
    <rect x="6" y="6" width="788" height="248" rx="34" fill="url(#apple-mesh)"/>
    <rect x="6" y="6" width="788" height="248" rx="34" fill="url(#bloom-rose)"/>
    <rect x="6" y="6" width="788" height="248" rx="34" fill="url(#bloom-sky)"/>
    <rect x="6" y="6" width="788" height="248" filter="url(#soft-grain)"/>
  </g>
  <rect x="6" y="6" width="788" height="248" rx="34" stroke="url(#glass-rim)" stroke-width="2.2"/>

  <!-- Left Hero Zone -->
  <circle cx="40" cy="36" r="4" fill="{health_color}" class="pulse-dot"/>
  <text x="52" y="40" font-size="11.5" font-weight="700" fill="{hero_muted}" letter-spacing="0.08em">{html.escape(tr['stage_prefix'])} {level}/5 • {html.escape(stage_name.upper())}</text>

  <!-- Bonsai Pixel Art -->
  <ellipse cx="160" cy="174" rx="46" ry="5" fill="rgba(0,0,0,0.22)"/>
  <g shape-rendering="crispEdges">
    {pixels_svg}
  </g>

  <!-- Apple StandBy-style Status & Large Readout -->
  <path d="M42 181.5s-4.5 4.8-4.5 7.5a4.5 4.5 0 0 0 9 0c0-2.7-4.5-7.5-4.5-7.5Z" fill="{health_color}"/>
  <text x="53" y="193" font-size="13" font-weight="700" fill="{hero_text}" letter-spacing="0.06em">{html.escape(health_label)}</text>
  <text x="36" y="233" font-size="38" font-weight="700" fill="{hero_text}" letter-spacing="-0.03em" class="num">{moisture}%<tspan dx="6" font-size="14" font-weight="600" letter-spacing="0.06em" fill="{hero_muted}">{html.escape(tr['moisture_unit'])}</tspan></text>

  <!-- Right Stacked Apple Cards -->
  <text x="322" y="39" font-size="12" font-weight="700" fill="{hero_muted}" letter-spacing="0.08em">{html.escape(tr['widget_header'])}</text>

  <!-- Card 1: Growth & Latest Watering -->
  <rect x="316" y="50" width="450" height="82" rx="20" fill="url(#card1-fill)" stroke="{card1_border}" stroke-width="1.2"/>
  <rect x="334" y="62" width="20" height="20" rx="6" stroke="{icon_box_stroke}" stroke-width="1.7" fill="none"/>
  <path d="M339.5 72.3l3.1 3.1 6-6.2" stroke="{xp_fill}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <text x="364" y="77" font-size="15" font-weight="600" fill="{card1_text}">{html.escape(tr['growth_prefix'])} • Lv.{level} {html.escape(stage_name)}</text>
  <text x="748" y="77" text-anchor="end" font-size="13.5" font-weight="600" fill="{xp_fill}" class="num">{html.escape(xp_label)}</text>
  <rect x="334" y="92" width="414" height="6" rx="3" fill="{track_bg}"/>
  <rect x="334" y="92" width="{xp_bar_w}" height="6" rx="3" fill="{xp_fill}" class="bar-anim"/>
  <text x="334" y="118" font-size="12" fill="{card1_muted}">{html.escape(card1_sub)}</text>

  <!-- Card 2: Frosted Glass Visitor Insights (Profile Views Replacement) -->
  <rect x="316" y="144" width="450" height="74" rx="20" fill="url(#card2-fill)" stroke="{card2_border}" stroke-width="1.2"/>
  <line x1="466" y1="158" x2="466" y2="204" stroke="{divider_color}" stroke-width="1"/>
  <line x1="616" y1="158" x2="616" y2="204" stroke="{divider_color}" stroke-width="1"/>

  <text x="391" y="170" text-anchor="middle" font-size="10.5" font-weight="700" fill="{card2_muted}" letter-spacing="0.06em">{html.escape(tr['views_label'])}</text>
  <text x="391" y="199" text-anchor="middle" font-size="22" font-weight="700" fill="{card2_text}" class="num">{views:,}</text>

  <text x="541" y="170" text-anchor="middle" font-size="10.5" font-weight="700" fill="{card2_muted}" letter-spacing="0.06em">{html.escape(tr['watered_label'])}</text>
  <text x="541" y="199" text-anchor="middle" font-size="22" font-weight="700" fill="{xp_fill}" class="num">{total_waterings:,}</text>

  <text x="691" y="170" text-anchor="middle" font-size="10.5" font-weight="700" fill="{card2_muted}" letter-spacing="0.06em">{html.escape(tr['lurkers_label'])}</text>
  <text x="691" y="199" text-anchor="middle" font-size="22" font-weight="700" fill="{card2_text}" class="num">{lurkers:,}</text>

  <!-- Bottom Apple Pager Indicator -->
  <rect x="490" y="232" width="102" height="5" rx="2.5" fill="rgba(255,255,255,0.28)"/>
  <rect x="528" y="232" width="38" height="5" rx="2.5" fill="#FFFFFF" fill-opacity="0.92"/>
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
    """Write both dark and light bonsai SVG cards into cards_dir."""
    cards_dir.mkdir(parents=True, exist_ok=True)
    for theme in ("dark", "light"):
        svg = render_svg_card(state, theme=theme, lang=lang, now=now)
        (cards_dir / f"bonsai-widget-{theme}.svg").write_text(svg, encoding="utf-8")


def build_issue_comment(
    result: Dict[str, Any],
    state: Dict[str, Any],
    lang: str = "en",
) -> str:
    """Create a friendly GitHub Issue reply summarizing the watering outcome."""
    tr = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    user = result["user"]
    stage_name = tr["levels"].get(state["level"], tr["levels"][1])
    health_label = tr["health"].get(state["health"], state["health"]).title()

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
