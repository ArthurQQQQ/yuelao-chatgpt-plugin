# 进展点 06 · 八种聊法匹配与 RAG 对照

2026 年 11 月 15 日（美东）。

- **四题选聊法。** 四个关系场景，每题从四句接话里选一句。八种聊法各出现两题。支持跳过、比较并列结果、直接换人、沿用旧题。用本机插件试聊，第二题选 C、第四题选 A，推荐郭律。随后明确点名切到杰哥，保留用户希望更直接的语气。 [四题与映射](../plugin/skills/yuelao-case-chat/references/style-matching.md) · [八种聊法与试聊句](style-guide.md)
- **RAG 对照。** 固定 33 道主播与问题组合，用相同检索逻辑比较关闭 RAG、v0.2.8、v0.2.9。首条原片和时码命中 0/16、8/16、15/16。新库保住 8 条原有案例、召回 7 条新增场景。天书催婚题漏检，曲曲和郭律各有一条相关负例误召回。24 条实际生成里，新库组在八条新增场景中给出 7 条正确原片。 [逐人得失、题库和复跑](rag-evaluation.md)
- **接话复测。** 鳌烨先问真实接触，天书先问双方各自的继续意愿。修复后用已知原输入复测。两条已知错候选在生成阶段被拒绝，梵公子和曲曲的观点片段正确定性。 [开场复测](../evals/opening-replay-results.json) · [引片复测](../evals/rag-response-retargeted.json)
- **验收。** 桌面 112 项测试通过。部署包的本机 HTTP 验证了八个推荐结果、四方同分及选定、跳题、点名覆盖和 23 条已有检索。v0.3.0 沿用 v0.2.9 的 29 条原片、37 张短卡。ChatGPT 账号内接入及界面仍待实测。 [HTTP 联调](quiz-acceptance-v0.3.0.json) · [本机试聊](../evals/quiz-chat-results.json)

**Checkpoint 06.** v0.3.0 adds a four-question quiz spanning eight conversation styles, style profiles, and reproducible per-host RAG comparison. The expanded snapshot retrieved the right source and time for 15 of 16 positive queries, up from 8, and returned two irrelevant candidates on near-match negatives. The generated responses cited the right source for seven of eight new scenarios. The quiz and current bundle passed local checks. [Method and results](rag-evaluation.md)
