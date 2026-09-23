"""Snapshot and explicitly restore project-level Foundry assets."""

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit
from urllib.request import urlopen
from xml.etree import ElementTree

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.core.rest import HttpRequest
from azure.identity import AzureCliCredential


ROOT = Path(__file__).resolve().parents[1] / "foundry"
MAX_DATASET_BYTES = 5_000_000
NAME = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")
API_VERSION = re.compile(r"^\d{4}-\d{2}-\d{2}(?:-preview)?$")
CONNECTION_METADATA = frozenset({"type", "knowledgeBaseName", "displayName", "ResourceId", "ApiType", "ApiVersion", "DeploymentApiVersion", "toolEntityId"})


def component(value: str) -> str:
    if not NAME.fullmatch(value):
        raise ValueError(f"Unsafe Foundry asset name or version: {value!r}")
    return value


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def encoded(value: dict) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def snapshot_file(path: Path, content: bytes, overwrite: bool) -> None:
    if path.exists():
        if path.read_bytes() == content:
            return
        if not overwrite:
            raise FileExistsError(f"{path} differs from Foundry; use --overwrite after reviewing your local edits")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def materialize(spec: dict, key: str, directory: Path) -> dict:
    result = dict(spec)
    filename = result.pop(key, None)
    if filename:
        result[{"instructions_file": "instructions", "prompt_file": "prompt_text"}[key]] = (
            directory / component(filename)
        ).read_text(encoding="utf-8")
    return result


def dataset_bytes(project: AIProjectClient, endpoint: str, name: str, version: str) -> bytes:
    url = f"{endpoint}/datasets/{quote(name)}/versions/{quote(version)}/credentials?api-version=v1"
    response = project.send_request(HttpRequest("POST", url))
    response.raise_for_status()
    sas = response.json()["blobReferenceForConsumption"]["credential"]["sasUri"]
    parts = urlsplit(sas)
    query = dict(parse_qsl(parts.query))
    if query.get("sr") != "c" or "r" not in query.get("sp", "") or "l" not in query.get("sp", ""):
        raise ValueError("Expected a read/list container credential for the Foundry dataset")
    listing = urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode({**query, "restype": "container", "comp": "list"}), "")
    )
    with urlopen(listing, timeout=30) as result:
        tree = ElementTree.fromstring(result.read())
    blobs = tree.findall("./Blobs/Blob")
    if len(blobs) != 1 or tree.findtext("./NextMarker") or not blobs[0].findtext("Name", "").endswith(".jsonl"):
        raise ValueError(f"Dataset {name}:{version} is not a single JSONL blob")
    blob = blobs[0]
    if int(blob.findtext("Properties/Content-Length", "0")) > MAX_DATASET_BYTES:
        raise ValueError(f"Dataset {name}:{version} exceeds the {MAX_DATASET_BYTES}-byte export limit")
    blob_url = urlunsplit(
        (parts.scheme, parts.netloc, parts.path + "/" + quote(blob.findtext("Name")), parts.query, "")
    )
    with urlopen(blob_url, timeout=60) as result:
        data = result.read(MAX_DATASET_BYTES + 1)
    if len(data) > MAX_DATASET_BYTES:
        raise ValueError(f"Dataset {name}:{version} exceeds the export limit")
    for line in data.decode("utf-8-sig").splitlines():
        if line.strip() and not isinstance(json.loads(line), dict):
            raise ValueError("Expected one JSON object per JSONL line")
    return data


def serializable(model) -> dict:
    return model.model_dump(mode="json", by_alias=True, exclude_none=True, warnings=False)


def evaluation_definition(evaluation: object) -> tuple[dict, list[dict]]:
    source = serializable(evaluation.data_source_config)
    if source.get("schema", {}).get("item") and not source.get("item_schema"):
        source["item_schema"] = source["schema"]["item"]
    source.pop("schema", None)
    criteria = [serializable(item) for item in evaluation.testing_criteria]
    for criterion in criteria:
        criterion.pop("id", None)
    return source, criteria


