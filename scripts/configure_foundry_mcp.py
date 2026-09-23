"""Connect the deployed pizza MCP services to the existing Foundry agent."""

import json
import shutil
import subprocess
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MCPTool, PromptAgentDefinition
from azure.identity import AzureCliCredential


ENDPOINT = "https://aihorizons-resource.services.ai.azure.com/api/projects/aihorizons"
AGENT = "nejlepsi-ai-pizza-na-pankraci"
VAULT = "kvaihorizons673af34d"
ARM_PROJECT = (
    "https://management.azure.com/subscriptions/673af34d-6b28-41dc-bc7b-f507418045e6"
    "/resourceGroups/RG-AI-Horizons/providers/Microsoft.CognitiveServices"
    "/accounts/aihorizons-resource/projects/aihorizons"
)
SERVICES = (
    ("pizza-catalog-mcp", "pizza_catalog", "pizza-mcp", "mcp-api-token"),
    ("pizza-orders-mcp", "pizza_orders", "pizza-order-mcp", "mcp-orders-api-token"),
)
HOST_SUFFIX = ".salmonwater-e074ca76.swedencentral.azurecontainerapps.io/mcp"


def secret(name: str) -> str:
    result = subprocess.run(
        [shutil.which("az") or "az", "keyvault", "secret", "show", "--vault-name", VAULT, "--name", name, "--query", "value", "-o", "tsv"],
        check=True, capture_output=True, text=True,
    )
    value = result.stdout.strip()
    if not value:
        raise ValueError(f"Empty Key Vault secret: {name}")
    return value


def arm_request(credential: AzureCliCredential, method: str, name: str, body: dict | None = None) -> dict:
    url = f"{ARM_PROJECT}/connections/{name}?api-version=2025-09-01"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = Request(
        url, data=data, method=method,
        headers={
            "Authorization": "Bearer " + credential.get_token("https://management.azure.com/.default").token,
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=60) as response:
            return json.load(response)
    except HTTPError as error:
        if error.code == 404 and method == "GET":
            return {}
        raise RuntimeError(f"Foundry connection {name}: ARM {method} returned HTTP {error.code}") from error


def main() -> None:
    credential = AzureCliCredential()
    project = AIProjectClient(ENDPOINT, credential)
    latest = max(project.agents.list_versions(AGENT), key=lambda version: int(version.version))
    current = project.agents.get_version(agent_name=AGENT, agent_version=latest.version)
    definition = current.definition.as_dict()
    if definition["kind"] != "prompt":
        raise ValueError(f"{AGENT} is not a prompt agent")

    tools = list(definition.get("tools") or [])
    for name, label, host, secret_name in SERVICES:
        url = f"https://{host}{HOST_SUFFIX}"
        existing = arm_request(credential, "GET", name)
        if existing:
            props = existing["properties"]
            if props["target"] != url or props["authType"] != "CustomKeys":
                raise ValueError(f"Existing connection {name} has a different target or authentication type")
            saved = project.connections.get(name, include_credentials=True).credentials.as_dict()
            if saved.get("authorization") != "Bearer " + secret(secret_name):
                raise ValueError(f"Existing connection {name} has an outdated Authorization credential")
        else:
            created = arm_request(credential, "PUT", name, {
                "properties": {
                    "category": "CustomKeys",
                    "authType": "CustomKeys",
                    "target": url,
                    "credentials": {"keys": {"Authorization": "Bearer " + secret(secret_name)}},
                },
            })
            if created["properties"]["target"] != url:
                raise RuntimeError(f"Connection {name} target was not saved")
            print(f"Created {name}")

        if any(tool.get("server_label") == label for tool in tools):
            if not any(
                tool.get("server_label") == label
                and tool.get("server_url") == url
                and tool.get("project_connection_id") == name
                and tool.get("require_approval") == "never"
                for tool in tools
            ):
                raise ValueError(f"Agent MCP tool {label} points to a different connection")
        else:
            tools.append(MCPTool(
                server_label=label,
                server_url=url,
                require_approval="never",
                project_connection_id=name,
            ).as_dict())

    instructions = definition["instructions"]
    if "pizza_catalog" not in instructions:
        instructions += (
            "\nPro aktuální nabídku, ceny, složení a alergeny používej nástroje pizza_catalog; "
            "pro historii objednávek fiktivních demo zákazníků používej pizza_orders. "
            "Údaje o cenách a objednávkách si nikdy nevymýšlej."
        )
    if "limit nejvýše 50" not in instructions:
        instructions += (
            "\nPři volání list_pizzas a list_customer_orders nastav limit nejvýše 50 "
            "(obvykle 20). Pokud chce zákazník i nedostupné pizzy, nastav available_only=false."
        )
    if tools != (definition.get("tools") or []) or instructions != definition["instructions"]:
        definition["tools"] = tools
        definition["instructions"] = instructions
        created = project.agents.create_version(
            agent_name=AGENT, definition=PromptAgentDefinition(**definition),
        )
        print(f"Agent {AGENT} version {created.version} has {len(tools)} tools")
    else:
        print(f"Agent {AGENT} already has both MCP tools")


if __name__ == "__main__":
    main()
