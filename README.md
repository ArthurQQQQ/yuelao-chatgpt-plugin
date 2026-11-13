# 月老连麦 · ChatGPT 插件

月老连麦是一个中文关系对话插件。可以直接讲遇到的事，也可以答三道场景题选一种聊法。ChatGPT 按当前诉求接话。需要举例时，调用只读 MCP 服务查找相似连麦，给出带时间点的原片链接。

当前版本 **0.2.5**，支持五种参考聊法。它们是 AI 对话方式，可以直接点名、比较或中途切换。

| 聊法 | 重点 |
| --- | --- |
| 鳌烨 | 择偶定位、定居与现实条件的取舍 |
| 天书定位 | 长期匹配、实际邀约、双方是否落实承诺 |
| 老林的情感研究室 | 感受、沟通、希望怎样被回应 |
| 童锦程 | 给一步可执行、可观察的行动 |
| 曲曲 | 对照双方投入、决定是否继续投入 |

## 本机试用服务

需要 Python 3.13 和支持 FTS5 的 SQLite。仓库自带聊天用案例索引，包含 **22 条原片和 23 张短卡**。每张卡记录相似情境、接话动作和原片时间。原片内容和角色归属仍待人工核听。

```sh
cd server
python -m pip install -r requirements.txt
python -m uvicorn yuelao_mvp.cloud_mcp:create_app --factory --host 127.0.0.1 --port 8080 --no-access-log
```

启动后可访问 `http://127.0.0.1:8080/healthz`。MCP 端点是 `http://127.0.0.1:8080/mcp`，提供场景题匹配、案例检索和证据卡三个工具。[HTTP 联调记录](acceptance.json)

## 接入 ChatGPT

私有试用可以用 OpenAI Secure MCP Tunnel 连接本机。长期使用可部署 `server/` 下的 Docker 镜像，在 HTTPS 网关设置访问控制，并把实际域名设为 `YUELAO_ALLOWED_HOSTS`。在 ChatGPT Plugins 添加自定义 MCP 后，将生成的连接绑定到 `plugin/` 里的聊天 Skill。已验证本机 HTTP 服务和组件交互，ChatGPT 账号内的注册及显示待验证。 [官方接入步骤](https://developers.openai.com/plugins/deploy/connect-chatgpt) · [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)

仓库保留运行代码、Skill、短卡和最小检索索引。直播视频、完整逐字稿、私人对话与账号凭据均留在本机。
