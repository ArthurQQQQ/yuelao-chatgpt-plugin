"""Score unchanged queries against no retrieval and two tagged YueLao RAG snapshots."""

from __future__ import annotations

import argparse
from collections import Counter
from contextlib import closing, contextmanager
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory


HERE = Path(__file__).resolve().parent
ARMS = ("no-rag", "v0.2.8", "v0.2.9")
NEGATIVE_KINDS = ("related-no-match", "off-topic", "excluded-source")
OFF_TOPIC_QUERY = "我想找一段讲面包发酵后如何判断面团能不能进烤箱的原片。"


def import_engine():
    for directory in (HERE.parent / "server", HERE.parents[1] / "mvp/src"):
        if (directory / "yuelao_mvp").is_dir():
            sys.path.insert(0, str(directory))
            break
    from yuelao_mvp.case_rag import HOSTS, search_relationship_cases, time_link

    return HOSTS, search_relationship_cases, time_link


@contextmanager
def snapshots(git_dir: Path, overrides: dict):
    paths = {}
    with TemporaryDirectory(prefix="yuelao-rag-compare-") as temp:
        for version, override in overrides.items():
            if override is not None:
                paths[version] = override.resolve(strict=True)
                continue
            path = Path(temp) / f"{version}.sqlite3"
            with path.open("wb") as stream:
                subprocess.run(
                    ["git", "-C", str(git_dir), "show", f"{version}:server/cases.sqlite3"],
                    stdout=stream,
                    check=True,
                )
            paths[version] = path
        yield paths


def snapshot_info(path: Path) -> tuple[dict, dict]:
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as conn:
        assert conn.execute("PRAGMA quick_check").fetchone() == ("ok",)
        cards = conn.execute(
            "SELECT c.host, p.source_id, p.start_seconds, p.end_seconds "
            "FROM compact_cases AS p JOIN clips AS c USING (source_id)"
        ).fetchall()
        sources = set(row[0] for row in conn.execute("SELECT source_id FROM clips"))
    info = {
        "sha256": sha256(path.read_bytes()).hexdigest(),
        "sources": len(sources),
        "cards": len(cards),
        "cards_by_host": dict(Counter(row[0] for row in cards)),
    }
    return info, {"sources": sources, "cards": cards}


def within_window(fixture: dict, source_id: str, time: float) -> bool:
    if source_id != fixture["target"]:
        return False
    left, right = fixture["window"]
    return left <= time < right


def validate_fixtures(fixtures, labels, inventories):
    assert len({row["id"] for row in fixtures}) == len(fixtures)
    assert {row["host"] for row in fixtures} == labels.keys()
    positive_types = {"added", "retained"}
    for fixture in fixtures:
        assert fixture["host"] in labels
        if fixture["kind"] in positive_types:
            assert fixture["target"] and len(fixture["window"]) == 2
            for arm, inventory in inventories.items():
                expected = arm == "v0.2.9" or fixture["kind"] == "retained"
                found = any(
                    host == labels[fixture["host"]] and within_window(fixture, source_id, start)
                    for host, source_id, start, _ in inventory["cards"]
                )
                assert found == expected, (arm, fixture["id"], found)
        else:
            assert fixture["kind"] in NEGATIVE_KINDS and fixture["target"] is None
            if fixture["kind"] == "excluded-source":
                assert all(
                    fixture["excluded_source"] not in inventory["sources"]
                    for inventory in inventories.values()
                )


def evaluate(fixtures, versions, labels, search, make_link):
    rows = []
    for fixture in fixtures:
        host = fixture["host"]
        for arm in ARMS:
            matches = [] if arm == "no-rag" else search(
                versions[arm], fixture["query"], host=host, limit=2,
            )
            candidates = [
                {key: match[key] for key in ("source_id", "host", "start_seconds", "end_seconds", "timestamp_url")}
                for match in matches
            ]
            assert all(
                match["host"] == labels[host] and
                match["timestamp_url"] == make_link(match["url"], match["start_seconds"])
                for match in matches
            )
            check = {"returned_empty": not matches}
            if fixture["target"] is not None:
                check.update({
                    "top1_source": bool(matches and matches[0]["source_id"] == fixture["target"]),
                    "top2_source": any(match["source_id"] == fixture["target"] for match in matches),
                    "top1_action": bool(matches and within_window(
                        fixture, matches[0]["source_id"], matches[0]["start_seconds"],
                    )),
                    "top2_action": any(within_window(
                        fixture, match["source_id"], match["start_seconds"],
                    ) for match in matches),
                })
            else:
                check["correct_empty"] = not matches
            rows.append({
                "fixture": fixture["id"], "host": host, "kind": fixture["kind"], "arm": arm,
                "checks": check, "candidates": candidates,
            })
    return rows


def summarize(rows):
    summary = {}
    for arm in ARMS:
        subset = [row for row in rows if row["arm"] == arm]
        stats = {}
        for kind, key in (("added", "top1_action"), ("retained", "top1_action"),
                          ("related-no-match", "correct_empty"),
                          ("off-topic", "correct_empty"), ("excluded-source", "correct_empty")):
            values = [row["checks"][key] for row in subset if row["kind"] == kind]
            stats[kind] = [sum(values), len(values)]
        positive = [row for row in subset if row["kind"] in {"added", "retained"}]
        for key in ("top1_source", "top2_source", "top1_action", "top2_action"):
            stats[key] = [sum(row["checks"][key] for row in positive), len(positive)]
        summary[arm] = stats
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--git-dir", type=Path, default=Path.cwd(),
                        help="Repository with v0.2.8 and v0.2.9 tags.")
    parser.add_argument("--baseline-db", type=Path, help="Use a baseline SQLite snapshot instead of the v0.2.8 tag.")
    parser.add_argument("--current-db", type=Path, help="Use a current SQLite snapshot instead of the v0.2.9 tag.")
    parser.add_argument("--fixtures", type=Path, default=HERE / "rag-heldout-fixtures.json")
    parser.add_argument("--out", type=Path, default=HERE / "rag-heldout-results.json")
    args = parser.parse_args()
    labels, search, make_link = import_engine()
    frozen_fixtures = args.fixtures.read_bytes()
    fixtures = json.loads(frozen_fixtures)
    fixtures += [
        {"id": f"{host}-off-topic", "host": host, "kind": "off-topic", "query": OFF_TOPIC_QUERY, "target": None,
         "reference": "烘焙情境与关系案例库无关，返回空结果。"}
        for host in labels
    ]
    with snapshots(args.git_dir, {"v0.2.8": args.baseline_db, "v0.2.9": args.current_db}) as versions:
        info, inventories = {}, {}
        for arm, path in versions.items():
            info[arm], inventories[arm] = snapshot_info(path)
        validate_fixtures(fixtures, labels, inventories)
        rows = evaluate(fixtures, versions, labels, search, make_link)
    result = {
        "scope": "Frozen paraphrased text queries over two release snapshots. Positive source clips or cards may be part of development; this is not held-out source generalization. Exact-source exclusion is a negative control.",
        "fixtures_sha256": sha256(frozen_fixtures).hexdigest(),
        "engine_sha256": sha256(Path(sys.modules[search.__module__].__file__).read_bytes()).hexdigest(),
        "snapshots": info,
        "fixtures": fixtures,
        "overall": summarize(rows),
        "by_host": {
            host: {"label": label, "metrics": summarize([row for row in rows if row["host"] == host])}
            for host, label in labels.items()
        },
        "runs": rows,
    }
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["overall"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
