import { readdir, stat } from "node:fs/promises";

const assetDir = new URL("../dist/assets/", import.meta.url);
const files = await readdir(assetDir);
const cssName = files.find((file) => file.endsWith(".css"));
const jsName = files.find((file) => file.endsWith(".js"));

if (!cssName || !jsName) {
  throw new Error("Built desktop assets were not found for benchmarking.");
}

const css = await stat(new URL(cssName, assetDir));
const js = await stat(new URL(jsName, assetDir));

console.log(
  JSON.stringify(
    {
      css_bytes: css.size,
      js_bytes: js.size,
      total_bytes: css.size + js.size,
    },
    null,
    2,
  ),
);
