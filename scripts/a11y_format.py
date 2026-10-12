#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mcd-a11y-counter · 老年友好格式化工具

把 mcd-mcp 返回的原始数值，转成能被读屏软件正确朗读、老年人一眼看懂的中文短句。

用法:
    python a11y_format.py money 34.5
    python a11y_format.py money 26
    python a11y_format.py walk 235
    python a11y_format.py clock 23:00
    python a11y_format.py open --start 06:30 --end 23:00 --now 20:46
    python a11y_format.py open --start 00:00 --end 23:59
    python a11y_format.py demo

仅依赖标准库。所有换算规则见 SKILL.md 第 1 步与第 12 条规约。
"""

from __future__ import annotations

import argparse
import math
import sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure") and (
    (sys.stdout.encoding or "").lower().replace("-", "") != "utf8"
):
    sys.stdout.reconfigure(encoding="utf-8")


# ---------------------------------------------------------------- 参数

# 老年步速（米/分钟）。成年人常用经验值是 80 m/min，这里刻意取保守值：
# 已计入等红灯、绕行、步幅下降与路面不平带来的额外时间。
WALK_SPEED_MPM = 50

# 超过这个距离就建议改送外送：16 分钟 * 50 m/min
WALK_FAR_METERS = 800

# 打烊倒计时的两个预警门槛（分钟）
URGENT_MINUTES = 30
NOTICE_MINUTES = 60


# ---------------------------------------------------------------- 金额

def money_to_chinese(value: float) -> str:
    """34.5 -> '34 元 5 角'；26 -> '26 元'；0.5 -> '5 角'。

    读屏软件会把 '¥34.5' 读成 '¥三十四点五元'，必须转换。
    """
    yuan = int(value)
    cents = int(round((value - yuan) * 100))
    jiao, fen = divmod(cents, 10)

    if jiao and fen:
        tail = f"{jiao} 角 {fen} 分"
    elif jiao:
        tail = f"{jiao} 角"
    elif fen:
        tail = f"零 {fen} 分"
    else:
        tail = None

    if yuan == 0:
        return tail if tail else "0 元"
    return f"{yuan} 元 {tail}" if tail else f"{yuan} 元"


# ---------------------------------------------------------------- 步行

def walk_to_chinese(distance_m: float) -> tuple[int, str, bool]:
    """把 distance 字段换算成老年人能判断的话术。

    返回 (走路分钟, 话术, 是否建议改外送)。
    """
    if distance_m < 50:
        return 0, "就在跟前", False

    minutes = max(1, math.ceil(distance_m / WALK_SPEED_MPM))

    if minutes <= 5:
        phrase = f"走路 {minutes} 分钟就到"
    elif minutes <= 10:
        phrase = f"走路 {minutes} 分钟"
    elif minutes <= 16:
        phrase = f"走路要 {minutes} 分钟，稍微有点远"
    else:
        phrase = f"走路要 {minutes} 分钟，太远了。要不要改成送到家？"

    return minutes, phrase, distance_m > WALK_FAR_METERS


# ---------------------------------------------------------------- 时刻

def _parse_hhmm(text: str) -> tuple[int, int]:
    try:
        parts = text.strip().split(":")
        return int(parts[0]), int(parts[1])
    except (ValueError, IndexError, AttributeError):
        raise ValueError(f"无法解析时间：{text!r}，应为 HH:MM")


def _period(hour: int) -> str:
    if hour < 5:
        return "凌晨"
    if hour < 9:
        return "早上"
    if hour < 12:
        return "上午"
    if hour == 12:
        return "中午"
    if hour < 18:
        return "下午"
    return "晚上"


def clock_to_chinese(hhmm: str) -> str:
    """'23:00' -> '晚上 11 点'；'06:30' -> '早上 6 点半'。"""
    hour, minute = _parse_hhmm(hhmm)
    hour12 = hour % 12 or 12
    period = _period(hour)

    if minute == 0:
        return f"{period} {hour12} 点"
    if minute == 30:
        return f"{period} {hour12} 点半"
    return f"{period} {hour12} 点 {minute} 分"


def _to_minutes(hhmm: str) -> int:
    hour, minute = _parse_hhmm(hhmm)
    return hour * 60 + minute


# ---------------------------------------------------------------- 营业

def is_open(start: str, end: str, now: str) -> bool:
    """判断是否营业，支持跨夜门店（如 18:00-06:00）。"""
    s, e, n = _to_minutes(start), _to_minutes(end), _to_minutes(now)
    if s == e:
        return True
    if e > s:
        return s <= n <= e
    return n >= s or n <= e          # 跨夜


def minutes_until_close(start: str, end: str, now: str) -> int | None:
    """距打烊还有几分钟；未营业返回 None。"""
    if not is_open(start, end, now):
        return None
    e, n = _to_minutes(end), _to_minutes(now)
    return (e - n) % 1440 or 1440


def is_24h(start: str, end: str) -> bool:
    return start in ("00:00", "0:00") and end in ("23:59", "23:59:59")


def open_to_chinese(start: str, end: str, now: str) -> str:
    """生成第 1 步里那句营业状态话术。"""
    if is_24h(start, end):
        return "这家店全天都开"

    if not is_open(start, end, now):
        return (
            f"这家店这会儿没开。"
            f"营业时间 {clock_to_chinese(start)} 到 {clock_to_chinese(end)}"
        )

    left = minutes_until_close(start, end, now)

    if left is None:
        return f"现在开门，到{clock_to_chinese(end)}"
    if left > NOTICE_MINUTES:
        return f"现在开门，到{clock_to_chinese(end)}"
    if left > URGENT_MINUTES:
        return f"这家店 {left} 分钟后关门，要不要现在就点？"
    return (
        f"这家店再有 {left} 分钟就关门了，可能来不及。"
        f"要不要换一家，或者送到家？"
    )


# ---------------------------------------------------------------- CLI

def _demo() -> None:
    print("== 金额 ==")
    for v in (34.5, 26, 13.9, 0.5, 49.9):
        print(f"  {v!s:>6}  ->  {money_to_chinese(v)}")

    print("\n== 距离（老年步速 50 米/分钟）==")
    for d in (30, 144, 235, 480, 720, 1200):
        minutes, phrase, far = walk_to_chinese(d)
        flag = "  [建议改外送]" if far else ""
        print(f"  {d:>5} 米  ->  {phrase}{flag}")

    print("\n== 时刻 ==")
    for t in ("06:30", "10:00", "12:00", "17:00", "23:00", "00:00"):
        print(f"  {t}  ->  {clock_to_chinese(t)}")

    print("\n== 营业状态（当前 20:46）==")
    cases = [
        ("06:30", "23:00"),
        ("00:00", "23:59"),
        ("06:00", "21:00"),
        ("06:00", "21:10"),
        ("18:00", "06:00"),
        ("08:00", "20:00"),
    ]
    for start, end in cases:
        print(f"  {start}-{end}  ->  {open_to_chinese(start, end, '20:46')}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="mcd-a11y-counter 老年友好格式化工具"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_money = sub.add_parser("money", help="金额 -> 中文元角")
    p_money.add_argument("value", type=float)

    p_walk = sub.add_parser("walk", help="距离(米) -> 走路分钟数话术")
    p_walk.add_argument("meters", type=float)

    p_clock = sub.add_parser("clock", help="HH:MM -> 中文口语时刻")
    p_clock.add_argument("time")

    p_open = sub.add_parser("open", help="营业时间 -> 营业状态话术")
    p_open.add_argument("--start", required=True)
    p_open.add_argument("--end", required=True)
    p_open.add_argument(
        "--now", default=None, help="当前时间 HH:MM，默认取本机时间"
    )

    sub.add_parser("demo", help="跑一遍全部样例")

    args = parser.parse_args()

    if args.cmd == "money":
        print(money_to_chinese(args.value))

    elif args.cmd == "walk":
        _, phrase, far = walk_to_chinese(args.meters)
        print(phrase)
        if far:
            print("[提示] 超过 800 米，建议改为送到家")

    elif args.cmd == "clock":
        print(clock_to_chinese(args.time))

    elif args.cmd == "open":
        now = args.now or datetime.now().strftime("%H:%M")
        print(open_to_chinese(args.start, args.end, now))

    elif args.cmd == "demo":
        _demo()

    return 0


if __name__ == "__main__":
    sys.exit(main())
