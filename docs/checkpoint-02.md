# 进展点 02 · Checkpoint 02

**v0.2.6 · 七种聊法、24 条原片、25 张短卡。** 新增两种可点名试用的聊法。杰哥相亲（JG）从安全感问到家庭开支和财务分工。梵公子社会学（FG）围绕外形焦虑和实际的约会反馈接话，参考片段为 17 秒第三方切片，说话人和语气待核听。场景题继续从首批五种聊法中推荐。名录另外记录 13 位创作者及公开样本。 [创作者名录](creator-roster.md) · [接话设计和原片](../plugin/skills/yuelao-case-chat/references/host-approaches.md)

从部署包启动的本机服务通过七种聊法点名、12 道既有检索回归、两张新案例卡的查询及展示调用。中文别名能查到同一张卡，换成另一位试用聊法时相同查询返回空结果。两组模拟用户各试聊三轮，前两轮接话并吸收补充事实，第三轮按请求各给出一条原片。梵公子试聊明确标了第三方来源和说话人待核。正式 ChatGPT 账号里的接入和显示仍待实测。 [HTTP 验收记录](acceptance-v0.2.6.json)

**v0.2.6 · Seven styles, 24 source videos, and 25 case cards.** Jie Ge (JG) asks what financial security means for household spending and decisions. Fan Gongzi (FG) asks what happened on the date before drawing conclusions about appearance or interest. The latter trial has a 17-second third-party reference clip pending speaker and audio review. Both are selectable by name. The quiz still covers the original five styles. The roster includes 13 additional creators with public samples. [Creator roster](creator-roster.md)

The packaged local service passed direct selection for all seven styles, all 12 prior retrieval checks, and lookup and display calls for both new cards. Chinese aliases resolve to the same cards. Changing the host filter to the other trial returns no match for these queries. In two three-turn Codex replays, each style responded to new information before retrieving a clip at the caller's request. The Fan Gongzi reply identified the third-party source and the pending speaker review. ChatGPT account integration and rendering remain to be tested. [HTTP acceptance results](acceptance-v0.2.6.json)
