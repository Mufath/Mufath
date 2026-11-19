"""Community Bonsai state manager and SVG card generator."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
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

LEVEL_NAMES: Dict[int, str] = {
    1: "Bibit",
    2: "Tunas",
    3: "Bonsai Muda",
    4: "Bonsai Mekar",
    5: "Bonsai Kuno",
}

# Minimum cumulative XP required to reach each level.
LEVEL_THRESHOLDS: Dict[int, int] = {
    1: 0,
    2: 30,
    3: 80,
    4: 160,
    5: 300,
}

HEALTH_META: Dict[str, Dict[str, str]] = {
    "subur": {"label": "Subur", "color": "#22C55E", "hint": "Daun rimbun & bercahaya"},
    "segar": {"label": "Segar", "color": "#38BDF8", "hint": "Kelembaban terjaga baik"},
    "haus": {"label": "Haus", "color": "#F59E0B", "hint": "Mulai kering, butuh air!"},
    "layu": {"label": "Layu", "color": "#EF4444", "hint": "Kritis! Selamatkan dengan siram"},
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
    """Determine health status string from moisture percentage (0-100)."""
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


def _relative_time_id(ts_str: Optional[str], now: datetime) -> str:
    parsed = _parse_iso(ts_str)
    if parsed is None:
        return "-"
    diff_sec = max(0, int((now - parsed).total_seconds()))
    if diff_sec < 60:
        return "baru saja"
    minutes = diff_sec // 60
    if minutes < 60:
        return f"{minutes}m lalu"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}j lalu"
    days = hours // 24
    return f"{days}h lalu"


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _next_level_progress(level: int, xp: int) -> Tuple[float, str]:
    if level >= 5:
        return 100.0, f"{xp} XP • MAX"
    cur_floor = LEVEL_THRESHOLDS[level]
    next_target = LEVEL_THRESHOLDS[level + 1]
    span = max(1, next_target - cur_floor)
    pct = max(0.0, min(100.0, ((xp - cur_floor) / span) * 100.0))
    return pct, f"{xp} / {next_target} XP"


def render_svg_card(
    state: Dict[str, Any],
    theme: str = "dark",
    now: Optional[datetime] = None,
) -> str:
    """Generate the full 800x260 Community Bonsai SVG card for light or dark theme."""
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    is_dark = theme == "dark"

    level = max(1, min(5, int(state.get("level", 1))))
    xp = max(0, int(state.get("xp", 0)))
    moisture = max(0, min(100, int(state.get("moisture", 75))))
    health = state.get("health") or compute_health(moisture)
    if health not in HEALTH_META:
        health = compute_health(moisture)

    total_waterings = max(0, int(state.get("total_waterings", 0)))
    raw_views = max(0, int(state.get("last_known_views", 0)))
    views = max(raw_views, total_waterings)
    lurkers = max(0, views - total_waterings)
    care_pct = (total_waterings / views * 100.0) if views > 0 else 0.0

    stage_name = LEVEL_NAMES.get(level, "Bibit")
    health_info = HEALTH_META[health]
    health_color = health_info["color"]
    health_label = health_info["label"]

    xp_pct, xp_label = _next_level_progress(level, xp)
    moisture_bar_w = round(486 * (moisture / 100.0), 1)
    xp_bar_w = round(486 * (xp_pct / 100.0), 1)

    # Theme tokens aligned with Mufath's GitHub Profile & cool-readme cards.
    card_bg = "#0D1117" if is_dark else "#FFFFFF"
    card_border = "#30363D" if is_dark else "#D0D7DE"
    habitat_bg = "#111824" if is_dark else "#F6F8FA"
    tile_bg = "#161B22" if is_dark else "#F6F8FA"
    tile_border = "#262C36" if is_dark else "#E1E4E8"
    track_bg = "#21262D" if is_dark else "#EAECEF"
    text_primary = "#F0F6FC" if is_dark else "#1F2328"
    text_secondary = "#8B949E" if is_dark else "#59636E"
    accent = "#38BDF8" if is_dark else "#0969DA"
    xp_color = "#A855F7" if is_dark else "#8250DF"
    glow_color = health_color

    last_user = state.get("last_watered_by")
    if last_user:
        rel = _relative_time_id(state.get("last_watered_at"), current)
        footer_left = f"Penyiram terakhir: @{html.escape(_truncate(str(last_user), 18))} ({rel})"
    else:
        footer_left = "Belum ada penyiram — jadilah yang pertama!"

    pixels_svg = render_bonsai_pixels(
        level=level,
        health=health,
        theme=theme,
        origin_x=46,
        origin_y=40,
        pixel_size=7,
    )

    # Ambient sparkles / droplets inside the habitat for visual life.
    if health in ("subur", "segar"):
        ambient_svg = (
            f'<circle cx="52" cy="56" r="2.2" fill="{accent}" class="float-a"/>'
            f'<circle cx="236" cy="72" r="1.8" fill="{health_color}" class="float-b"/>'
            f'<circle cx="220" cy="48" r="1.5" fill="{accent}" class="float-c"/>'
        )
    elif health == "haus":
        ambient_svg = (
            f'<rect x="180" y="28" width="78" height="20" rx="10" fill="{card_bg}" stroke="{health_color}" stroke-width="1"/>'
            f'<text x="219" y="42" text-anchor="middle" font-size="10" font-weight="600" fill="{health_color}">Butuh Air</text>'
        )
    else:
        ambient_svg = (
            f'<rect x="172" y="28" width="86" height="20" rx="10" fill="{card_bg}" stroke="{health_color}" stroke-width="1"/>'
            f'<text x="215" y="42" text-anchor="middle" font-size="10" font-weight="600" fill="{health_color}">Darurat Air!</text>'
        )

    title_text = html.escape(f"Community Bonsai Lv.{level} {stage_name}")
    desc_text = html.escape(
        f"Kelembaban {moisture}%, Status {health_label}, "
        f"Views {views}, Siram {total_waterings}, Cuma Liat {lurkers}."
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="260" viewBox="0 0 800 260" fill="none" role="img" aria-labelledby="bonsai-title bonsai-desc">
  <title id="bonsai-title">{title_text}</title>
  <desc id="bonsai-desc">{desc_text}</desc>
  <defs>
    <radialGradient id="habitat-glow" cx="50%" cy="52%" r="55%">
      <stop offset="0%" stop-color="{glow_color}" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="{glow_color}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <style>
    text {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
    }}
    .mono {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-variant-numeric: tabular-nums;
    }}
    .bar-anim {{
      transform-box: fill-box;
      transform-origin: left center;
      animation: growX 0.9s cubic-bezier(.2,.7,.2,1) both;
    }}
    .float-a {{ animation: floatY 3.2s ease-in-out infinite; }}
    .float-b {{ animation: floatY 4.1s ease-in-out 0.6s infinite; }}
    .float-c {{ animation: floatY 2.8s ease-in-out 1.1s infinite; }}
    .pulse-dot {{ animation: pulseDot 2.2s ease-in-out infinite; }}
    @keyframes growX {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
    @keyframes floatY {{
      0%, 100% {{ transform: translateY(0px); opacity: 0.45; }}
      50% {{ transform: translateY(-5px); opacity: 0.95; }}
    }}
    @keyframes pulseDot {{
      0%, 100% {{ opacity: 0.65; }}
      50% {{ opacity: 1; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      * {{ animation: none !important; }}
    }}
  </style>

  <!-- Outer Card -->
  <rect x="0.5" y="0.5" width="799" height="259" rx="12" fill="{card_bg}" stroke="{card_border}"/>

  <!-- Left Habitat Panel -->
  <rect x="18" y="18" width="252" height="224" rx="10" fill="{habitat_bg}" stroke="{tile_border}"/>
  <rect x="18" y="18" width="252" height="224" rx="10" fill="url(#habitat-glow)"/>
  {ambient_svg}
  <g shape-rendering="crispEdges">
    {pixels_svg}
  </g>
  <text x="144" y="229" text-anchor="middle" font-size="11.5" font-weight="600" fill="{text_secondary}">Stage {level}/5 • {html.escape(stage_name)}</text>

  <!-- Right Panel Header -->
  <g transform="translate(292 27)" fill="{health_color}">
    <path d="M7 13V7.5C7 4.8 4.8 3 2 3c0 2.8 1.8 4.8 4.5 5M7 9.5C7 6.5 9.2 4.5 12 4.5c0 2.8-1.8 4.8-4.5 5" stroke="{health_color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  </g>
  <text x="311" y="40" font-size="15" font-weight="700" fill="{text_primary}" letter-spacing="0.02em">COMMUNITY BONSAI</text>
  <text x="292" y="57" font-size="11.5" fill="{text_secondary}">{html.escape(health_info['hint'])}</text>

  <!-- Health Pill -->
  <rect x="688" y="24" width="94" height="24" rx="12" fill="{tile_bg}" stroke="{health_color}" stroke-opacity="0.65"/>
  <circle cx="703" cy="36" r="4" fill="{health_color}" class="pulse-dot"/>
  <text x="714" y="40" font-size="11.5" font-weight="600" fill="{text_primary}">{html.escape(health_label)}</text>

  <!-- Moisture Bar -->
  <path d="M298 70.5c0 0-4.5 4.9-4.5 7.6a4.5 4.5 0 0 0 9 0c0-2.7-4.5-7.6-4.5-7.6Z" fill="{health_color}"/>
  <text x="309" y="81" font-size="12" font-weight="600" fill="{text_primary}">Kelembaban Air</text>
  <text x="778" y="81" text-anchor="end" font-size="12" font-weight="700" fill="{health_color}" class="mono">{moisture}%</text>
  <rect x="292" y="89" width="486" height="9" rx="4.5" fill="{track_bg}"/>
  <rect x="292" y="89" width="{moisture_bar_w}" height="9" rx="4.5" fill="{health_color}" class="bar-anim"/>

  <!-- Growth XP Bar -->
  <path d="M293 121.5c.8-4.8 4.2-8.2 9.5-8.8-.6 5.3-4 8.7-8.8 9.5l-.7-.7Z" fill="{xp_color}"/>
  <text x="309" y="121" font-size="12" font-weight="600" fill="{text_primary}">Pertumbuhan (Lv.{level} {html.escape(stage_name)})</text>
  <text x="778" y="121" text-anchor="end" font-size="12" font-weight="700" fill="{accent}" class="mono">{html.escape(xp_label)}</text>
  <rect x="292" y="129" width="486" height="9" rx="4.5" fill="{track_bg}"/>
  <rect x="292" y="129" width="{xp_bar_w}" height="9" rx="4.5" fill="{xp_color}" class="bar-anim"/>

  <!-- Stats Grid (Profile Views Replacement) -->
  <rect x="292" y="154" width="154" height="58" rx="8" fill="{tile_bg}" stroke="{tile_border}"/>
  <path d="M304 168.5s2.4-4 6-4 6 4 6 4-2.4 4-6 4-6-4-6-4Z" stroke="{text_secondary}" stroke-width="1.3" fill="none"/>
  <circle cx="310" cy="168.5" r="1.5" fill="{text_secondary}"/>
  <text x="321" y="172" font-size="10.5" font-weight="600" fill="{text_secondary}" letter-spacing="0.04em">PROFILE VIEWS</text>
  <text x="304" y="196" font-size="19" font-weight="700" fill="{text_primary}" class="mono">{views:,}</text>
  <text x="436" y="195" text-anchor="end" font-size="10" fill="{text_secondary}">total</text>

  <rect x="458" y="154" width="154" height="58" rx="8" fill="{tile_bg}" stroke="{tile_border}"/>
  <path d="M474.5 163.5s-3.5 3.8-3.5 5.8a3.5 3.5 0 0 0 7 0c0-2-3.5-5.8-3.5-5.8Z" fill="{accent}"/>
  <text x="484" y="172" font-size="10.5" font-weight="600" fill="{text_secondary}" letter-spacing="0.04em">SUDAH SIRAM</text>
  <text x="470" y="196" font-size="19" font-weight="700" fill="{accent}" class="mono">{total_waterings:,}</text>
  <text x="602" y="195" text-anchor="end" font-size="10" fill="{text_secondary}">{care_pct:.1f}%</text>

  <rect x="624" y="154" width="154" height="58" rx="8" fill="{tile_bg}" stroke="{tile_border}"/>
  <circle cx="641" cy="166.5" r="2.2" stroke="{text_secondary}" stroke-width="1.3" fill="none"/>
  <path d="M636.5 172.5c.6-1.8 2.3-2.7 4.5-2.7s3.9.9 4.5 2.7" stroke="{text_secondary}" stroke-width="1.3" stroke-linecap="round" fill="none"/>
  <text x="651" y="172" font-size="10.5" font-weight="600" fill="{text_secondary}" letter-spacing="0.04em">CUMA LIAT</text>
  <text x="636" y="196" font-size="19" font-weight="700" fill="{text_primary}" class="mono">{lurkers:,}</text>
  <text x="768" y="195" text-anchor="end" font-size="10" fill="{text_secondary}">pasif</text>

  <!-- Footer -->
  <text x="292" y="236" font-size="11.5" fill="{text_secondary}">{footer_left}</text>
  <text x="778" y="236" text-anchor="end" font-size="11" fill="{accent}">Klik "Siram Bonsai" ↓</text>
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


def write_cards(cards_dir: Path, state: Dict[str, Any], now: Optional[datetime] = None) -> None:
    """Write both dark and light bonsai SVG cards into cards_dir."""
    cards_dir.mkdir(parents=True, exist_ok=True)
    for theme in ("dark", "light"):
        svg = render_svg_card(state, theme=theme, now=now)
        (cards_dir / f"bonsai-{theme}.svg").write_text(svg, encoding="utf-8")


def build_issue_comment(result: Dict[str, Any], state: Dict[str, Any]) -> str:
    """Create a friendly Indonesian GitHub Issue reply summarizing the watering outcome."""
    user = result["user"]
    stage_name = LEVEL_NAMES.get(state["level"], "Bibit")
    health_label = HEALTH_META.get(state["health"], {}).get("label", state["health"])

    if result["status"] == "cooldown":
        return (
            f"Terima kasih @{user}! ⏳ Bonsai baru saja kamu siram sebelumnya.\n\n"
            f"Tunggu sekitar **{result['remaining_minutes']} menit** lagi sebelum menyiram ulang agar tanaman tidak overwatering.\n\n"
            f"- **Level:** Lv.{state['level']} ({stage_name})\n"
            f"- **Kelembaban:** {state['moisture']}% ({health_label})"
        )

    lines = [
        f"Terima kasih @{user} sudah menyiram Community Bonsai! 💧🌱",
        "",
        f"- **XP didapat:** +{result['xp_gained']} XP"
        + (" *(Rescue Bonus karena tanaman sedang haus/layu!)*" if result.get("rescue_bonus") else ""),
    ]
    if result.get("leveled_up"):
        lines.append(
            f"- 🎉 **LEVEL UP!** Bonsai tumbuh dari **Lv.{result['old_level']}** ke **Lv.{state['level']} ({stage_name})**!"
        )
    else:
        lines.append(f"- **Level saat ini:** Lv.{state['level']} ({stage_name}) — {state['xp']} XP")
    lines.extend(
        [
            f"- **Kelembaban air:** {state['moisture']}% ({health_label})",
            f"- **Total siraman komunitas:** {state['total_waterings']}x",
            "",
            "Issue ini ditutup otomatis. Cek lagi profil [@Mufath](https://github.com/Mufath) untuk melihat tampilan terbaru!",
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
        comment = build_issue_comment(result, state)
    elif args.mode == "decay":
        result = decay_bonsai(state, now=now, force=args.force_decay)
    elif args.mode in ("sync", "render"):
        state["health"] = compute_health(int(state.get("moisture", 75)))
        state["level"] = compute_level(int(state.get("xp", 0)))

    save_state(state_path, state)
    write_cards(cards_dir, state, now=now)

    _write_github_output(
        {
            "status": str(result.get("status", "ok")),
            "comment": comment,
        }
    )
    print(json.dumps({"result": result, "state_summary": {
        "level": state["level"],
        "xp": state["xp"],
        "moisture": state["moisture"],
        "health": state["health"],
        "total_waterings": state["total_waterings"],
        "last_known_views": state["last_known_views"],
    }}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
