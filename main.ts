// THE MONDAY GLOBE — hand-in program for the news-image-20261123 entry.
//
// The grader expects a single file, entry.png, inside the output folder.
// This program delivers it: it locates entry.png (next to this program, or
// in the working directory as a fallback), makes sure the output folder
// exists, empties whatever the folder previously held — the folder itself
// is never removed — and copies the image across byte for byte.

import { copyFileSync, existsSync, mkdirSync, readdirSync, rmSync } from "node:fs";
import { dirname, join, resolve } from "node:path";

const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";

// The folder this program lives in, derived from how it was invoked, so the
// image is found relative to the program rather than the caller's shell.
const programDir = dirname(resolve(process.argv[1] ?? "main.ts"));
const candidates = [join(programDir, "entry.png"), join(process.cwd(), "entry.png")];
const source = candidates.find((p) => existsSync(p));
if (!source) {
  console.error("main.ts: entry.png not found next to the program or in the working directory");
  process.exit(1);
}

mkdirSync(outDir, { recursive: true });
for (const name of readdirSync(outDir)) {
  rmSync(join(outDir, name), { recursive: true, force: true });
}
copyFileSync(source, join(outDir, "entry.png"));
console.log(`handed in entry.png -> ${join(outDir, "entry.png")}`);