def connection_inventory(connection: object) -> dict:
    data = connection.as_dict()
    target = data.get("target", "")
    if target.startswith("https://"):
        parts = urlsplit(target)
        if (parts.username or parts.password or parts.fragment or
                any(key != "api-version" or not API_VERSION.fullmatch(value)
                    for key, value in parse_qsl(parts.query, keep_blank_values=True))):
            raise ValueError(f"Connection {connection.name} has a target containing possible credentials")
    elif not target.startswith("/subscriptions/"):
        raise ValueError(f"Unexpected connection target for {connection.name}")
    return {
        "name": component(connection.name),
        "type": data["type"],
        "target": target,
        "is_default": data.get("isDefault", False),
        "credential_type": (data.get("credentials") or {}).get("type"),
        "metadata": {key: value for key, value in (data.get("metadata") or {}).items()
                     if key in CONNECTION_METADATA},
    }


def validate() -> dict:
    manifest = load(ROOT / "manifest.json")
    if not manifest["endpoint"].startswith("https://"):
        raise ValueError("Foundry project endpoint must use HTTPS")
    for item in manifest["agents"]:
        directory = ROOT / "agents" / component(item["name"]) / component(item["version"])
        definition = materialize(load(directory / "definition.json"), "instructions_file", directory)
        if definition.get("kind") != "prompt" or not definition.get("model"):
            raise ValueError(f"Invalid prompt agent: {item['name']}")
    for item in manifest["evaluators"]:
        directory = ROOT / "evaluators" / component(item["name"]) / component(item["version"])
        definition = materialize(load(directory / "evaluator.json")["definition"], "prompt_file", directory)
        if definition.get("type") != "prompt" or not definition.get("prompt_text"):
            raise ValueError(f"Invalid prompt evaluator: {item['name']}")
    for item in manifest["datasets"]:
        directory = ROOT / "datasets" / component(item["name"]) / component(item["version"])
        spec = load(directory / "dataset.json")
        content = (directory / "data.jsonl").read_bytes()
        if hashlib.sha256(content).hexdigest() != spec["sha256"]:
            raise ValueError(f"Dataset checksum differs: {item['name']}:{item['version']}")
        rows = [json.loads(line) for line in content.decode("utf-8-sig").splitlines() if line.strip()]
        if not rows or not all(isinstance(row, dict) for row in rows):
            raise ValueError(f"Expected nonempty JSONL objects: {item['name']}:{item['version']}")
    for item in manifest["evaluations"]:
        spec = load(ROOT / "evaluations" / component(item["name"]) / "evaluation.json")
        if not spec["testing_criteria"] or not spec["run_data_source"]:
            raise ValueError(f"Incomplete evaluation recipe: {item['name']}")
    for item in manifest.get("toolboxes", []):
        name = component(item["name"])
        version = component(item["version"])
        directory = ROOT / "toolboxes" / name
        versions = list(directory.iterdir())
        if not versions or version not in {path.name for path in versions}:
            raise ValueError(f"Missing toolbox default version: {name}:{version}")
        for path in versions:
            if not path.is_dir():
                raise ValueError(f"Unexpected toolbox asset: {path}")
            spec = load(path / "toolbox.json")
            if spec["name"] != name or spec["version"] != component(path.name) or not spec["tools"]:
                raise ValueError(f"Invalid toolbox: {name}:{path.name}")
    for item in manifest.get("memory_stores", []):
        name = component(item["name"])
        spec = load(ROOT / "memory_stores" / name / "memory_store.json")
        if spec["name"] != name or not spec["definition"]:
            raise ValueError(f"Invalid memory store: {name}")
    connections = load(ROOT / "connections.json") if "connections" in manifest else []
    if sorted(component(item["name"]) for item in connections) != sorted(
        component(name) for name in manifest.get("connections", [])
    ):
        raise ValueError("Connection inventory does not match manifest")
    if any(set(item) != {"name", "type", "target", "is_default", "credential_type", "metadata"}
           or set(item["metadata"]) - CONNECTION_METADATA for item in connections):
        raise ValueError("Unexpected fields in connection inventory")
    return manifest


