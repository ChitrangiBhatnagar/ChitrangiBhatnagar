from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

COUNT_RE = re.compile(r"^(\d+|No) contribution", re.IGNORECASE)


def _parse_int(value: str | None) -> int:
    if not value:
        return 0
    return int(value)


def _count_from_tooltip(text: str) -> int:
    match = COUNT_RE.match(text.strip())
    if not match:
        return 0
    token = match.group(1)
    return 0 if token.lower() == "no" else int(token)


def _streaks(days: list[dict[str, object]]) -> tuple[int, int]:
    ordered = sorted(days, key=lambda item: str(item["date"]))
    current = 0
    longest = 0
    running = 0
    today = datetime.now(timezone.utc).date().isoformat()
    for day in ordered:
        count = int(day["count"])
        if count > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0
    for day in reversed(ordered):
        if str(day["date"]) > today:
            continue
        if int(day["count"]) > 0:
            current += 1
        else:
            break
    return current, longest


def fetch_contributions(username: str) -> dict[str, object]:
    url = f"https://github.com/users/{username}/contributions"
    response = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    tooltips: dict[str, int] = {}
    for tip in soup.select("tool-tip[for]"):
        target = tip.get("for")
        if target:
            tooltips[target] = _count_from_tooltip(tip.get_text(" ", strip=True))

    days: list[dict[str, object]] = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        date = cell.get("data-date")
        if not date:
            continue
        cell_id = cell.get("id") or ""
        count = tooltips.get(cell_id)
        if count is None:
            count = _parse_int(cell.get("data-count"))
        days.append({
            "date": date,
            "count": count,
            "level": _parse_int(cell.get("data-level")),
        })

    days.sort(key=lambda item: str(item["date"]))
    if not days:
        raise RuntimeError("No contribution cells found in GitHub response")

    heading = soup.select_one("#js-contribution-activity-description")
    heading_total = None
    if heading:
        digits = re.sub(r"[^\d]", "", heading.get_text(" ", strip=True).split("contribution")[0])
        if digits:
            heading_total = int(digits)

    counts = Counter(int(day["count"]) for day in days)
    best_day = max(days, key=lambda item: (int(item["count"]), str(item["date"])))
    current_streak, longest_streak = _streaks(days)
    monthly_totals = Counter(str(day["date"])[0:7] for day in days)
    cell_total = sum(int(day["count"]) for day in days)

    payload = {
        "username": username,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "days": days,
        "stats": {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "best_day": {"date": best_day["date"], "count": best_day["count"]},
            "month_totals": dict(sorted(monthly_totals.items())),
            "levels": dict(sorted(counts.items())),
            "total": heading_total if heading_total is not None else cell_total,
        },
    }
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch public GitHub contribution data.")
    parser.add_argument("--username", default=os.environ.get("GITHUB_USERNAME", "ChitrangiBhatnagar"), help="GitHub username")
    parser.add_argument("--output", type=Path, default=Path("data/contributions.json"), help="Output JSON path")
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = fetch_contributions(args.username)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {args.output} ({len(payload['days'])} days, {payload['stats']['total']} contributions)")  # type: ignore[index]


if __name__ == "__main__":
    main()
