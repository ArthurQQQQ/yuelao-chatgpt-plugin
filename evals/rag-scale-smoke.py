"""Measure local serving retrieval over the real snapshot plus synthetic load."""

from __future__ import annotations

import argparse
from collections import defaultdict
from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
from statistics import median, quantiles
from tempfile import TemporaryDirectory
from time import perf_counter

from yuelao_mvp.case_rag import HOSTS, search_relationship_cases, terms

NEEDLES = "独木舟 纸风车 斑马线 海鸥灯 珊瑚礁 萤火虫 螺丝刀 窗台猫".split()
SHARED_SCENE = "模拟的共同场景：第一次周末见面的时间安排还没确定。"
SHARED_MOVE = "先核对双方有空的时间，再约一个具体的周末见面时间。"


def seed_snapshot(source: Path, destination: Path, per_host: int) -> dict:
    shutil.copyfile(source, destination)
    ids = {}
    with closing(sqlite3.connect(destination)) as db, db:
        for host_index, (slug, label) in enumerate(HOSTS.items()):
            for index in range(per_host):
                source_id = f"bili-BV{(1 + host_index * per_host + index):010d}"
                url = f"https://www.bilibili.com/video/{source_id[5:]}/"
                scene = SHARED_SCENE
                move = SHARED_MOVE
                tags = "周末见面 时间安排 具体邀约"
                if index == 0:
                    scene = f"模拟的稀有问题：{NEEDLES[host_index]}代号的独立路线选择。"
                    move = "查清同一个专用代号对应的路线。"
                    tags = f"{NEEDLES[host_index]} 专用代号 路线选择 稀有问题"
                    ids[slug] = source_id
                db.execute("INSERT INTO clips VALUES (?, ?, ?, ?, ?, ?)",
                           (source_id, label, "Synthetic scale fixture", url, scene, "synthetic"))
                card_id = db.execute("INSERT INTO compact_cases VALUES (NULL, ?, 0, 20, ?, ?, ?)",
                                     (source_id, scene, move, tags)).lastrowid
                db.execute("INSERT INTO compact_terms(rowid, situation, move, tags) VALUES (?, ?, ?, ?)",
                           (card_id, *(" ".join(sorted(set(terms(field)))) for field in (scene, move, tags))))
        assert db.execute("PRAGMA quick_check").fetchone() == ("ok",)
    return ids


def measure(snapshot: Path, per_host: int) -> dict:
    timings = defaultdict(list)
    cases = []
    with TemporaryDirectory(prefix="yuelao-scale-") as work:
        db = Path(work) / "cases.sqlite3"
        ids = seed_snapshot(snapshot, db, per_host)
        for slug, needle in zip(HOSTS, NEEDLES):
            queries = (
                ("targeted", f"{needle}这个专用代号，要怎样核对路线选择？"),
                ("common", "第一次周末见面的时间安排还没确定，怎样约一个具体的周末见面时间？"),
                ("unrelated", "高原地形降水量变动时如何计算雪线海拔？"),
            )
            for mode, question in queries:
                for _ in range(5):
                    start = perf_counter()
                    rows = search_relationship_cases(db, question, host=slug, limit=2)
                    timings[mode].append((perf_counter() - start) * 1000)
                    assert all(row["host"] == HOSTS[slug] for row in rows)
                    if mode == "targeted":
                        assert rows and rows[0]["source_id"] == ids[slug] and rows[0]["start_seconds"] == 0
                    elif mode == "common":
                        assert rows
                    else:
                        assert not rows
                cases.append({"host": slug, "mode": mode, "passed": True})
        return {"scope": "Synthetic FTS workload plus deploy snapshot, local Python only; no quality or hosted SLA claims.",
                "synthetic_cards_per_host": per_host, "synthetic_cards": per_host * len(HOSTS),
                "index_bytes": db.stat().st_size, "checks": cases,
                "timing_ms": {name: {"p50": round(median(t), 2), "p95": round(quantiles(t, n=20)[18], 2),
                                     "calls": len(t)} for name, t in timings.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("server/cases.sqlite3"))
    parser.add_argument("--per-host", type=int, default=1000)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.per_host < 2:
        parser.error("--per-host must be at least 2")
    result = measure(args.db, args.per_host)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result["timing_ms"], indent=2))


if __name__ == "__main__":
    main()
