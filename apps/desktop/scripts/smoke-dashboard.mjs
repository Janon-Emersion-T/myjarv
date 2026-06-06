import { readFile } from "node:fs/promises";

const html = await readFile(new URL("../dist/index.html", import.meta.url), "utf8");
if (!html.includes("root")) {
  throw new Error("Desktop build output is missing the root mount.");
}
console.log(JSON.stringify({ status: "ok", check: "desktop-dist-root" }, null, 2));
