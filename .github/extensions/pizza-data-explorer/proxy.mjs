export function endpoint(raw) {
    const url = new URL(raw);
    const local = url.protocol === "http:" &&
        ["127.0.0.1", "localhost"].includes(url.hostname);
    const azure = url.protocol === "https:" &&
        url.hostname.endsWith(".azurecontainerapps.io");
    if ((!local && !azure) || url.username || url.password || url.search || url.hash ||
        !["/", "/mcp", "/mcp/"].includes(url.pathname)) {
        throw new Error("Použijte HTTPS adresu Azure Container App nebo místní http://127.0.0.1:port.");
    }
    return url.origin;
}

export async function probe(baseUrl) {
    const origin = endpoint(baseUrl);
    const response = await fetch(`${origin}/healthz`, { signal: AbortSignal.timeout(10000) });
    return { httpStatus: response.status, body: await response.json() };
}

async function post(origin, token, id, method, params) {
    const response = await fetch(`${origin}/mcp`, {
        method: "POST",
        signal: AbortSignal.timeout(15000),
        headers: {
            "Content-Type": "application/json",
            Accept: "application/json, text/event-stream",
            Authorization: `Bearer ${token}`,
            "Mcp-Protocol-Version": "2025-11-25",
        },
        body: JSON.stringify({ jsonrpc: "2.0", id, method, params }),
    });
    const text = await response.text();
    let parsed;
    try {
        parsed = JSON.parse(text);
    } catch {
        throw new Error(`MCP odpověď HTTP ${response.status} není JSON.`);
    }
    if (!response.ok) throw new Error(`MCP HTTP ${response.status}: ${parsed.error?.message ?? parsed.error ?? text}`);
    if (parsed.error) throw new Error(`MCP: ${parsed.error.message}`);
    return parsed;
}

export async function requestMcp({ baseUrl, token, method, tool, arguments: args }) {
    const origin = endpoint(baseUrl);
    if (!token || typeof token !== "string") throw new Error("Vyplňte demo přístupový token.");
    if (!["tools/list", "tools/call"].includes(method)) throw new Error("Nepovolená MCP metoda.");
    if (method === "tools/call" &&
        (!["list_pizzas", "get_pizza", "check_allergen", "list_ingredients", "list_allergens"].includes(tool) ||
            typeof args !== "object" || args === null || Array.isArray(args))) {
        throw new Error("Nepovolený nástroj nebo argumenty.");
    }
    await post(origin, token, 1, "initialize", {
        protocolVersion: "2025-11-25", capabilities: {},
        clientInfo: { name: "pizza-data-explorer", version: "0.1" },
    });
    const params = method === "tools/list" ? {} : { name: tool, arguments: args };
    const response = await post(origin, token, 2, method, params);
    return { request: { method, params }, response: response.result };
}
