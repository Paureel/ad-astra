import { cp, mkdir, readdir, rm } from "node:fs/promises";
import { fileURLToPath } from "node:url";
const source = fileURLToPath(new URL("../web/", import.meta.url));
const target = fileURLToPath(new URL("../dist/", import.meta.url));
const root = fileURLToPath(new URL("../", import.meta.url));
await rm(target, { recursive: true, force: true });
await mkdir(target, { recursive: true });
for (const file of await readdir(source)) {
  if (file.startsWith(".") || file.endsWith(".cjs") || file.endsWith(".md")) continue;
  await cp(`${source}/${file}`, `${target}/${file}`, { recursive: true });
}
for (const file of ["LICENSE", "NOTICE", "licenses", "SOURCES.json"]) {
  await cp(`${root}/${file}`, `${target}/${file}`, { recursive: true });
}
console.log("Built dist/ · static files only.");
