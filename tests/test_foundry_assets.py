import importlib.util
import json
import shutil
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("foundry_assets", REPO / "scripts" / "foundry_assets.py")
assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assets)


def test_exported_snapshot_is_valid_and_keeps_prompts_separate():
    manifest = assets.validate()
    assert len(manifest["agents"]) == len(manifest["datasets"]) == len(manifest["evaluators"]) == 1
    agent = assets.ROOT / "agents" / manifest["agents"][0]["name"] / manifest["agents"][0]["version"]
    evaluator = assets.ROOT / "evaluators" / manifest["evaluators"][0]["name"] / manifest["evaluators"][0]["version"]
    assert "instructions" not in assets.load(agent / "definition.json")
    assert "prompt_text" not in assets.load(evaluator / "evaluator.json")["definition"]
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
