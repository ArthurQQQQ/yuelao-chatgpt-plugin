"""Select a conversation approach from optional, session-specific preferences."""

from dataclasses import dataclass
from typing import Literal, get_args


TOPIC_HOSTS = dict(zip("ABCDE", ("aoye", "tianshu", "laolin", "tong", "ququ")))
MOVE_HOSTS = dict(zip("ABCDE", ("laolin", "aoye", "tianshu", "tong", "ququ")))
SelectableHost = Literal["aoye", "tianshu", "laolin", "tong", "ququ", "jiege", "fan"]
SELECTABLE_HOSTS = frozenset(get_args(SelectableHost))
TONES = {"A": "gentle", "B": "direct", "C": "adaptive"}
RELATIONSHIP_HOSTS = {"A": "laolin", "B": "ququ", "C": "tong"}
TRADEOFF_HOSTS = {"A": "aoye", "B": "tianshu", "C": "laolin"}
FOLLOWUP_HOSTS = {"A": "tianshu", "B": "aoye", "C": "tong"}


@dataclass(frozen=True)
class StyleMatch:
    host: str | None
    tone: str
    alternate: str | None = None
    tied: tuple[str, ...] = ()


def _answer(options: dict[str, str], answer: str | None) -> str | None:
    if answer is None or not answer.strip():
        return None
    key = answer.strip().upper()
    if key not in options:
        raise ValueError(f"Choose one of {', '.join(options)}")
    return options[key]


def match_style(
    topic: str | None = None,
    first_move: str | None = None,
    tone: str | None = None,
    *,
    selected_host: str | None = None,
) -> StyleMatch:
    """Prefer the requested next move over the topic, unless the user names a host."""
    tone_preference = _answer(TONES, tone) or "adaptive"
    if selected_host is not None:
        if selected_host not in SELECTABLE_HOSTS:
            raise ValueError(f"Unknown host: {selected_host}")
        return StyleMatch(selected_host, tone_preference)

    topic_host = _answer(TOPIC_HOSTS, topic)
    move_host = _answer(MOVE_HOSTS, first_move)
    if move_host is None:
        return StyleMatch(topic_host, tone_preference)
    alternate = topic_host if topic_host != move_host else None
    return StyleMatch(move_host, tone_preference, alternate)


def match_scenario(
    relationship: str | None = None,
    tradeoff: str | None = None,
    followup: str | None = None,
    *,
    tie_break: str | None = None,
    selected_host: str | None = None,
) -> StyleMatch:
    """Match from the three scene choices and defer ties to the user."""
    if selected_host is not None:
        return match_style(selected_host=selected_host)

    answers = (
        (3, _answer(RELATIONSHIP_HOSTS, relationship)),
        (2, _answer(TRADEOFF_HOSTS, tradeoff)),
        (2, _answer(FOLLOWUP_HOSTS, followup)),
    )
    scores: dict[str, int] = {}
    for points, host in answers:
        if host is not None:
            scores[host] = scores.get(host, 0) + points
    if not scores:
        if tie_break is not None:
            raise ValueError("No scenario choices to resolve")
        return StyleMatch(None, "adaptive")

    ranked = sorted(scores, key=scores.__getitem__, reverse=True)
    lead = ranked[0]
    tied = tuple(host for host in ranked if scores[host] == scores[lead])
    if len(tied) > 1:
        if tie_break is None:
            return StyleMatch(None, "adaptive", tied=tied)
        if tie_break not in tied:
            raise ValueError(f"Choose one of {', '.join(tied)}")
        alternate = next(host for host in tied if host != tie_break)
        return StyleMatch(tie_break, "adaptive", alternate)

    if tie_break is not None:
        raise ValueError("The scenario choices are not tied")
    alternate = ranked[1] if len(ranked) > 1 else None
    return StyleMatch(lead, "adaptive", alternate)
