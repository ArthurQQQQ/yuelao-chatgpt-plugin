"""Read-only MCP access to the local relationship-case index."""

from __future__ import annotations

import argparse
from contextlib import closing
from pathlib import Path
import sqlite3
from typing import Annotated, Literal

from .case_rag import DEFAULT_DB, REVIEW_STATUS, search_relationship_cases as lookup_cases, time_link
from .style_matching import SelectableHost, match_scenario, match_style

try:
    from mcp.server.mcpserver import MCPServer
    from mcp.types import ToolAnnotations
    from pydantic import BaseModel, Field, StringConstraints
except ImportError as error:
    raise SystemExit('安装 MCP 适配器依赖：python -m pip install "mcp>=2.3,<3"') from error


CASE_WIDGET_URI = "ui://yuelao/evidence.html"
CASE_WIDGET = Path(__file__).with_name("case_widget.html")


class RelationshipCase(BaseModel):
    source_id: str
    title: str
    host: str
    url: str
    timestamp_url: str
    start_seconds: float
    end_seconds: float
    summary: str
    situation: str | None = None
    move: str | None = None
    review_status: str
    caveat: str


class SearchResult(BaseModel):
    cases: list[RelationshipCase]


class StyleResult(BaseModel):
    host: str | None
    tone: str
    alternate: str | None
    tied: tuple[str, ...] = ()


def case_result(match: dict) -> RelationshipCase:
    return RelationshipCase(**match, caveat="这是案例摘要。引述说话人、原话或分数前，请按时间点核对原片。")


def build_server(db: Path = DEFAULT_DB) -> MCPServer:
    server = MCPServer("yuelao-cases", title="月老连麦案例库")
    widget_meta = None
    if CASE_WIDGET.is_file():
        @server.resource(CASE_WIDGET_URI, name="evidence-card", title="相似连麦证据卡",
                         mime_type="text/html;profile=mcp-app",
                         meta={"ui": {"csp": {"redirectDomains": ["https://www.bilibili.com"]}, "prefersBorder": True},
                               "openai/widgetCSP": {"redirect_domains": ["https://www.bilibili.com"]}})
        def case_widget() -> str:
            return CASE_WIDGET.read_text(encoding="utf-8")

        widget_meta = {"ui": {"resourceUri": CASE_WIDGET_URI}}

    @server.tool(
        title="按三题推荐月老聊法",
        description=("按用户选的三道场景题推荐本轮聊法。relationship、tradeoff、followup 为 A–C，跳过传空。"
                     "最高分并列时返回 tied，用户选定后用 tie_break。已点名用 selected_host。jiege（杰哥相亲）、fan（梵公子社会学）、guolu（郭延娇）支持点名试用。"
                     "只在接续旧版问法时用 topic、first_move 和 tone。"),
        annotations=ToolAnnotations(
            read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False,
        ),
    )
    def match_conversation_style(
        topic: Literal["A", "B", "C", "D", "E"] | None = None,
        first_move: Literal["A", "B", "C", "D", "E"] | None = None,
        tone: Literal["A", "B", "C"] | None = None,
        selected_host: SelectableHost | None = None,
        relationship: Literal["A", "B", "C"] | None = None,
        tradeoff: Literal["A", "B", "C"] | None = None,
        followup: Literal["A", "B", "C"] | None = None,
        tie_break: Literal["aoye", "tianshu", "laolin", "tong", "ququ"] | None = None,
    ) -> StyleResult:
        if any(choice is not None for choice in (relationship, tradeoff, followup, tie_break)):
            matched = match_scenario(relationship, tradeoff, followup, tie_break=tie_break,
                                     selected_host=selected_host)
        else:
            matched = match_style(topic, first_move, tone, selected_host=selected_host)
        return StyleResult(host=matched.host, tone=matched.tone, alternate=matched.alternate, tied=matched.tied)

    @server.tool(
        title="查找相关连麦片段",
        description=(
            "在用户要找相似案例，或已明确的婚恋判断需要案例对照时查询一次。"
            "用一句不含身份信息的情境和要核对的动作，返回场景、主播动作及同一时段的原片链接。"
            "纯倾诉、只要一句回应或明确不看视频时直接对话。"
            "用户明确选了主播时，用 host 保持来源一致。可用 aoye、tianshu、laolin、ququ、tong、jiege、fan、guolu 或中文名。"
            "没有匹配时返回空列表。案例摘要用于辅助判断，引用主播原话前请核对原片。"
        ),
        annotations=ToolAnnotations(
            read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False,
        ),
    )
    def search_relationship_cases(
        question: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)],
        host: Annotated[str, StringConstraints(strip_whitespace=True, max_length=64)] | None = None,
        limit: Annotated[int, Field(ge=1, le=3, strict=True)] = 2,
    ) -> SearchResult:
        matches = lookup_cases(db, question, host=host or None, limit=limit)
        return SearchResult(cases=[case_result(match) for match in matches])

    @server.tool(
        title="展示一条连麦原片证据卡",
        description="用户要看案例时，可展示从查找工具选定的一条。传该条的 source_id 和 start_seconds。",
        annotations=ToolAnnotations(
            read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False,
        ),
        meta=widget_meta,
    )
    def show_relationship_case(
        source_id: Annotated[str, StringConstraints(pattern=r"^bili-BV[A-Za-z0-9]{10}$")],
        start_seconds: Annotated[float, Field(ge=0, allow_inf_nan=False)],
    ) -> SearchResult:
        with closing(sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute("""
                SELECT p.source_id, c.title, c.host, c.url, p.start_seconds, p.end_seconds,
                       p.situation, p.move, p.situation || p.move AS summary
                FROM compact_cases AS p JOIN clips AS c USING (source_id)
                WHERE p.source_id = ? AND p.start_seconds = ?
            """, (source_id, start_seconds)).fetchone()
        if row is None:
            return SearchResult(cases=[])
        match = dict(row)
        match.update(timestamp_url=time_link(match["url"], match["start_seconds"]), review_status=REVIEW_STATUS)
        return SearchResult(cases=[case_result(match)])

    return server


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--http-port", type=int, help="只在本机 127.0.0.1 启动 /mcp，默认用标准输入输出。")
    args = parser.parse_args(argv)
    if not args.db.is_file():
        parser.error("案例索引文件不存在。请先建立本地案例索引。")
    if args.http_port is not None and not 1 <= args.http_port <= 65535:
        parser.error("--http-port 必须介于 1 和 65535。")

    server = build_server(args.db.resolve())
    if args.http_port is None:
        server.run()
    else:
        server.run("streamable-http", host="127.0.0.1", port=args.http_port, stateless_http=True, json_response=True)


if __name__ == "__main__":
    main()
