# 月老连麦 · YueLao Live Calls

**把一段关系讲清楚，选一种聊法，必要时看一段相似连麦。**

ChatGPT 插件原型 · 8 种可选聊法 · 3 道场景题 · 25 条原片 / 26 张案例卡

[中文](#中文) · [English](#english)

![首批五种月老聊法四象限。横轴从感受与互动到条件与投入，纵轴从先厘清到给下一步。TJ 左上，QQ 右上，LL 左下，TS 和 AY 右下。](assets/conversation-quadrants.png)

## 中文

### 它怎么来的

中文直播间里，有一种叫「月老连麦」的婚恋对话。来访者上麦讲一件拿不准的事，主播当场追问。比如来访者说「见面聊得很好，回家总是我先发消息」。有人会问下一次见面是谁定的，有人会问哪种回复让你觉得被敷衍。听到一个新细节，主播可能当场改判。直播切片把这些具体回合留了下来。 [老林的连麦](https://www.bilibili.com/video/BV1Yi421a7sj/?t=84) · [天书的连麦](https://www.bilibili.com/video/BV1XYW86vEEz/?t=284)

**同一件事，换个人接下一句，你愿不愿意继续讲？** 这是我们做月老连麦时想回答的问题。我们把这些接话动作做成可以选择、比较和切换的 AI 聊法。对话里需要例子时，插件会查案例库，给出相似片段和能跳到对应秒数的原片链接。

我觉得月老连麦值得看，是因为来访者从一团乱麻里讲出具体处境，主播追问一句，常常就能把问题说得更清楚。我们想评价的是这句有没有接住事实、听到新细节会不会改判，以及推荐的原片能不能对上当下的问题。 [进展点 01](docs/checkpoint-01.md)

### 四个象限，八种可选聊法

横轴看这一轮更关心**感受与互动**，还是**条件与投入**。纵轴看更适合**先厘清**，还是**给下一步**。上图画的是参加三题匹配的首批五种聊法。八种都可直接点名或中途切换。

| 字母 | 参考聊法 | 接下来会做什么 |
| --- | --- | --- |
| **LL** | 老林的情感研究室 | 先弄清哪个细节让你难受，以及你想怎样被回应。 |
| **TJ** | 童锦程 | 给一个能执行、也能观察结果的小动作。 |
| **TS** | 天书定位 | 看谁提出安排、谁落实，以及改期后谁主动补约。 |
| **AY** | 鳌烨 | 找到最影响择偶决定的现实条件，比如城市或工作。 |
| **QQ** | 曲曲 | 对照双方实际投入，帮你想清还愿意投入多少。 |
| **JG** | 杰哥相亲（点名试用） | 问安全感落在哪笔家庭开销、怎样存钱或由谁作决定。 |
| **FG** | 梵公子社会学（点名试用） | 从一次可观察的互动聊外形焦虑和约会反馈。 |
| **GL** | 郭延娇（点名试用） | 先核对双方各自明确说过什么，再把长期计划分歧问具体。 |

直接说「用杰哥相亲聊婚后开支」或「切到樊公子，聊聊约会之后的反应」。也可以说「用郭律的方式，帮我问清对方的长期计划」。樊公子按公开账号名「梵公子社会学」接入。另有 20 位研究候选，涵盖同城说媒、现场牵线、婚内沟通和关系问答。 [28 位创作者名录](docs/creator-roster.md)

### 场景题库与 MBTI / SBTI 启发

小测借鉴 MBTI 的偏好选择和 SBTI 的具体生活场景。三道题分别问见面后总是你先联系、外地工作和本地对象怎么取舍，以及对方总说「改天」却不定时间。每题让你选**此刻更想听的那句回应**，结果用来选这次的聊法。 [MBTI 偏好说明](https://www.myersbriggs.org/my-mbti-personality-type/the-mbti-preferences/) · [SBTI 原作者首发](https://www.bilibili.com/list/417038183?bvid=BV1LpDHByET6&oid=116371081925898)

> 见了两次面，都聊到店员开始收桌。散场后却总是你先发消息。你更想听哪一句？
>
> - **A**「更让你难受的是每次都要你先开口，还是聊了也觉得没被认真听？」
> - **B**「两次分别是谁提议见面，最后是谁把时间定下来的？」
> - **C**「下次把定时间留给对方，看看对方会不会给个具体安排。」

可以跳题。最高分并列时，比较两句接法再选。已经有事想说，也可以直接开始聊。 [完整题库与计分](plugin/skills/yuelao-case-chat/references/style-matching.md)

### 提示词、工具与案例库

提示词决定怎样接话，用户补充新事实时可以改判。工具负责场景题匹配、查询案例和展示证据卡。RAG 优先找相同主播的短卡，必要时用索引里的词项补找候选。每张卡保存来访情境、接话动作和原片时码。仓库内有 **25 条原片记录和 26 张短卡**，转写和说话人归属待人工核听。完整逐字稿、音视频和私人对话保存在本机。 [MCP 服务](server/yuelao_mvp/case_mcp.py) · [HTTP 联调记录](docs/acceptance-v0.2.7.json) · [素材规模与提示词接法](docs/corpus-and-prompt.md)

当前版本 **0.2.7** 已验证本机服务、八种聊法点名切换和新案例的证据卡调用。梵公子案例来自一段 17 秒的第三方片段，说话人和语气待核听。ChatGPT 账号内的注册和显示仍待实测。 [进展点 03](docs/checkpoint-03.md) · [本机启动与接入](#run-locally)

## English

**Tell your story, choose how you want to talk it through, and pull up a similar live call when it helps.**

### Where it came from

On Chinese-language livestreams, callers sometimes bring a real dating or relationship dilemma to a host for an on-air conversation known as *YueLao lianmai*. A caller might say, “We talk for hours in person, but I'm always the one who texts afterward.” One host asks who set the next date. Another asks what made the reply feel dismissive. A new detail can change how the host understands the situation. Short clips preserve those turns. [Lao Lin call](https://www.bilibili.com/video/BV1Yi421a7sj/?t=84) · [Tianshu call](https://www.bilibili.com/video/BV1XYW86vEEz/?t=284)

**If someone responded differently to the same story, would you want to keep talking?** That's the question behind YueLao Live Calls. The plugin turns these approaches into AI conversation styles you can choose, compare, or switch between. When an example helps, it can retrieve a similar call and link to the relevant moment.

What interests me about these live calls is how one well-placed question can make a messy situation easier to describe. We evaluate whether the reply picks up the facts, changes its judgment when new details arrive, and links to a clip that actually addresses the caller's question. [Checkpoint 01](docs/checkpoint-01.md)

### Four quadrants and eight selectable styles

The horizontal axis runs from **feelings and interaction** to **constraints and effort**. The vertical axis runs from **clarifying first** to **suggesting a next step**. The chart shows the first five styles, which are available through the quiz. You can pick or switch among all eight styles by name.

| Code | Style reference | What it tends to do next |
| --- | --- | --- |
| **LL** | Lao Lin's Relationship Lab | Ask what hurt and what response you were hoping for. |
| **TJ** | Tong Jincheng | Offer one small action with an observable outcome. |
| **TS** | Tianshu Dingwei | Look at who proposed, confirmed, or rescheduled an actual plan. |
| **AY** | Ao Ye | Identify the practical constraint that most affects the choice, such as location or work. |
| **QQ** | Ququ | Compare the effort both people have already put in and help you decide how much to keep investing. |
| **JG** | Jie Ge Matchmaking (direct-pick trial) | Ask what financial security means in practice, such as household expenses, savings, or who makes decisions. |
| **FG** | Fan Gongzi (direct-pick trial) | Ask what happened on a date before drawing conclusions about appearance or interest. |
| **GL** | Guo Yanjiao (direct-pick trial) | Clarify what each person has said about long-term plans and help ask a concrete follow-up. |

Try “Talk through household expenses with Jie Ge” or “Switch to Fan Gongzi and help me understand what happened after the date.” The roster also tracks 20 creators for research across local matchmaking, onstage introductions, and relationship Q&A. [28-creator roster](docs/creator-roster.md)

### The question bank, inspired by MBTI and SBTI

The quiz borrows preference choices from MBTI and everyday situations from SBTI. Three prompts cover always texting first after a date, weighing a job in another city against a local match, and hearing “another day” without an actual date. You pick **the response you'd most like to hear right now**. [MBTI preferences](https://www.myersbriggs.org/my-mbti-personality-type/the-mbti-preferences/) · [Original SBTI announcement](https://www.bilibili.com/list/417038183?bvid=BV1LpDHByET6&oid=116371081925898)

> You've met twice and talked until the staff started clearing tables. Afterward, you're always the one who texts first. Which response would you want?
>
> - **A** “Does it hurt more to always reach out first, or to feel unheard once you do?”
> - **B** “Who suggested each date, and who actually set the time?”
> - **C** “Let them pick the time next time, and see whether they offer a concrete plan.”

You can skip questions, choose between two suggested responses if the scores tie, or skip the quiz and tell your story. [Question bank and scoring](plugin/skills/yuelao-case-chat/references/style-matching.md)

### Prompts, tools, and retrieval

Prompts guide how the model responds and when it updates its view. The read-only MCP tools match a style, search for a case, and display a source card. Retrieval prioritizes the selected style's short cards and uses indexed terms to surface extra candidates when needed. This repository contains metadata for **25 source videos and 26 case cards**, with timecodes, short situations, and host actions. Transcription and speaker attribution still need human audio review. Full transcripts, source media, and private conversations are stored locally. [MCP service](server/yuelao_mvp/case_mcp.py) · [HTTP acceptance results](docs/acceptance-v0.2.7.json) · [Corpus and prompt integration](docs/corpus-and-prompt.md)

## Run locally

需要 Python 3.13 和支持 FTS5 的 SQLite。 / Requires Python 3.13 and SQLite with FTS5.

```sh
cd server
python -m pip install -r requirements.txt
python -m uvicorn yuelao_mvp.cloud_mcp:create_app --factory --host 127.0.0.1 --port 8080 --no-access-log
```

本机健康检查为 `http://127.0.0.1:8080/healthz`，MCP 端点为 `http://127.0.0.1:8080/mcp`。私有试用可走 OpenAI Secure MCP Tunnel。部署时可用 `server/` 里的 Dockerfile，在 HTTPS 网关配置访问控制，将实际域名设为 `YUELAO_ALLOWED_HOSTS`。在 ChatGPT 添加自定义 MCP 后，将连接绑定到 [插件目录](plugin/)。

Use `http://127.0.0.1:8080/healthz` to check the service and `http://127.0.0.1:8080/mcp` as the local MCP endpoint. For private testing, use OpenAI Secure MCP Tunnel. For hosted use, build the Dockerfile in `server/`, configure access control at the HTTPS gateway, and set `YUELAO_ALLOWED_HOSTS` to the serving hostname. Add the custom MCP server in ChatGPT and bind it to the [plugin skill](plugin/). Version **0.2.7** passed local HTTP checks for direct selection and evidence-card calls. The Fan Gongzi card points to a 17-second third-party clip pending speaker and audio review. ChatGPT account registration and in-chat rendering still need verification. [Connect to ChatGPT](https://developers.openai.com/plugins/deploy/connect-chatgpt) · [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)
