"""Index downloaded relationship clips and retrieve timecoded case evidence."""

from __future__ import annotations

import argparse
from contextlib import closing
import json
import math
from pathlib import Path
import re
import sqlite3
import tempfile
import unicodedata
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .clip_batch import MVP, collect
from .pipeline import media_valid, read_json


DEFAULT_DB = MVP / "data/relationship-cases.sqlite3"
DEPLOY_SNAPSHOT_VERSION = 1
COMPACT_CASES = MVP / "config/compact-cases.json"
HOSTS = {"aoye": "鳌烨", "tianshu": "天书定位", "laolin": "老林的情感研究室", "ququ": "曲曲", "tong": "童锦程"}
PUBLIC_SAMPLES = MVP / "data/public-source-samples"
SAMPLE_CARDS = MVP / "config/public-sample-cards.json"
REVIEW_STATUS = "machine_asr_pending_review"
COMMON_TERMS = set("我的 他的 她的 一个 一下 想问 问问 怎么 怎么办 什么 是不是 不是 这个 那个 有点 感觉 觉得 有些 自己 这种 没有 我想 如果 你说 我该 应该 对方 可不 可以 还是 然后 他们 这样 是我 我们 对象 后来 来不".split())


def terms(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", text).lower()
    tokens = []
    for part in re.findall(r"a[档码]|a\d+(?:\.\d+)?|[\u3400-\u9fff]+|[a-z0-9]+", normalized):
        if re.fullmatch(r"a(?:[档码]|\d+(?:\.\d+)?)", part):
            tokens.append(part.replace(".", "p"))
        elif part.isascii():
            if len(part) >= 2 and not part.isdecimal():
                tokens.append(part)
        else:
            tokens.extend(part[i:i + 2] for i in range(len(part) - 1))
    return [token for token in tokens if token not in COMMON_TERMS]


def transcript_passages(record: dict):
    current, size, first, last = [], 0, 0.0, 0.0
    for segment in record["transcript"]["segments"]:
        text = str(segment["text"]).strip()
        if not text:
            continue
        start, end = float(segment["start"]), float(segment["end"])
        if not (math.isfinite(start) and math.isfinite(end) and 0 <= start < end <= record["duration"] + 1):
            # The Script archive retains this text and its original ASR offsets.
            # Only usable media timestamps enter the playback index.
            continue
        if current and (end - first > 35 or size + len(text) > 260):
            yield first, last, " ".join(current)
            current, size = [], 0
        if not current:
            first = start
        current.append(text)
        last = end
        size += len(text)
    if current:
        yield first, last, " ".join(current)


def sample_records(cards: list[dict]) -> list[dict]:
    acquisitions = {record["source_id"]: record
                    for record in read_json(PUBLIC_SAMPLES / "download-results.json")["records"]}
    records = []
    for source_id, host in {card["source_id"]: card["host"] for card in cards}.items():
        acquired = acquisitions[source_id]
        transcript = read_json(PUBLIC_SAMPLES / "transcripts" / f"{source_id}.json")
        if (transcript["source_id"] != source_id or transcript.get("status") != "machine_transcribed"
                or not transcript.get("segments") or transcript.get("source_sha256") != acquired.get("sha256")
                or not media_valid(acquired)):
            raise ValueError(f"Unverified acquired sample: {source_id}")
        summary = " ".join(card["situation"] + card["move"] for card in cards if card["source_id"] == source_id)
        records.append({**acquired, "transcript": transcript, "catalog_host": HOSTS[host],
                        "catalog_summary": summary})
    return records


def build_index(path: Path, *, include_samples: bool = True) -> dict:
    records = collect()
    if not records:
        raise ValueError("No verified downloaded clips found")
    cards = read_json(COMPACT_CASES)
    if include_samples and PUBLIC_SAMPLES.is_dir():
        samples = read_json(SAMPLE_CARDS)
        records.extend(sample_records(samples))
        cards.extend(samples)
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = {"clips": len(records), "asr_segments": 0, "passages": 0, "compact_cards": 0, "hosts": {}}
    durations = {record["source_id"]: record["duration"] for record in records}
    with tempfile.TemporaryDirectory(prefix="case-index-", dir=path.parent) as work:
        temporary = Path(work) / path.name
        with closing(sqlite3.connect(temporary)) as connection, connection:
            connection.executescript("""
                CREATE TABLE clips (
                    source_id TEXT PRIMARY KEY, host TEXT NOT NULL, title TEXT NOT NULL,
                    url TEXT NOT NULL, summary TEXT NOT NULL, source_sha256 TEXT NOT NULL
                );
                CREATE TABLE passages (
                    id INTEGER PRIMARY KEY, source_id TEXT NOT NULL REFERENCES clips(source_id),
                    start_seconds REAL NOT NULL, end_seconds REAL NOT NULL, transcript TEXT NOT NULL
                );
                CREATE VIRTUAL TABLE case_terms USING fts5(source_id UNINDEXED, tokens);
                CREATE VIRTUAL TABLE passage_terms USING fts5(tokens);
                CREATE INDEX passages_source ON passages(source_id);
                CREATE TABLE compact_cases (
                    id INTEGER PRIMARY KEY, source_id TEXT NOT NULL REFERENCES clips(source_id),
                    start_seconds REAL NOT NULL, end_seconds REAL NOT NULL,
                    situation TEXT NOT NULL, move TEXT NOT NULL, tags TEXT NOT NULL,
                    UNIQUE(source_id, start_seconds, end_seconds)
                );
                CREATE VIRTUAL TABLE compact_terms USING fts5(situation, move, tags);
            """)
            for record in records:
                source_id, host = record["source_id"], record["catalog_host"]
                title, overview = record["title"], record["catalog_summary"]
                connection.execute("INSERT INTO clips VALUES (?, ?, ?, ?, ?, ?)",
                                   (source_id, host, title, record["url"], overview, record["sha256"]))
                connection.execute("INSERT INTO case_terms VALUES (?, ?)",
                                   (source_id, " ".join(terms(overview))))
                summary["hosts"][host] = summary["hosts"].get(host, 0) + 1
                summary["asr_segments"] += len(record["transcript"]["segments"])
                for start, end, text in transcript_passages(record):
                    row = connection.execute("INSERT INTO passages VALUES (NULL, ?, ?, ?, ?)",
                                             (source_id, start, end, text)).lastrowid
                    connection.execute("INSERT INTO passage_terms(rowid, tokens) VALUES (?, ?)",
                                       (row, " ".join(terms(text))))
                    summary["passages"] += 1
            for card in cards:
                source_id = card["source_id"]
                start, end = card["start"], card["end"]
                if source_id not in durations or not 0 <= start < end <= durations[source_id]:
                    raise ValueError(f"Compact case is outside its source video: {source_id} {start}–{end}")
                fields = (card["situation"], card["move"], card["tags"])
                if any(not value.strip() or len(value) > 100 for value in fields):
                    raise ValueError(f"Invalid short case fields: {source_id} {start}")
                row = connection.execute("INSERT INTO compact_cases VALUES (NULL, ?, ?, ?, ?, ?, ?)",
                                         (source_id, start, end, *fields)).lastrowid
                connection.execute("INSERT INTO compact_terms(rowid, situation, move, tags) VALUES (?, ?, ?, ?)",
                                   (row, *(" ".join(terms(value)) for value in fields)))
                summary["compact_cards"] += 1
        temporary.replace(path)
    return summary


def time_link(url: str, seconds: float) -> str:
    parts = urlsplit(url)
    if parts.hostname not in {"bilibili.com", "www.bilibili.com"}:
        return url
    params = [(key, value) for key, value in parse_qsl(parts.query) if key != "t"]
    params.append(("t", str(int(seconds))))
    return urlunsplit(parts._replace(query=urlencode(params)))


def search_cases(db: Path, query: str, *, host: str | None = None, limit: int = 3,
                 include_text: bool = False) -> list[dict]:
    query_terms = set(terms(query.strip()[:350]))
    if len(query_terms) < 2 or limit <= 0:
        return []
    host = HOSTS.get(host, host)
    expression = " OR ".join(f'"{token}"' for token in sorted(query_terms))
    with closing(sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        compact_snapshot = connection.execute("PRAGMA user_version").fetchone()[0] == DEPLOY_SNAPSHOT_VERSION
        options = connection.execute("""
            SELECT p.*, c.host, c.title, c.url, c.summary, bm25(passage_terms) AS rank
            FROM passage_terms JOIN passages AS p ON p.id = passage_terms.rowid
            JOIN clips AS c ON c.source_id = p.source_id
            WHERE passage_terms MATCH :query AND (:host IS NULL OR c.host = :host)
            ORDER BY rank, p.id LIMIT 120
        """, {"query": expression, "host": host}).fetchall()
        summary_ranks = {row[0]: -row[1] for row in connection.execute("""
            SELECT source_id, bm25(case_terms) FROM case_terms WHERE case_terms MATCH ?
        """, (expression,))}
    candidates = []
    for row in options:
        passage_terms = row["transcript"].split() if compact_snapshot else terms(row["transcript"])
        passage_matches = query_terms & set(passage_terms)
        overview_matches = query_terms & set(terms(row["summary"]))
        if len(passage_matches) < 2 or len(passage_matches | overview_matches) < min(4, len(query_terms)):
            continue
        score = -row["rank"] + 0.8 * summary_ranks.get(row["source_id"], 0)
        candidates.append((score, row))
    results, seen = [], set()
    for score, row in sorted(candidates, key=lambda item: (-item[0], item[1]["id"])):
        if row["source_id"] in seen:
            continue
        seen.add(row["source_id"])
        result = {key: row[key] for key in (
            "source_id", "host", "title", "url", "summary", "start_seconds", "end_seconds"
        )}
        result.update(timestamp_url=time_link(row["url"], row["start_seconds"]),
                      score=round(score, 6), review_status=REVIEW_STATUS)
        if include_text and not compact_snapshot:
            result["unreviewed_transcript"] = row["transcript"]
        results.append(result)
        if len(results) == limit:
            break
    return results


def search_compact_cases(db: Path, query: str, *, host: str | None = None,
                         limit: int = 2, transcript_support: set[str] | None = None) -> list[dict]:
    """Return scene and observed move from the same time range as the source link."""
    query_terms = set(terms(query.strip()[:350]))
    if len(query_terms) < 2 or limit <= 0:
        return []
    expression = " OR ".join(f'"{token}"' for token in sorted(query_terms))
    with closing(sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        indexed = connection.execute("SELECT 1 FROM sqlite_master WHERE name = 'compact_terms'").fetchone()
        if not indexed:
            return search_cases(db, query, host=host, limit=limit)
        options = connection.execute("""
            SELECT p.*, c.host, c.title, c.url, bm25(compact_terms, 2.0, 1.0, 1.0) AS rank
            FROM compact_terms JOIN compact_cases AS p ON p.id = compact_terms.rowid
            JOIN clips AS c ON c.source_id = p.source_id
            WHERE compact_terms MATCH :query AND (:host IS NULL OR c.host = :host)
            ORDER BY rank, p.id
        """, {"query": expression, "host": HOSTS.get(host, host)}).fetchall()
    results, seen = [], set()
    for row in options:
        evidence = " ".join(row[key] for key in ("situation", "move", "tags"))
        overlap = len(query_terms & set(terms(evidence)))
        required = min(4, len(query_terms))
        if transcript_support and row["source_id"] in transcript_support:
            # A second representation supports the source, while the card still
            # needs its own match before its action time can be recommended.
            required = min(3, len(query_terms))
        if overlap < required or row["source_id"] in seen:
            continue
        seen.add(row["source_id"])
        result = {key: row[key] for key in (
            "source_id", "host", "title", "url", "start_seconds", "end_seconds", "situation", "move"
        )}
        result.update(summary=f"{row['situation']}{row['move']}",
                      timestamp_url=time_link(row["url"], row["start_seconds"]),
                      score=round(-row["rank"], 6), review_status=REVIEW_STATUS)
        results.append(result)
        if len(results) == limit:
            break
    return results


def search_relationship_cases(db: Path, query: str, *, host: str | None = None,
                              limit: int = 2) -> list[dict]:
    """Prefer direct card matches and use transcript search for missed candidates."""
    cards = search_compact_cases(db, query, host=host, limit=limit)
    if cards:
        return cards
    support = {item["source_id"] for item in search_cases(db, query, host=host, limit=2)}
    return search_compact_cases(db, query, host=host, limit=limit, transcript_support=support) if support else []


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("build").add_argument("--base-only", action="store_true")
    search = commands.add_parser("search")
    search.add_argument("query")
    search.add_argument("--host", choices=HOSTS)
    search.add_argument("--limit", type=int, choices=(1, 2, 3), default=2)
    search.add_argument("--include-text", action="store_true")
    modes = search.add_mutually_exclusive_group()
    modes.add_argument("--compact", action="store_true")
    modes.add_argument("--hybrid", action="store_true")
    args = parser.parse_args()
    if args.command == "build":
        result = build_index(args.db, include_samples=not args.base_only)
    elif args.compact or args.hybrid:
        if args.include_text:
            parser.error("--include-text can only be used for transcript search")
        searcher = search_relationship_cases if args.hybrid else search_compact_cases
        result = searcher(args.db, args.query, host=args.host, limit=args.limit)
    else:
        result = search_cases(args.db, args.query, host=args.host, limit=args.limit, include_text=args.include_text)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
