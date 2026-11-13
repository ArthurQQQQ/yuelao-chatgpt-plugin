# 进展点 03 · Checkpoint 03

**v0.2.7。** 郭延娇（郭律，GL）可点名试用。本人发布的一条 B 站连麦已下载、解码并转写，02:39–02:58 入一张沟通案例卡。现在八种聊法可点名，聊天库有 25 条原片、26 张短卡。郭律的本人合集枚举到 190 个视频 ID，另有 1,194 个第三方视频线索。新增七位有公开热度数据的创作者，名录合计 28 位。 [规模与提示词](corpus-and-prompt.md) · [创作者名录](creator-roster.md)

**验证。** 郭律三轮模拟试聊分别测试了帮用户开口、听到新事实后更新判断、应请求查出对应原片。三个步骤均通过。本地 HTTP 验证了八种点名聊法、十二道既有检索回归、三张试用卡以及无匹配返回空结果。100 项单元测试通过。主播说话人与转写待人工核听，ChatGPT 账号内接入待实测。 [HTTP 验收记录](acceptance-v0.2.7.json)

**v0.2.7.** Guo Yanjiao (GL) is available by name. One of her published Bilibili calls was downloaded, decoded, and transcribed locally. The new case card covers 02:39–02:58. The chat index now has 25 source videos and 26 cards across eight selectable approaches. The research roster has 28 creators, including seven additional high-reach candidates. [Corpus and prompt integration](corpus-and-prompt.md) · [Creator roster](creator-roster.md)

The three-turn Codex replay exercised an opening question, an update after new facts, and a source link on request. Local HTTP verified eight selectable styles, twelve prior retrieval fixtures, and three trial cards. All 100 unit tests passed. Speaker and transcription review and ChatGPT account integration are pending. [HTTP acceptance](acceptance-v0.2.7.json)
