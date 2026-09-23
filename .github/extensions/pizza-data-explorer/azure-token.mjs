import { execFile } from "node:child_process";
import { promisify } from "node:util";

const run = promisify(execFile);

export const catalogUrl = "https://pizza-mcp.salmonwater-e074ca76.swedencentral.azurecontainerapps.io";

export async function loadCatalogToken() {
    const command = process.platform === "win32" ? "az.cmd" : "az";
    const { stdout } = await run(command, [
        "keyvault", "secret", "show",
        "--vault-name", "kvaihorizons673af34d",
        "--name", "mcp-api-token",
        "--query", "value",
        "--output", "tsv",
        "--only-show-errors",
    ], {
        shell: process.platform === "win32",
        windowsHide: true,
        timeout: 30000,
        maxBuffer: 4096,
    });
    const token = stdout.trim();
    if (!token || /\s/.test(token)) throw new Error("Azure Key Vault returned an invalid token");
    return token;
}
