from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

MONTH_NAMES = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


def _parse_int(value: str | None) -> int:
    if not value:
        return 0
    return int(value)


def _streaks(days: list[dict[str, object]]) -> tuple[int, int]:
    ordered = sorted(days, key=lambda item: item["date"])
    current = 0
    longest = 0
    running = 0
    today = datetime.utcnow().date().isoformat()
    for day in ordered:
        count = int(day["count"])
        if count > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0
    for day in reversed(ordered):
        if day["date"] > today:
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

    days: list[dict[str, object]] = []
    for day in soup.select("td[data-date]"):
        date = day.get("data-date")
        count = _parse_int(day.get("data-count"))
        level = _parse_int(day.get("data-level"))
        days.append({"date": date, "count": count, "level": level})

    if not days:
        raise RuntimeError("No contribution cells found in GitHub response")

    counts = Counter(day["count"] for day in days)
    best_day = max(days, key=lambda item: (int(item["count"]), str(item["date"])))
    current_streak, longest_streak = _streaks(days)
    monthly_totals = Counter(str(day["date"])[0:7] for day in days)

    payload = {
        "username": username,
        "fetched_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "days": days,
        "stats": {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "best_day": {"date": best_day["date"], "count": best_day["count"]},
            "month_totals": dict(sorted(monthly_totals.items())),
            "levels": dict(sorted(counts.items())),
            "total": sum(int(day["count"]) for day in days),
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


if __name__ == "__main__":
    main()