def snapshot(project: AIProjectClient, endpoint: str, overwrite: bool) -> None:
    files: dict[Path, bytes] = {}
    manifest = {"endpoint": endpoint, "agents": [], "datasets": [], "evaluators": [],
                "evaluations": [], "toolboxes": [], "memory_stores": [], "connections": []}
    evaluator_versions = {}
    agent_versions = {}
    unsupported = {
        "indexes": project.indexes,
        "evaluation rules": project.evaluation_rules,
        "skills": project.beta.skills,
        "routines": project.beta.routines,
        "schedules": project.beta.schedules,
        "evaluation taxonomies": project.beta.evaluation_taxonomies,
        "insight monitors": project.beta.agent_insight_monitors,
        "red teams": project.beta.red_teams,
    }
    for label, operations in unsupported.items():
        if any(operations.list()):
            raise ValueError(f"Foundry has {label} not supported by this snapshot; refusing a partial export")

    for agent in project.agents.list():
        name = component(agent.name)
        versions = list(project.agents.list_versions(name))
        if not versions:
            raise ValueError(f"Agent {name} has no saved versions")
        if name in {"pizza-staff-langgraph", "pizza-hello-external"}:
            expected_kind = "hosted" if name == "pizza-staff-langgraph" else "external"
            if any(version.definition.as_dict().get("kind") != expected_kind for version in versions):
                raise ValueError(f"Unexpected coded agent kind: {name}")
            continue
        latest = max(versions, key=lambda v: int(v.version))
        agent_versions[name] = latest.version
        directory = Path("agents") / name
        manifest["agents"].append({"name": name, "version": latest.version})
        for version in versions:
            definition = version.definition.as_dict()
            if definition.get("kind") != "prompt":
                raise ValueError(f"Cannot snapshot non-prompt agent {name}:{version.version}")
            version_dir = directory / component(version.version)
            instructions = definition.pop("instructions", "")
            definition["instructions_file"] = "instructions.txt"
            files[version_dir / "definition.json"] = encoded(definition)
            files[version_dir / "instructions.txt"] = instructions.encode("utf-8")

    for dataset in project.datasets.list():
        name, version = component(dataset.name), component(dataset.version)
        content = dataset_bytes(project, endpoint, name, version)
        directory = Path("datasets") / name / version
        files[directory / "data.jsonl"] = content
        files[directory / "dataset.json"] = encoded({
            "name": name,
            "version": version,
            "sha256": hashlib.sha256(content).hexdigest(),
        })
        manifest["datasets"].append({"name": name, "version": version})

    for evaluator in project.beta.evaluators.list(type="custom"):
        name = component(evaluator.name)
        versions = list(project.beta.evaluators.list_versions(name, type="custom"))
        latest = max(versions, key=lambda v: int(v.version))
        evaluator_versions[name] = latest.version
        manifest["evaluators"].append({"name": name, "version": latest.version})
        for version in versions:
            definition = version.definition.as_dict()
            if definition.get("type") != "prompt":
                raise ValueError(f"Cannot snapshot non-prompt evaluator {name}:{version.version}")
            version_dir = Path("evaluators") / name / component(version.version)
            prompt = definition.pop("prompt_text")
            definition["prompt_file"] = "prompt.txt"
            files[version_dir / "prompt.txt"] = prompt.encode("utf-8")
            files[version_dir / "evaluator.json"] = encoded({
                "name": name,
                "display_name": version.display_name,
                "description": version.description or "",
                "categories": list(version.categories or []),
                "supported_evaluation_levels": list(version.supported_evaluation_levels or []),
                "definition": definition,
            })

    openai = project.get_openai_client()
    for evaluation in openai.evals.list():
        name = component(evaluation.name)
        full = openai.evals.retrieve(evaluation.id)
        source, criteria = evaluation_definition(full)
        for criterion in criteria:
            evaluator_name = criterion.get("evaluator_name")
            if evaluator_name in evaluator_versions:
                criterion["evaluator_version"] = evaluator_versions[evaluator_name]
        directory = Path("evaluations") / name
        runs = list(openai.evals.runs.list(eval_id=evaluation.id))
        if not runs:
            raise ValueError(f"Evaluation {name} has no run to recover its target and dataset")
        latest_run = max(runs, key=lambda run: run.created_at)
        run_source = serializable(latest_run.data_source)
        target = run_source.get("target", {})
        if target.get("name") in agent_versions:
            target["version"] = agent_versions[target["name"]]
        files[directory / "evaluation.json"] = encoded({
            "name": name,
            "source_id": evaluation.id,
            "data_source_config": source,
            "testing_criteria": criteria,
            "run_data_source": run_source,
        })
        files[directory / "runs.json"] = encoded({
            "source_id": evaluation.id,
            "runs": [{
                "id": run.id,
                "status": run.status,
                "created_at": run.created_at,
                "result_counts": serializable(run.result_counts) if run.result_counts else None,
                "data_source": serializable(run.data_source),
                "report_url": run.report_url,
            } for run in runs],
        })
        manifest["evaluations"].append({"name": name})

    for toolbox in project.toolboxes.list():
        name = component(toolbox.name)
        manifest["toolboxes"].append({"name": name, "version": component(toolbox.default_version)})
        versions = list(project.toolboxes.list_versions(name))
        if not versions or toolbox.default_version not in {version.version for version in versions}:
            raise ValueError(f"Toolbox {name} has no saved default version")
        for version in versions:
            version_dir = Path("toolboxes") / name / component(version.version)
            definition = version.as_dict()
            files[version_dir / "toolbox.json"] = encoded({
                "name": name,
                "version": version.version,
                "tools": definition["tools"],
                "skills": definition.get("skills") or [],
                "policies": definition.get("policies") or {},
                "metadata": definition.get("metadata") or {},
            })

    for memory in project.beta.memory_stores.list():
        name = component(memory.name)
        detail = project.beta.memory_stores.get(name).as_dict()
        files[Path("memory_stores") / name / "memory_store.json"] = encoded({
            "name": name,
            "description": detail.get("description") or "",
            "metadata": detail.get("metadata") or {},
            "definition": detail["definition"],
        })
        manifest["memory_stores"].append({"name": name})

    connections = sorted((connection_inventory(c) for c in project.connections.list()),
                         key=lambda c: c["name"])
    manifest["connections"] = [c["name"] for c in connections]
    files[Path("connections.json")] = encoded(connections)

    files[Path("manifest.json")] = encoded(manifest)
    conflicts = [ROOT / path for path, data in files.items()
                 if (ROOT / path).exists() and (ROOT / path).read_bytes() != data]
    if conflicts and not overwrite:
        raise FileExistsError(f"Snapshot would overwrite {len(conflicts)} edited files; first: {conflicts[0]}")
    for path, data in files.items():
        snapshot_file(ROOT / path, data, overwrite)
    print(f"Saved {len(files)} files in {ROOT}; review generated data before committing to Git.")


