"""jp-office: 日本の祝日・営業日・和暦・年度ユーティリティ(読み取り専用)."""
import re
import sys
from datetime import date, timedelta

import jpholiday

ERA_STARTS = {"明治": 1868, "大正": 1912, "昭和": 1926, "平成": 1989, "令和": 2019}
ERA_ABBREV = {"M": "明治", "T": "大正", "S": "昭和", "H": "平成", "R": "令和"}
# 元号の切替日(この日以降が新元号)
ERA_BOUNDARIES = [
    (date(2019, 5, 1), "令和"),
    (date(1989, 1, 8), "平成"),
    (date(1926, 12, 25), "昭和"),
    (date(1912, 7, 30), "大正"),
    (date(1868, 1, 25), "明治"),
]
_FULL = re.compile(r"(明治|大正|昭和|平成|令和)(元|\d{1,2})年(\d{1,2})月(\d{1,2})日")
_ABBR = re.compile(r"\b([MTSHRmtshr])(\d{1,2})[./](\d{1,2})[./](\d{1,2})\b")
YEAREND_DAYS = {(12, 29), (12, 30), (12, 31), (1, 1), (1, 2), (1, 3)}


def is_holiday(d: date) -> str | None:
    return jpholiday.is_holiday_name(d)


def _is_off(d: date, exclude_yearend: bool) -> bool:
    if d.weekday() >= 5 or jpholiday.is_holiday(d):
        return True
    return exclude_yearend and (d.month, d.day) in YEAREND_DAYS


def add_business_days(d: date, n: int, *, exclude_yearend: bool = False) -> date:
    step = 1 if n >= 0 else -1
    remaining = abs(n)
    cur = d
    while remaining > 0:
        cur += timedelta(days=step)
        if not _is_off(cur, exclude_yearend):
            remaining -= 1
    return cur


def wareki_to_iso(s: str) -> str | None:
    m = _FULL.search(s)
    if m:
        era, y, mo, dy = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
        year = ERA_STARTS[era] + (1 if y == "元" else int(y)) - 1
    else:
        m = _ABBR.search(s)
        if not m:
            return None
        era = ERA_ABBREV[m.group(1).upper()]
        year = ERA_STARTS[era] + int(m.group(2)) - 1
        mo, dy = int(m.group(3)), int(m.group(4))
    try:
        return date(year, mo, dy).isoformat()
    except ValueError:
        return None


def iso_to_wareki(s: str) -> str:
    d = date.fromisoformat(s)
    for boundary, era in ERA_BOUNDARIES:
        if d >= boundary:
            n = d.year - ERA_STARTS[era] + 1
            y = "元" if n == 1 else str(n)
            return f"{era}{y}年{d.month}月{d.day}日"
    raise ValueError(f"unsupported date: {s}")


def fiscal_year(d: date) -> int:
    return d.year if d.month >= 4 else d.year - 1


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(argv) < 2:
        print("usage: jp_dates.py holiday|addbiz|wareki|fy ...")
        return 1
    cmd = argv[1]
    if cmd == "holiday":
        name = is_holiday(date.fromisoformat(argv[2]))
        print(name or "祝日ではありません")
    elif cmd == "addbiz":
        opts = "--exclude-yearend" in argv
        print(add_business_days(date.fromisoformat(argv[2]), int(argv[3]), exclude_yearend=opts))
    elif cmd == "wareki":
        print(wareki_to_iso(argv[2]) or "和暦として解釈できません")
    elif cmd == "fy":
        print(fiscal_year(date.fromisoformat(argv[2])))
    else:
        print(f"unknown command: {cmd}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
