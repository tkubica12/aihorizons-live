"""Explicit Foundry data-plane deployment for staff hosted and external agents."""

import argparse
import os
import re
import shutil
import subprocess

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    AgentEndpointProtocol, ContainerConfiguration, ExternalAgentDefinition,
    HostedAgentDefinition, ProtocolVersionRecord,
)
from azure.identity import AzureCliCredential

from configure_foundry_mcp import ENDPOINT, HOST_SUFFIX, arm_request, secret


STAFF_TOOLBOX = "pizza-staff-tools"
STAFF_AGENT = "pizza-staff-langgraph"
HELLO_AGENT = "pizza-hello-external"
STAFF_CONNECTION = "pizza-staff-orders-mcp"
STAFF_URL = f"https://pizza-staff-order-mcp{HOST_SUFFIX}"
SOURCE_TOOLBOX = "sada-nastroju-pro-ai-borce"


def client():
    return AIProjectClient(ENDPOINT, AzureCliCredential(), allow_preview=True)


def configure_toolbox() -> None:
    credential = AzureCliCredential()
    connection = arm_request(credential, "GET", STAFF_CONNECTION)
    if connection:
        props = connection["properties"]
        if (props["target"] != STAFF_URL or props["authType"] != "CustomKeys"
                or props["category"] != "RemoteTool"
                or props.get("metadata") != {"type": "custom_MCP"}):
            raise ValueError("Existing staff MCP connection does not match expected target/auth")
        project = client()
        actual = project.connections.get(STAFF_CONNECTION, include_credentials=True)
        if actual.credentials.as_dict().get("authorization") != "Bearer " + secret("mcp-staff-api-token"):
            raise ValueError("Staff MCP connection credential differs from Key Vault secret")
    else:
        arm_request(credential, "PUT", STAFF_CONNECTION, {
            "properties": {
                "category": "RemoteTool",
                "authType": "CustomKeys",
                "target": STAFF_URL,
                "credentials": {
                    "keys": {"Authorization": "Bearer " + secret("mcp-staff-api-token")}
                },
                "metadata": {"type": "custom_MCP"},
            },
        })

    project = client()
    source = project.toolboxes.get_version(
        name=SOURCE_TOOLBOX,
        version=project.toolboxes.get(SOURCE_TOOLBOX).default_version,
    ).as_dict()
    tools = []
    for tool in source["tools"]:
        if tool.get("server_label") == "pizza_staff_orders":
            continue
        if tool["type"] == "mcp":
            tool = {**tool, "require_approval": "never"}
        tools.append(tool)
    tools.append({
        "type": "mcp",
        "name": "pizza-staff-orders-mcp",
        "server_label": "pizza_staff_orders",
        "server_url": STAFF_URL,
        "require_approval": "never",
        "project_connection_id": STAFF_CONNECTION,
    })
    expected = {
        "tools": tools,
        "skills": source.get("skills") or [],
        "policies": source.get("policies") or {},
        "metadata": {},
    }
    existing = {item.name: item for item in project.toolboxes.list()}
    if STAFF_TOOLBOX in existing:
        latest = project.toolboxes.get_version(
            name=STAFF_TOOLBOX, version=existing[STAFF_TOOLBOX].default_version,
        ).as_dict()
        if any(latest.get(key) != value for key, value in expected.items()):
            raise ValueError("Existing staff toolbox differs; review before creating a new version")
        print(f"Staff toolbox already configured: {STAFF_TOOLBOX}")
        return
    version = project.toolboxes.create_version(STAFF_TOOLBOX, body=expected)
    project.toolboxes.update(STAFF_TOOLBOX, default_version=version.version)
    print(f"Created staff toolbox {STAFF_TOOLBOX} version {version.version}")


def deploy_hosted(image: str) -> None:
    if not re.fullmatch(r"[a-z0-9.-]+/[a-zA-Z0-9._/-]+@sha256:[a-f0-9]{64}", image):
        raise ValueError("Hosted image must be pinned to a registry digest")
    registry, name = image.split("/", 1)
    result = subprocess.run(
        [shutil.which("az") or "az", "acr", "manifest", "show-metadata",
         "-r", registry.removesuffix(".azurecr.io"), "-n", name,
         "--query", "digest", "-o", "tsv"],
        capture_output=True, text=True,
    )
    if result.returncode or result.stdout.strip() != image.rsplit("@", 1)[1]:
        raise ValueError("Hosted image digest does not exist in ACR")
    project = client()
    existing = {item.name: item for item in project.agents.list()}
    if STAFF_AGENT in existing:
        version = max(project.agents.list_versions(STAFF_AGENT), key=lambda item: int(item.version))
        definition = version.definition.as_dict()
        if definition.get("kind") != "hosted":
            raise ValueError("Existing staff agent is not hosted")
        container = definition.get("container_configuration") or {}
        if container.get("image") == image and str(version.status).lower().endswith("active"):
            print(f"Hosted agent already deployed: {STAFF_AGENT} v{version.version}")
            return
    agent = project.agents.create_version(
        agent_name=STAFF_AGENT,
        description="Read-only fictional staff operations in LangGraph",
        definition=HostedAgentDefinition(
            protocol_versions=[
                ProtocolVersionRecord(protocol=AgentEndpointProtocol.RESPONSES, version="2.0.0"),
            ],
            cpu="1", memory="2Gi",
            container_configuration=ContainerConfiguration(image=image),
            environment_variables={"MODEL_DEPLOYMENT_NAME": "gpt-5.4"},
        ),
    )
    print(f"Created hosted agent {agent.name} v{agent.version}")


def register_external() -> None:
    project = client()
    existing = {item.name: item for item in project.agents.list()}
    if HELLO_AGENT in existing:
        version = max(project.agents.list_versions(HELLO_AGENT), key=lambda item: int(item.version))
        latest = version.definition.as_dict()
        if latest.get("kind") != "external" or latest.get("otel_agent_id") != HELLO_AGENT:
            raise ValueError("Existing hello agent differs from external registration")
        print(f"External agent already registered: {HELLO_AGENT}")
        return
    agent = project.agents.create_version(
        agent_name=HELLO_AGENT,
        description="LangGraph hello demo running outside Foundry in Azure Container Apps",
        definition=ExternalAgentDefinition(otel_agent_id=HELLO_AGENT),
    )
    print(f"Registered external agent {agent.name} v{agent.version}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("toolbox", "hosted", "external"))
    parser.add_argument("--image", default=os.environ.get("HOSTED_AGENT_IMAGE"))
    args = parser.parse_args()
    if args.action == "toolbox":
        configure_toolbox()
    elif args.action == "hosted":
        if not args.image:
            parser.error("hosted requires --image or HOSTED_AGENT_IMAGE")
        deploy_hosted(args.image)
    else:
        register_external()