def apply(project: AIProjectClient, endpoint: str, *, dry_run: bool = False) -> None:
    manifest = validate()
    if endpoint != manifest["endpoint"]:
        raise ValueError("This snapshot is bound to its source project; refusing a different endpoint")

    remote_datasets = {(data.name, data.version) for data in project.datasets.list()}
    remote_evaluators = {ev.name for ev in project.beta.evaluators.list(type="custom")}
    remote_agents = {agent.name for agent in project.agents.list()}
    remote_toolboxes = {toolbox.name: toolbox for toolbox in project.toolboxes.list()}
    remote_memory = {memory.name for memory in project.beta.memory_stores.list()}
    new_datasets = []
    new_evaluators = []
    new_agents = []
    new_toolboxes = []
    new_memory = []
    expected_connections = load(ROOT / "connections.json") if "connections" in manifest else []
    actual_connections = sorted((connection_inventory(c) for c in project.connections.list()),
                                key=lambda c: c["name"])
    if actual_connections != expected_connections:
        raise ValueError("Project connections differ from the saved inventory; reconcile separately")

    for item in manifest.get("memory_stores", []):
        name = item["name"]
        spec = load(ROOT / "memory_stores" / component(name) / "memory_store.json")
        if name in remote_memory:
            actual = project.beta.memory_stores.get(name).as_dict()
            if any(actual.get(key) != spec[key] for key in ("name", "description", "metadata", "definition")):
                raise ValueError(f"Remote memory store differs: {name}")
            print(f"Memory store unchanged: {name}")
        else:
            new_memory.append(spec)

    for item in manifest.get("toolboxes", []):
        name, version = item["name"], item["version"]
        directory = ROOT / "toolboxes" / component(name)
        if name in remote_toolboxes:
            remote = remote_toolboxes[name]
            if remote.default_version != version:
                raise ValueError(f"Remote toolbox default version differs: {name}")
            for local in directory.iterdir():
                if not local.is_dir():
                    continue
                spec = load(local / "toolbox.json")
                actual = project.toolboxes.get_version(name, local.name).as_dict()
                if any(actual.get(key) != spec[key] for key in ("tools", "skills", "policies", "metadata")):
                    raise ValueError(f"Remote toolbox differs: {name}:{local.name}")
            print(f"Toolbox unchanged: {name}:{version}")
        else:
            versions = sorted((load(path / "toolbox.json") for path in directory.iterdir() if path.is_dir()),
                              key=lambda item: int(item["version"]))
            new_toolboxes.append((name, version, versions))
    for item in manifest["datasets"]:
        name, version = item["name"], item["version"]
        directory = ROOT / "datasets" / component(name) / component(version)
        spec = load(directory / "dataset.json")
        path = directory / "data.jsonl"
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != spec["sha256"]:
            raise ValueError(f"Local dataset changed without updating snapshot metadata: {name}:{version}")
        if (name, version) in remote_datasets:
            if dataset_bytes(project, endpoint, name, version) != content:
                raise ValueError(f"Remote dataset differs: {name}:{version}")
            print(f"Dataset unchanged: {name}:{version}")
        else:
            new_datasets.append((name, version, path))

    for item in manifest["evaluators"]:
        name, version = item["name"], item["version"]
        directory = ROOT / "evaluators" / component(name) / component(version)
        spec = load(directory / "evaluator.json")
        spec["definition"] = materialize(spec["definition"], "prompt_file", directory)
        existing = list(project.beta.evaluators.list_versions(name, type="custom")) if name in remote_evaluators else []
        if existing:
            latest = max(existing, key=lambda ev: int(ev.version))
            actual = latest.as_dict()
            for key in ("name", "display_name", "description", "categories", "supported_evaluation_levels", "definition"):
                if actual.get(key) != spec[key]:
                    raise ValueError(f"Remote evaluator differs: {name}:{latest.version}")
            print(f"Evaluator unchanged: {name}:{latest.version}")
        else:
            new_evaluators.append((name, spec))

    for item in manifest["agents"]:
        name, version = item["name"], item["version"]
        directory = ROOT / "agents" / component(name) / component(version)
        definition = materialize(load(directory / "definition.json"), "instructions_file", directory)
        existing = list(project.agents.list_versions(name)) if name in remote_agents else []
        if existing:
            latest = max(existing, key=lambda agent: int(agent.version))
            if latest.definition.as_dict() != definition:
                raise ValueError(f"Remote agent differs: {name}:{latest.version}")
            print(f"Agent unchanged: {name}:{latest.version}")
        else:
            new_agents.append((name, definition))

    client = project.get_openai_client()
    remote_evaluations = list(client.evals.list())
    for item in manifest["evaluations"]:
        name = item["name"]
        spec = load(ROOT / "evaluations" / component(name) / "evaluation.json")
        existing = [ev for ev in remote_evaluations if ev.name == name]
        if existing:
            if len(existing) != 1 or existing[0].id != spec["source_id"]:
                raise ValueError(f"Evaluation name collision: {name}")
            print(f"Original evaluation retained: {name} ({existing[0].id})")
        repo_name = f"{name}-repo"
        matching = [ev for ev in remote_evaluations if ev.name == repo_name]
        if len(matching) > 1:
            raise ValueError(f"Duplicate repository evaluation: {repo_name}")
        if matching:
            actual_source, actual_criteria = evaluation_definition(client.evals.retrieve(matching[0].id))
            if actual_source != spec["data_source_config"] or actual_criteria != spec["testing_criteria"]:
                raise ValueError(f"Remote repository evaluation differs: {repo_name}")

    if dry_run:
        for spec in new_memory:
            print(f"Would create memory store: {spec['name']}")
        for name, version, _ in new_toolboxes:
            print(f"Would create toolbox: {name} (default {version})")
        for name, version, _ in new_datasets:
            print(f"Would upload dataset: {name}:{version}")
        for name, _ in new_evaluators:
            print(f"Would create evaluator: {name}")
        for name, _ in new_agents:
            print(f"Would create agent: {name}")
        for item in manifest["evaluations"]:
            name = f"{item['name']}-repo"
            if not any(ev.name == name for ev in remote_evaluations):
                print(f"Would create evaluation recipe: {name} (no run)")
        return

    for spec in new_memory:
        project.beta.memory_stores.create(body=spec)
        print(f"Created memory store: {spec['name']} (stored memories are not restored)")
    for name, default_version, versions in new_toolboxes:
        for spec in versions:
            created = project.toolboxes.create_version(name, body={
                "tools": spec["tools"],
                "skills": spec["skills"],
                "policies": spec["policies"],
                "metadata": spec["metadata"],
            })
            if created.version != spec["version"]:
                raise ValueError(f"Toolbox version mismatch for {name}: expected {spec['version']}, got {created.version}")
        project.toolboxes.update(name, default_version=default_version)
        print(f"Created toolbox: {name} (default {default_version})")
    for name, version, path in new_datasets:
        project.datasets.upload_file(name=name, version=version, file_path=str(path))
        print(f"Uploaded dataset: {name}:{version}")
    for name, spec in new_evaluators:
        created = project.beta.evaluators.create_version(name=name, evaluator_version=spec)
        print(f"Created evaluator: {name}:{created.version}")
    for name, definition in new_agents:
        created = project.agents.create_version(name, definition=PromptAgentDefinition(**definition))
        print(f"Created agent: {name}:{created.version}")
    for item in manifest["evaluations"]:
        name = item["name"]
        repo_name = f"{name}-repo"
        if any(ev.name == repo_name for ev in remote_evaluations):
            print(f"Repository evaluation already exists: {repo_name}")
        else:
            spec = load(ROOT / "evaluations" / component(name) / "evaluation.json")
            created = client.evals.create(
                name=repo_name,
                data_source_config=spec["data_source_config"],
                testing_criteria=spec["testing_criteria"],
            )
            print(f"Created evaluation recipe: {repo_name} ({created.id}); no run started")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("snapshot", "validate", "check", "apply"))
    parser.add_argument("--endpoint", default="https://aihorizons-resource.services.ai.azure.com/api/projects/aihorizons")
    parser.add_argument("--overwrite", action="store_true", help="Replace edited local snapshot files")
    args = parser.parse_args()
    if args.overwrite and args.command != "snapshot":
        parser.error("--overwrite is only available for snapshot")
    if args.command == "validate":
        manifest = validate()
        print(f"Valid snapshot: {len(manifest['agents'])} agents, {len(manifest['datasets'])} datasets, "
              f"{len(manifest['evaluators'])} evaluators, {len(manifest['evaluations'])} evaluations, "
              f"{len(manifest.get('toolboxes', []))} toolboxes, "
              f"{len(manifest.get('memory_stores', []))} memory stores, "
              f"{len(manifest.get('connections', []))} connections")
        return
    with AzureCliCredential() as credential, AIProjectClient(endpoint=args.endpoint, credential=credential) as project:
        if args.command == "snapshot":
            snapshot(project, args.endpoint, args.overwrite)
        else:
            apply(project, args.endpoint, dry_run=args.command == "check")


if __name__ == "__main__":
    main()
