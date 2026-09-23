import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { createCanvas, CanvasError, joinSession } from "@github/copilot-sdk/extension";
import { catalogUrl, loadCatalogToken } from "./azure-token.mjs";
import { probe, requestMcp } from "./proxy.mjs";

const servers = new Map();
const assets = {
    "/": ["panel.html", "text/html; charset=utf-8"],
    "/panel.js": ["panel.js", "text/javascript; charset=utf-8"],
    "/panel.css": ["panel.css", "text/css; charset=utf-8"],
};

function reply(res, status, data) {
    res.writeHead(status, {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "no-store",
    });
    res.end(JSON.stringify(data));
}

async function body(req) {
    let text = "";
    for await (const chunk of req) {
        text += chunk;
        if (text.length > 8192) throw new Error("Požadavek je příliš velký.");
    }
    return JSON.parse(text);
}

async function startServer(instanceId, baseUrl) {
    let entry;
    const server = createServer(async (req, res) => {
        try {
            if (req.method === "GET" && req.url === "/api/config") {
                reply(res, 200, { baseUrl, connected: Boolean(entry.token) });
                return;
            }
            if (req.method === "POST" && (req.url === "/api/health" || req.url === "/api/mcp")) {
                const origin = req.headers.origin;
                const self = `http://127.0.0.1:${server.address().port}`;
                if (origin && origin !== self) {
                    reply(res, 403, { error: "Nedůvěryhodný původ." });
                    return;
                }
                const input = await body(req);
                const result = req.url === "/api/health"
                    ? await probe(input.baseUrl)
                    : await requestMcp({
                        ...input,
                        token: input.token || (
                            input.baseUrl === entry.baseUrl ? entry.token : undefined
                        ),
                    });
                reply(res, 200, result);
                return;
            }
            const asset = assets[req.url];
            if (req.method !== "GET" || !asset) {
                reply(res, 404, { error: "Nenalezeno." });
                return;
            }
            res.writeHead(200, {
                "Content-Type": asset[1],
                "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'",
                "Cache-Control": "no-store",
            });
            res.end(await readFile(new URL(asset[0], import.meta.url)));
        } catch (error) {
            reply(res, 400, { error: error.message });
        }
    });
    await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
    entry = { server, url: `http://127.0.0.1:${server.address().port}/`, baseUrl, token: null };
    return entry;
}

await joinSession({
    canvases: [
        createCanvas({
            id: "pizza-catalog",
            displayName: "Pizza catalog / MCP",
            description: "Prohlédnout demo katalog pizz a ručně otestovat Azure MCP nástroje.",
            inputSchema: {
                type: "object",
                properties: { baseUrl: { type: "string" } },
                additionalProperties: false,
            },
            actions: [{
                name: "health",
                description: "Ověřit dostupnost nasazeného pizza MCP serveru.",
                inputSchema: {
                    type: "object",
                    properties: { baseUrl: { type: "string" } },
                    required: ["baseUrl"],
                    additionalProperties: false,
                },
                handler: async ({ input }) => {
                    try {
                        const result = await probe(input.baseUrl);
                        if (result.httpStatus !== 200) {
                            throw new CanvasError("unhealthy", `Služba hlásí HTTP ${result.httpStatus}.`);
                        }
                        return result;
                    } catch (error) {
                        if (error instanceof CanvasError) throw error;
                        throw new CanvasError("probe_failed", error.message);
                    }
                },
            }, {
                name: "connect_azure",
                description: "Připojit tento panel ke katalogovému MCP pomocí tokenu z Azure Key Vault, bez zobrazení tokenu.",
                handler: async ({ instanceId }) => {
                    const entry = servers.get(instanceId);
                    if (!entry || entry.baseUrl !== catalogUrl) {
                        throw new CanvasError("wrong_endpoint", "Otevřete katalogový panel na schválené Azure adrese.");
                    }
                    let token;
                    try {
                        token = await loadCatalogToken();
                        const result = await requestMcp({
                            baseUrl: entry.baseUrl, token, method: "tools/list",
                        });
                        entry.token = token;
                        return { connected: true, toolCount: result.response.tools.length };
                    } catch {
                        throw new CanvasError("azure_connect_failed",
                            "Připojení selhalo; ověřte místní Azure CLI přihlášení a přístup ke Key Vaultu.");
                    }
                },
            }],
            open: async (ctx) => {
                let entry = servers.get(ctx.instanceId);
                if (!entry) {
                    entry = await startServer(ctx.instanceId, ctx.input?.baseUrl ?? "");
                    servers.set(ctx.instanceId, entry);
                }
                return { title: "Pizza catalog / MCP", url: entry.url };
            },
            onClose: async ({ instanceId }) => {
                const entry = servers.get(instanceId);
                if (entry) {
                    servers.delete(instanceId);
                    await new Promise((resolve) => entry.server.close(resolve));
                }
            },
        }),
    ],
});
