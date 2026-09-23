const $ = (id) => document.getElementById(id);
const status = (message, error = false) => {
    $("status").textContent = message;
    $("status").className = error ? "warning" : "ok";
};

async function api(path, data) {
    const response = await fetch(path, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ baseUrl: $("base-url").value, token: $("token").value, ...data }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error ?? `HTTP ${response.status}`);
    return payload;
}

async function perform(method, tool, args) {
    const data = await api("/api/mcp", { method, tool, arguments: args });
    $("raw").textContent = JSON.stringify(data, null, 2);
    if (data.response?.isError) throw new Error(data.response.content?.[0]?.text ?? "MCP nástroj selhal.");
    return data.response?.structuredContent ?? data.response;
}

function line(parent, text, tag = "p") {
    const element = document.createElement(tag);
    element.textContent = text;
    parent.append(element);
    return element;
}

async function run(action) {
    try {
        status("Čekám na odpověď...");
        await action();
        if ($("status").textContent === "Čekám na odpověď...") status("Hotovo");
    } catch (error) {
        status(error.message, true);
    }
}

$("health").onclick = () => run(async () => {
    const result = await api("/api/health", {});
    if (result.httpStatus !== 200) throw new Error(`Služba HTTP ${result.httpStatus}: ${JSON.stringify(result.body)}`);
    status(`Služba žije: ${result.body.status}`);
});

$("discover").onclick = () => run(async () => {
    const result = await perform("tools/list");
    status(`MCP nástroje: ${result.tools.map((tool) => tool.name).join(", ")}`);
});

$("search").onclick = () => run(async () => {
    const result = await perform("tools/call", "list_pizzas", {
        category: $("category").value || null, query: $("query").value || null,
        available_only: $("available").checked, limit: 50,
    });

    const container = $("pizzas");
    container.replaceChildren();
    line(container, `${result.count} položek (max. ${result.limit})`);
    for (const pizza of result.pizzas) {
        const row = document.createElement("div");
        row.className = "item";
        line(row, `${pizza.name} · ${pizza.price_czk} Kč · ${pizza.category}${pizza.available ? "" : " · nedostupná"}`, "strong");
        const button = document.createElement("button");
        button.textContent = "Recept";
        button.onclick = () => { $("pizza-id").value = pizza.id; $("detail").click(); };
        row.append(button);
        container.append(row);
    }
});

for (const [button, tool, key] of [
    ["ingredients", "list_ingredients", "ingredients"],
    ["allergens", "list_allergens", "allergens"],
]) {
    $(button).onclick = () => run(async () => {
        const result = await perform("tools/call", tool, {});
        const container = $("reference");
        container.replaceChildren();
        line(container, `${result.count} položek`, "h3");
        for (const item of result[key]) {
            line(container, key === "allergens"
                ? `${item.number}. ${item.name}`
                : `${item.name} (${item.id})${item.allergen_profile_complete ? "" : " · profil nejistý"}`);
        }
    });
}

$("detail").onclick = () => run(async () => {
    const result = await perform("tools/call", "get_pizza", { pizza_id: $("pizza-id").value });
    const container = $("detail-result");
    container.replaceChildren();
    line(container, `${result.name} · ${result.price_czk} Kč`, "h3");
    line(container, `Deklarované alergeny: ${result.declared_allergens.map((a) => `${a.number} ${a.name}`).join(", ")}`);
    if (result.uncertain_ingredients.length) {
        line(container, `Neúplný profil: ${result.uncertain_ingredients.map((i) => `${i.ingredient} (${i.note})`).join(", ")}`, "strong").className = "warning";
    }
    const table = document.createElement("table");
    for (const ingredient of result.ingredients) {
        const row = document.createElement("tr");
        line(row, ingredient.name, "td");
        line(row, `${ingredient.grams} g`, "td");
        table.append(row);
    }
    container.append(table);
    line(container, result.safety_note);
});

$("check").onclick = () => run(async () => {
    const result = await perform("tools/call", "check_allergen", {
        pizza_id: $("pizza-id").value, allergen_number: Number($("allergen").value),
    });
    const container = $("detail-result");
    container.replaceChildren();
    line(container, `${result.allergen_name} (${result.allergen_number}): ${result.status}`, "h3");
    line(container, result.safety_note);
    if (result.uncertain_ingredients.length) {
        line(container, result.uncertain_ingredients.map((i) => `${i.ingredient}: ${i.note}`).join("; ")).className = "warning";
    }
});

$("tool").onchange = () => {
    const defaults = {
        list_pizzas: {}, get_pizza: { pizza_id: "01-margherita" },
        check_allergen: { pizza_id: "01-margherita", allergen_number: 7 },
        list_ingredients: {}, list_allergens: {},
    };
    $("args").value = JSON.stringify(defaults[$("tool").value], null, 2);
};
$("call").onclick = () => run(async () => {
    const args = JSON.parse($("args").value);
    await perform("tools/call", $("tool").value, args);
});

const config = await fetch("/api/config").then((response) => response.json());
$("base-url").value = config.baseUrl;
if (config.connected) {
    $("token").placeholder = "Připojeno přes místní Azure Key Vault";
    status("Azure katalog připojen. Token zůstává pouze v místní proxy.");
}
