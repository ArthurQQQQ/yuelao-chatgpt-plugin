"""Build a reading index for a downloaded clip batch without copying the media."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from urllib.parse import quote
import argparse
import os
import re

from .pipeline import media_valid, read_json, write_json


MVP = Path(__file__).resolve().parents[2]
BATCH = MVP / "data/clip-batch-20"
OUTPUT = MVP.parent / "09-二十条直播切片"
LABELS = {"aoye": "鳌烨", "tianshu": "天书定位", "lengai": "冷爱"}


def _clock(seconds: float) -> str:
    minutes, seconds = divmod(int(seconds), 60)
    return f"{minutes:02d}:{seconds:02d}"


def _link(path: Path, folder: Path) -> str:
    return quote(os.path.relpath(path, folder), safe="/")


def _text(value) -> str:
    if isinstance(value, dict):
        return "；".join(f"{key}：{_text(item)}" for key, item in value.items())
    if isinstance(value, list):
        return "；".join(_text(item) for item in value)
    return str(value or "").strip().replace("\n", " ").replace("|", "\\|").replace("[", "（").replace("]", "）")


def _summary(record: dict) -> str:
    value = record.get("summary") or record.get("summary_zh") or record.get("topic_summary")
    if isinstance(value, dict) and isinstance(value.get("summary"), str):
        value = value["summary"]
    return _text(value)


def _platform_key(record: dict) -> str:
    match = re.search(r"/video/(BV[A-Za-z0-9]+|\d+)", str(record.get("url", "")))
    return match.group(1) if match else record["source_id"]


def _old_keys() -> tuple[set, set]:
    old = []
    for path in (MVP / "config/acquisition_attempts.json", MVP / "data/guest-review/new-downloads.json"):
        if path.exists():
            data = read_json(path)
            old.extend(data if isinstance(data, list) else data.get("records", []))
    return {_platform_key(r) for r in old if r.get("status") == "downloaded"}, {
        r.get("sha256") for r in old if r.get("status") == "downloaded"}


def collect() -> list[dict]:
    platform_keys, fingerprints = _old_keys()
    selected = []
    for path in (BATCH / group / "records.json" for group in ("aoye", "tianshu", "lengai")):
        if not path.exists():
            continue
        data = read_json(path)
        records = data if isinstance(data, list) else data["records"]
        summaries_path = path.with_name("summaries.json")
        summaries = read_json(summaries_path) if summaries_path.is_file() else {}
        for record in records:
            if record.get("status") != "downloaded":
                continue
            source_id, sha = record["source_id"], record["sha256"]
            platform_key = _platform_key(record)
            if platform_key in platform_keys or sha in fingerprints:
                raise ValueError(f"duplicate clip: {source_id}")
            media = Path(record["media_path"])
            if not media_valid(record) or media.stat().st_size != record["bytes"] or record["duration"] <= 0:
                raise ValueError(f"unverified media: {source_id}")
            if not re.fullmatch(r"https://[^\s()]+", record["url"]):
                raise ValueError(f"missing source URL: {source_id}")
            transcript_path = Path((record.get("transcript") or {}).get("transcript_path") or record.get("transcript_path") or "")
            if not transcript_path.is_file():
                raise ValueError(f"missing ASR file: {source_id}")
            transcript = read_json(transcript_path)
            if transcript.get("status") != "machine_transcribed" or not transcript.get("segments"):
                raise ValueError(f"missing completed ASR: {source_id}")
            if transcript.get("source_sha256") != sha:
                raise ValueError(f"ASR came from another clip: {source_id}")
            if transcript.get("source_id") != source_id:
                raise ValueError(f"ASR came from another clip ID: {source_id}")
            summary = _summary(record) or _summary({"summary": summaries.get(source_id)})
            if not summary:
                raise ValueError(f"missing summary: {source_id}")
            platform_keys.add(platform_key)
            fingerprints.add(sha)
            label = record.get("host") or record.get("performer") or record.get("creator_name") or LABELS.get(path.parent.name, path.parent.name)
            selected.append({**record, "transcript": transcript, "catalog_host": label, "group": path.parent.name,
                             "catalog_summary": summary})
    return selected


def render(records: list[dict], expected: int) -> None:
    OUTPUT.mkdir(exist_ok=True)
    hosts = Counter(_text(r["catalog_host"]) for r in records)
    duration = sum(r["duration"] for r in records)
    size = sum(r["bytes"] for r in records)
    groups = "、".join(f"{name} {n} 条" for name, n in hosts.items())
    lines = ["# 直播切片首批下载索引", "",
             f"本批 {len(records)} 条已下载并完整解码，共 {_clock(duration)}，{size:,} 字节。{groups}。",
             "", "逐条摘要根据下载视频的机器转写整理。人名、数值及说话人存在误听可能。发布账号与画面中的主播分别记录。",
             "", "[GitHub Skill 与切片来源查找过程](GitHub%20Skill%20与切片来源.md)", ""]
    for host in hosts:
        lines.extend([f"## {host}", "", "| 切片 | 讲了什么 | 本机文件 |", "| --- | --- | --- |"])
        for number, r in enumerate(records, 1):
            if _text(r["catalog_host"]) != host:
                continue
            publisher = _text(r.get("uploader") or "未记录发布账号")
            local = _link(Path(r["media_path"]), OUTPUT)
            lines.append(f"| {number:02d}. [{_text(r['title'])}]({r['url']}) · {_clock(r['duration'])} · {publisher} | {r['catalog_summary']} | [打开视频]({local}) |")
        lines.append("")
    lines.extend(["[可核对的下载清单](下载清单.json)", ""])
    (OUTPUT / "20条切片总表.md").write_text("\n".join(lines), encoding="utf-8")
    public_fields = ("source_id", "url", "title", "uploader", "uploader_id", "media_path", "bytes", "sha256",
                     "duration", "decode_verified", "catalog_host", "catalog_summary", "creator_evidence", "attribution",
                     "performer_attribution", "clip_type", "provenance", "discovery")
    write_json(OUTPUT / "下载清单.json", {"target": expected, "actual": len(records), "total_duration_seconds": round(duration, 2),
               "total_bytes": size, "hosts": dict(hosts), "clips": [
                   {**{key: r[key] for key in public_fields if key in r},
                    "transcript_path": (r.get("transcript") or {}).get("transcript_path") or r.get("transcript_path"),
                    "transcript_review": (r.get("transcript") or {}).get("review_status") or "machine_asr_pending_review"}
                   for r in records]})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected", type=int, default=20)
    args = parser.parse_args()
    records = collect()
    if len(records) != args.expected:
        raise SystemExit(f"Expected {args.expected} verified clips; found {len(records)}")
    render(records, args.expected)
    print(f"Verified {len(records)} videos. {OUTPUT / '20条切片总表.md'}")


if __name__ == "__main__":
    main()
