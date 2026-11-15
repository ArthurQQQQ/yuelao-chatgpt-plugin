import asyncio
from collections import Counter
from itertools import product

import pytest

from yuelao_mvp.style_matching import QUIZ_HOSTS, SELECTABLE_HOSTS, StyleMatch, match_quiz, match_scenario, match_style


def test_every_host_can_be_recommended_by_the_three_scene_questions():
    matches = [match_scenario(*answers) for answers in product("ABC", repeat=3)]
    assert {match.host for match in matches} == {"aoye", "tianshu", "laolin", "tong", "ququ"}
    assert all(match.host != match.alternate for match in matches)


def test_scenario_preferences_can_reinforce_or_outweigh_the_first_question():
    assert match_scenario("a", " C ", "A").host == "laolin"
    assert match_scenario("B", "B", "A").host == "tianshu"


def test_skipped_question_can_leave_two_approaches_for_a_tie_break():
    match = match_scenario(tradeoff="A", followup="A")
    assert match == StyleMatch(None, "adaptive", tied=("aoye", "tianshu"))
    assert match_scenario(tradeoff="A", followup="A", tie_break="tianshu") == StyleMatch(
        "tianshu", "adaptive", alternate="aoye"
    )
    with pytest.raises(ValueError, match="Choose one of"):
        match_scenario(tradeoff="A", followup="A", tie_break="ququ")


def test_scenario_no_choices_and_explicit_host():
    assert match_scenario() == StyleMatch(None, "adaptive")
    assert match_scenario("A", "C", "A", selected_host="ququ").host == "ququ"
    assert match_style("B", "A", "A") == StyleMatch("laolin", "gentle", "tianshu")


@pytest.mark.parametrize(
    ("answers", "expected"),
    [
        (("A", None, "C", None), "laolin"),
        (("B", None, None, "D"), "tianshu"),
        (("C", None, "D", None), "tong"),
        (("D", "B", None, None), "ququ"),
        ((None, "A", None, "C"), "aoye"),
        ((None, "C", None, "A"), "guolu"),
        ((None, "D", "B", None), "jiege"),
        ((None, None, "A", "B"), "fan"),
    ],
)
def test_four_scene_preferences_can_reinforce_every_host(answers, expected):
    assert match_quiz(answers) == StyleMatch(expected, "adaptive")
    assert match_quiz(answers, selected_host="aoye", tone="A") == StyleMatch("aoye", "gentle")


def test_four_scene_quiz_gives_all_eight_styles_equal_exposure():
    assert Counter(host for question in QUIZ_HOSTS for host in question.values()) == {
        host: 2 for host in SELECTABLE_HOSTS
    }
    assert match_quiz([" a ", " a ", " c ", "b"]) == StyleMatch(
        "laolin", "adaptive", alternate="aoye"
    )


def test_four_scene_ties_are_returned_and_resolved_by_the_user():
    answers = [None, "D", "A", None]
    assert match_quiz(answers) == StyleMatch(None, "adaptive", tied=("jiege", "fan"))
    assert match_quiz(answers, tie_break="fan", tone="B") == StyleMatch("fan", "direct", "jiege")
    with pytest.raises(ValueError, match="Choose one of"):
        match_quiz(answers, tie_break="aoye")
    assert match_quiz(["A", "A", "A", "A"]).tied == ("laolin", "aoye", "fan", "guolu")


def test_four_scene_quiz_allows_skips_and_rejects_invalid_answers():
    assert match_quiz([]) == match_quiz([None, " ", None, None]) == StyleMatch(None, "adaptive")
    assert match_quiz(["B"]) == StyleMatch("tianshu", "adaptive")
    assert match_quiz([None, None, "A"], selected_host="guolu") == StyleMatch("guolu", "adaptive")
    with pytest.raises(ValueError, match="No scenario choices"):
        match_quiz([], tie_break="fan")
    with pytest.raises(ValueError, match="not tied"):
        match_quiz(["A"], tie_break="laolin")
    with pytest.raises(ValueError, match="four scene questions"):
        match_quiz([None] * 5)
    with pytest.raises(ValueError, match="Choose one of"):
        match_quiz(["E"])


def test_mcp_routes_four_scene_three_scene_and_legacy_preferences():
    pytest.importorskip("mcp.server.mcpserver")
    from yuelao_mvp.case_mcp import build_server

    async def run_calls():
        server = build_server()

        async def match(**arguments):
            result = await server.call_tool("match_conversation_style", arguments)
            assert not result.is_error
            return result.structured_content

        assert (await match(quiz_answers=[None, None, "A", "B"]))["host"] == "fan"
        assert (await match(quiz_answers=[None, "D", "A"]))["tied"] == ["jiege", "fan"]
        assert (await match(quiz_answers=[None, "D", "A"], tie_break="jiege"))["host"] == "jiege"
        assert (await match(quiz_answers=[]))["host"] is None
        assert (await match(quiz_answers=["A"], selected_host="guolu", tone="B")) == {
            "host": "guolu", "alternate": None, "tied": [], "tone": "direct"
        }
        assert (await match(relationship="A", tradeoff="C", followup="A"))["host"] == "laolin"
        assert (await match(tradeoff="A", followup="A", tie_break="tianshu"))["host"] == "tianshu"
        assert (await match(topic="B", first_move="A", tone="A")) == {
            "host": "laolin", "alternate": "tianshu", "tied": [], "tone": "gentle"
        }

    asyncio.run(run_calls())
