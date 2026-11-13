# 各主播案例 · RAG coverage

v0.2.9 · 2026 年 11 月 13 日（美东）。本地研究库 508 份 Script，506 份可检索，另有 2 份留出。聊天案例库 29 条原片、37 张时码卡。八种聊法都新增了可查的案例。

| 主播 | 本地 Script | 聊天原片 | 案例卡 | 新增场景 | 样本 |
| --- | ---: | ---: | ---: | --- | --- |
| 鳌烨 | 429 | 10 | 12 | 单身联谊、表达不同意见 | [原片 09:40](https://www.bilibili.com/video/BV1qdEL6REVT/?t=580) |
| 天书定位 | 8 | 5 | 8 | 父母催婚、家业流水与积蓄 | [原片 06:55](https://www.bilibili.com/video/BV1XYW86vEEz/?t=415) |
| 老林的情感研究室 | 6 | 5 | 7 | 暧昧话术、暂不结婚时的相处预期 | [原片 02:59](https://www.bilibili.com/video/BV13W421R7Zx/?t=179) |
| 童锦程 | 3 | 1 | 2 | 先核对暧昧到了什么程度 | [原片 00:00](https://www.bilibili.com/video/BV1tpLwzgEKS/?t=0) |
| 曲曲 | 3 | 2 | 2 | AA 后的后续邀约（观点分享） | [原片 04:21](https://www.bilibili.com/video/BV1WQeCzNEau/?t=261) |
| 杰哥相亲 | 3 | 2 | 2 | 约会坐地铁还是打车 | [原片 01:34](https://www.bilibili.com/video/BV12L796CEd9/?t=94) |
| 梵公子社会学 | 3 | 2 | 2 | 线上资料和线下接触的第一印象（观点分享） | [原片 02:45](https://www.bilibili.com/video/BV1EdXsBiEfd/?t=165) |
| 郭延娇 | 2 | 2 | 2 | 婆媳冲突先问发生在哪、是否同住 | [原片 00:33](https://www.bilibili.com/video/BV1qmxe6bEug/?t=33) |

本轮下载、解码和转写 7 条 B 站原片，4 条进入聊天库。郭延娇、杰哥的新增卡来自连麦，曲曲、梵公子来自本人账号的观点分享。另 3 条保留在研究归档，分别是相亲等级点评、带招募内容的学员回访和来源语境不足的剪辑。已有原片另拆出 7 张卡。所有新增卡均基于自动转写，原声与说话人待人工核听。51 份研究 Script 未确认单一主播归属。

本机按情境改写的 11 条新问题都首位命中指定原片和时间点，12 条既有用例通过。检查覆盖检索与时码，实际用户对接话效果的判断由试聊反馈收集。 [HTTP 联调](acceptance-v0.2.9.json) · [全量归档核验](archive-audit-v0.2.9.json) · [候选池与 Prompt 接法](corpus-and-prompt.md)

All eight approaches gained searchable cards. The current snapshot has 29 source videos and 37 cards. Two new sources are creator commentary, labeled separately from calls. The local service passed 11 new retrieval queries and all 12 prior checks. Human review of audio and speaker attribution remains pending.
