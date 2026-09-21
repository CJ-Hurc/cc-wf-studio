#!/usr/bin/env node
/**
 * Minimal CE2E sandbox UI for cc-wf-studio — serves /command-fault-matrix
 * with cc-wf-studio.openEditor fault occupancy (visible-error-no-corrupt-state).
 *   node test/sandbox-ui/server.mjs
 *   PORT=7788 HOST=127.0.0.1 node test/sandbox-ui/server.mjs
 */
import { createServer } from "node:http";
import { readFileSync, existsSync } from "node:fs";
import { join, normalize, extname } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = fileURLToPath(new URL(".", import.meta.url));
const ROOT = normalize(join(HERE, "..", ".."));
const PORT = Number(process.env.PORT) || 7788;
const HOST = process.env.HOST || "127.0.0.1";

const MIME = {
	".html": "text/html; charset=utf-8",
	".js": "application/javascript; charset=utf-8",
	".mjs": "application/javascript; charset=utf-8",
	".css": "text/css; charset=utf-8",
	".json": "application/json",
};

const ROUTES = {
	"/": "/test/sandbox-ui/fixtures/command-fault-matrix.html",
	"/command-fault-matrix": "/test/sandbox-ui/fixtures/command-fault-matrix.html",
	"/health": null,
};

const server = createServer((req, res) => {
	const url = (req.url || "/").split("?")[0];
	if (url === "/health") {
		res.writeHead(200, { "content-type": "application/json" });
		res.end(JSON.stringify({ ok: true, product: "cc-wf-studio", port: PORT }));
		return;
	}
	const rel = ROUTES[url];
	if (!rel) {
		res.writeHead(404, { "content-type": "text/plain" });
		res.end("not found");
		return;
	}
	const abs = join(ROOT, rel.replace(/^\//, ""));
	if (!existsSync(abs)) {
		res.writeHead(404, { "content-type": "text/plain" });
		res.end("missing fixture");
		return;
	}
	const body = readFileSync(abs);
	res.writeHead(200, { "content-type": MIME[extname(abs)] || "application/octet-stream" });
	res.end(body);
});

server.listen(PORT, HOST, () => {
	console.log(`cc-wf-studio sandbox-ui http://${HOST}:${PORT}/command-fault-matrix`);
});
