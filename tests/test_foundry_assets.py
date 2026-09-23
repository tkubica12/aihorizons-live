import importlib.util
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest


REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("foundry_assets", REPO / "scripts" / "foundry_assets.py")
assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assets)


def test_exported_snapshot_is_valid_and_keeps_prompts_separate():
    manifest = assets.validate()
    assert len(manifest["agents"]) == len(manifest["datasets"]) == len(manifest["evaluators"]) == 1
    assert len(manifest["toolboxes"]) == 2
    assert len(manifest["memory_stores"]) == 1
    assert "pizza-staff-orders-mcp" in manifest["connections"]
    agent = assets.ROOT / "agents" / manifest["agents"][0]["name"] / manifest["agents"][0]["version"]
    evaluator = assets.ROOT / "evaluators" / manifest["evaluators"][0]["name"] / manifest["evaluators"][0]["version"]
    assert "instructions" not in assets.load(agent / "definition.json")
    assert "prompt_text" not in assets.load(evaluator / "evaluator.json")["definition"]
    toolbox = assets.ROOT / "toolboxes" / "sada-nastroju-pro-ai-borce" / "1" / "toolbox.json"
    staff_toolbox = assets.ROOT / "toolboxes" / "pizza-staff-tools" / "1" / "toolbox.json"
    memory = assets.ROOT / "memory_stores" / manifest["memory_stores"][0]["name"] / "memory_store.json"
    assert len(assets.load(toolbox)["tools"]) == 3
    assert {tool.get("server_label") for tool in assets.load(staff_toolbox)["tools"]} == {
        None, "kb-kb-pizza-mtcxs", "pizza-catalog-mcp", "pizza_staff_orders",
    }
    assert assets.load(memory)["definition"]["kind"] == "default"
    rows = (assets.ROOT / "datasets" / "pizza_customers" / "1.0" / "data.jsonl").read_text(
        encoding="utf-8"
    ).splitlines()
    assert len(rows) == 50
    assert all({"id", "query", "description", "candidate_response"} <= json.loads(line).keys() for line in rows)


def test_changed_dataset_checksum_is_rejected(tmp_path, monkeypatch):
    shutil.copytree(assets.ROOT, tmp_path / "foundry")
    monkeypatch.setattr(assets, "ROOT", tmp_path / "foundry")
    dataset = assets.ROOT / "datasets" / "pizza_customers" / "1.0" / "data.jsonl"
    dataset.write_bytes(dataset.read_bytes() + b'{"query":"not reviewed"}\n')
    with pytest.raises(ValueError, match="checksum differs"):
        assets.validate()


def test_snapshot_refuses_to_replace_local_edits(tmp_path):
    target = tmp_path / "prompt.txt"
    target.write_text("local edit", encoding="utf-8")
    with pytest.raises(FileExistsError):
        assets.snapshot_file(target, b"portal edit", overwrite=False)
    assert target.read_text(encoding="utf-8") == "local edit"


def test_connection_inventory_excludes_credentials_and_sensitive_metadata():
    connection = SimpleNamespace(
        name="observability",
        as_dict=lambda: {
            "type": "AppInsights",
            "target": "/subscriptions/abc/resourceGroups/demo",
            "isDefault": True,
            "credentials": {"type": "ApiKey", "key": "private"},
            "metadata": {"displayName": "demo", "ApplicationInsightsConnectionString": "private"},
        },
    )
    inventory = assets.connection_inventory(connection)
    assert inventory["credential_type"] == "ApiKey"
    assert inventory["metadata"] == {"displayName": "demo"}
    assert "private" not in json.dumps(inventory)


def test_connection_inventory_rejects_secret_in_target():
    connection = SimpleNamespace(
        name="unknown",
        as_dict=lambda: {"type": "RemoteTool", "target": "https://example.com/mcp?token=private"},
    )
    with pytest.raises(ValueError, match="possible credentials"):
        assets.connection_inventory(connection)
