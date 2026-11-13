"""Auditable artifact assembly. No stage is inferred from a plan or a web page."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def validate_scope(scope: dict) -> dict:
    if not scope.get("creator_id") or not scope.get("videos"):
        raise ValueError("creator_id and videos are required")
    sources, families = set(), {}
    for video in scope["videos"]:
        sid, family, split = (video.get(k) for k in ("source_id", "family_id", "split"))
        if not sid or sid in sources:
            raise ValueError("source_id must be present and unique")
        if not family or split not in {"dev", "holdout"}:
            raise ValueError("family_id and explicit dev/holdout split required")
        if video.get("creator_id") != scope["creator_id"]:
            raise ValueError("creator mismatch")
        if not str(video.get("url", "")).startswith("https://"):
            raise ValueError("public source URL required")
        if family in families and families[family] != split:
            raise ValueError("conversation family crosses dev/holdout")
        sources.add(sid)
        families[family] = split
    return scope


def freeze_split(videos: list[dict], path: Path) -> dict:
    frozen = {v["source_id"]: {k: v[k] for k in ("family_id", "split")} for v in videos}
    if Path(path).exists() and read_json(path) != frozen:
        raise ValueError("frozen split changed; create a new experiment instead")
    if not Path(path).exists():
        write_json(path, frozen)
    return frozen


def media_valid(record: dict) -> bool:
    if record.get("status") != "downloaded" or record.get("decode_verified") is not True:
        return False
    path = Path(record.get("media_path") or "")
    if not path.is_file() or path.stat().st_size <= 0:
        return False
    return hashlib.sha256(path.read_bytes()).hexdigest() == record.get("sha256")


def artifact_counts(records: list[dict], transcripts: list[dict], dialogues: list[dict], runs: list[dict]) -> dict:
    valid = {r["source_id"] if "source_id" in r else r["sha256"] for r in records if media_valid(r)}
    transcribed = {t["source_id"] for t in transcripts if t.get("status") == "machine_transcribed" and t.get("segments")}
    return {
        "downloaded_videos": len(valid), "transcribed_videos": len(transcribed),
        "machine_labeled_dialogues": len({d["source_id"] for d in dialogues if d.get("turns")}),
        "reviewed_dialogues": sum(d.get("review_status") in {"verified", "human_verified"} for d in dialogues),
        "replay_runs": sum(r.get("kind") == "replay" and r.get("status") == "completed" for r in runs),
        "simulated_sessions": sum(r.get("kind") == "simulation" and r.get("status") == "completed" for r in runs),
    }


def dialogue_from_labels(source: dict, transcript: dict, labels: dict) -> dict:
    segments = {s.get("id", i): s for i, s in enumerate(transcript["segments"])}
    if len(segments) != len(transcript["segments"]):
        raise ValueError("duplicate transcript segment id")
    assigned, tagged = set(), {}
    for turn in labels.get("turns", []):
        speaker = turn.get("speaker")
        if speaker not in {"host", "caller", "unknown"}:
            raise ValueError("invalid speaker")
        for sid in turn["segment_ids"]:
            if sid not in segments:
                raise ValueError("unknown segment id")
            if sid in assigned:
                raise ValueError("duplicate segment assignment")
            assigned.add(sid)
            tagged[sid] = speaker
    turns = []
    for sid, segment in segments.items():
        speaker = tagged.get(sid, "unknown")
        if turns and turns[-1]["speaker"] == speaker:
            turns[-1]["segment_ids"].append(sid)
            turns[-1]["text"] += segment["text"]
            turns[-1]["end"] = segment["end"]
        else:
            turns.append({"turn_id": f"{source['source_id']}:t{len(turns)}", "speaker": speaker,
                          "segment_ids": [sid], "start": segment["start"], "end": segment["end"], "text": segment["text"]})
    return {**{k: source[k] for k in ("source_id", "creator_id", "family_id", "split")},
            "source_sha256": source.get("sha256"), "review_status": "machine_labeled_pending_review",
            "speaker_status": "text_inference_not_acoustic_diarization", "turns": turns,
            "created_at": datetime.now(timezone.utc).isoformat()}


def load_catalog(root: Path) -> list[dict]:
    records = read_json(root / "config/acquisition_attempts.json")
    scope = validate_scope(read_json(root / "config/scope.json"))
    frozen = freeze_split(scope["videos"], root / "config/frozen_split.json")
    scoped = {source["source_id"]: source for source in scope["videos"]}
    latest = {}
    for record in records:
        source_id = record["source_id"]
        if record.get("status") == "downloaded" and source_id in scoped:
            if any(record.get(k) != scoped[source_id][k] for k in ("creator_id", "url", *frozen[source_id])):
                raise ValueError(f"Acquisition record differs from frozen scope: {source_id}")
            if media_valid(record):
                latest[source_id] = record
    catalog = []
    for source in latest.values():
        item = dict(source)
        for key, folder in (("transcript", "transcripts"), ("dialogue", "dialogues")):
            path = root / "data" / folder / (source["source_id"] + ".json")
            if path.exists():
                artifact = read_json(path)
                if (artifact.get("source_id") != source["source_id"] or artifact.get("split") != source["split"]
                        or artifact.get("source_sha256") != source["sha256"]):
                    raise ValueError(f"{key} does not match acquisition: {source['source_id']}")
                item[key] = artifact
        if "dialogue" in item and item["dialogue"].get("asr_model") != item.get("transcript", {}).get("asr_model"):
            del item["dialogue"]
        catalog.append(item)
    return catalog


def annotation_prompt(source: dict, transcript: dict) -> str:
    segments = [{"id": s.get("id", i), "start": s["start"], "end": s["end"], "text": s["text"]}
                for i, s in enumerate(transcript["segments"])]
    return ("你只做中文婚恋连麦的说话人标注。host=主持月老，caller=来访者。"
            "按上下文给每个ASR片段标注；同段混合两人或无法判断标unknown。不得重写文字，不得编造片段。"
            "这只是待核听的文本推断，不是声纹识别。每个id恰好出现一次。禁止使用任何工具。\n"
            + json.dumps({"title": source.get("title"), "segments": segments}, ensure_ascii=False))


ANNOTATION_SCHEMA = {"type": "object", "properties": {"turns": {"type": "array", "items": {
    "type": "object", "properties": {"speaker": {"type": "string", "enum": ["host", "caller", "unknown"]},
    "segment_ids": {"type": "array", "items": {"type": ["integer", "string"]}}},
    "required": ["speaker", "segment_ids"], "additionalProperties": False}}},
    "required": ["turns"], "additionalProperties": False}
