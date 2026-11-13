import { mkdirSync, readFileSync, writeFileSync, copyFileSync } from "node:fs";

const read = path => readFileSync(new URL(path, import.meta.url), "utf8");
const script = read("../worker/index.js");
const marker = 'import { form } from "./form.js";';
if (!script.startsWith(marker)) throw new Error("Missing form placeholder");
const output = new URL("../dist/server/", import.meta.url);
mkdirSync(output, { recursive: true });
const source = "const form = " + JSON.stringify(read("../worker/index.html")) + ";";
writeFileSync(new URL("index.js", output), source + script.slice(marker.length));
const manifestDir = new URL("../dist/.openai/", import.meta.url);
mkdirSync(manifestDir, { recursive: true });
copyFileSync(new URL("../.openai/hosting.json", import.meta.url), new URL("hosting.json", manifestDir));
