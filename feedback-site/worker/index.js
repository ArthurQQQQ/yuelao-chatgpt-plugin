import { form } from "./form.js";

const hosts = new Map(Object.entries({
  ay: "aoye", ts: "tianshu", ll: "laolin", tj: "tong", qq: "ququ",
  jg: "jiege", fg: "fan", gl: "guolu",
}));
const knownHosts = new Set([...hosts.values(), "unknown"]);
const verdicts = new Set(["like", "unreal", "mixed"]);
const reasons = new Set(["", "opening", "question", "tone", "judgment", "source", "other"]);
const maxBody = 18000;
const responseHeaders = {
  "Cache-Control": "no-store",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "no-referrer",
};

function json(value, status = 200) {
  return Response.json(value, { status, headers: responseHeaders });
}

function page(content, status = 200) {
  return new Response(content, { status, headers: {
    ...responseHeaders,
    "Content-Type": "text/html; charset=utf-8",
    "Content-Security-Policy": "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
  } });
}

async function readSubmission(request) {
  const mime = request.headers.get("content-type")?.split(";")[0].trim();
  if (mime !== "application/json" || Number(request.headers.get("content-length")) > maxBody || !request.body) {
    return null;
  }
  const reader = request.body.getReader();
  const decoder = new TextDecoder("utf-8", { fatal: true });
  let text = "";
  let size = 0;
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > maxBody) return null;
      text += decoder.decode(value, { stream: true });
    }
    const fields = JSON.parse(text + decoder.decode());
    if (!fields || typeof fields !== "object" || Array.isArray(fields)) return null;
    const { request_id: id, verdict, reason = "", share_excerpt = false } = fields;
    const hostValue = typeof fields.host === "string" ? fields.host.toLowerCase() : "";
    const host = hosts.get(hostValue) ?? hostValue;
    const { version = "unknown", turn = "", comment = "", excerpt = "" } = fields;
    if (typeof id !== "string" || !/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i.test(id) ||
        !knownHosts.has(host) || !verdicts.has(verdict) || !reasons.has(reason) ||
        typeof share_excerpt !== "boolean" || typeof version !== "string" ||
        !/^(?:unknown|v?\d+(?:\.\d+){1,3}(?:-[a-z0-9.-]+)?)$/i.test(version) || version.length > 40 ||
        typeof turn !== "string" || turn.length > 100 ||
        typeof comment !== "string" || comment.length > 1000 ||
        typeof excerpt !== "string" || excerpt.length > 1500) return null;
    return { id: id.toLowerCase(), host, version, verdict, reason,
      turn: turn.trim(), comment: comment.trim(), excerpt: share_excerpt ? excerpt.trim() : "" };
  } catch {
    return null;
  } finally {
    await reader.cancel().catch(() => {});
  }
}

async function receiveFeedback(request, env, url) {
  if (request.headers.get("origin") !== url.origin) return json({ error: "请从反馈页提交。" }, 403);
  const entry = await readSubmission(request);
  if (!entry) return json({ error: "请检查反馈内容后再试。" }, 400);
  const created = new Date().toISOString();
  const receipt = crypto.randomUUID();
  await env.DB.prepare(
    "INSERT INTO feedback (id, receipt_id, created_at, host, version, verdict, reason, turn, comment, excerpt) SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ? WHERE (SELECT COUNT(*) FROM feedback WHERE created_at >= strftime('%Y-%m-%dT%H:%M:%fZ','now','-1 minute')) < 60 ON CONFLICT (id) DO NOTHING",
  ).bind(entry.id, receipt, created, entry.host, entry.version, entry.verdict, entry.reason, entry.turn, entry.comment, entry.excerpt).run();
  const saved = await env.DB.prepare("SELECT receipt_id FROM feedback WHERE id = ?").bind(entry.id).first();
  if (!saved) return json({ error: "提交较多，请稍后重试。" }, 429);
  return json(saved, saved.receipt_id === receipt ? 201 : 200);
}

function escape(value) {
  return String(value ?? "").replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
}

async function inbox(request, env) {
  const email = request.headers.get("oai-authenticated-user-email")?.toLowerCase();
  if (!env.OWNER_EMAIL || email !== env.OWNER_EMAIL.toLowerCase()) {
    return page('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>作者收件箱</title><p>请用站点作者的 ChatGPT 账户登录。</p><a href="/signin-with-chatgpt?returnTo=%2Finbox">登录</a> <a href="/">返回反馈页</a></html>', 403);
  }
  const { results } = await env.DB.prepare(
    "SELECT created_at, host, version, verdict, reason, turn, comment, excerpt FROM feedback WHERE created_at >= strftime('%Y-%m-%dT%H:%M:%fZ','now','-90 days') ORDER BY created_at DESC LIMIT 100",
  ).all();
  const rows = results.map(row => {
    const fields = [row.created_at, row.host, row.version, row.verdict, row.reason, row.turn, row.comment, row.excerpt];
    return "<tr>" + fields.map(field => "<td>" + escape(field) + "</td>").join("") + "</tr>";
  }).join("");
  return page(`<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>月老 · 作者收件箱</title><style>body{font:16px/1.55 system-ui;margin:2rem;background:#faf6ef;color:#241914}div{overflow:auto}td,th{padding:.55rem;vertical-align:top;text-align:left;border-bottom:1px solid #d5bba9}td{white-space:pre-wrap;overflow-wrap:anywhere}table{width:100%;min-width:42rem}</style>
  <h1>作者收件箱</h1><p>最近 90 天内的 100 条反馈 · <a href="/">返回反馈页</a></p>
  <div><table><thead><tr><th>时间（UTC）</th><th>聊法</th><th>版本</th><th>评分</th><th>问题</th><th>哪一轮</th><th>建议</th><th>自愿附上的摘录</th></tr></thead>
  <tbody>${rows || '<tr><td colspan="8">还没有反馈</td></tr>'}</tbody></table></div></html>`);
}

async function prune(env) {
  await env.DB.prepare("DELETE FROM feedback WHERE created_at < strftime('%Y-%m-%dT%H:%M:%fZ','now','-90 days')").run();
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    try {
      if (request.method === "GET" && (url.pathname === "/" || url.pathname === "/feedback")) return page(form);
      if (request.method === "GET" && url.pathname === "/inbox") return await inbox(request, env);
      if (request.method === "GET" && url.pathname === "/privacy") {
        return page('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>反馈隐私</title><h1>反馈隐私</h1><p>提交后，项目作者会收到你选择的聊法、版本、评分、问题、建议，以及你主动勾选附上的摘录。我们用它来定位试聊的问题。作者收件箱显示最近 90 天的数据，服务在收到新反馈时清理超过 90 天的旧记录。</p><p>项目不读取你的 ChatGPT 聊天记录。语音输入使用浏览器的识别功能，可能由浏览器提供方在线转写。此项目只接收你主动提交的文字。</p><p>如需删除一条反馈，请把提交后的回执编号交给项目作者。</p><a href="/">返回反馈页</a></html>');
      }
      if (request.method === "POST" && url.pathname === "/api/feedback") {
        const response = await receiveFeedback(request, env, url);
        if (response.status === 201) ctx.waitUntil(prune(env).catch(() => {}));
        return response;
      }
      return json({ error: "找不到这个页面。" }, 404);
    } catch {
      return json({ error: "反馈暂时没写入，请稍后重试。" }, 503);
    }
  },
};
