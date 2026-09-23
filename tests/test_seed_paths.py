"""Seed fixtures must remain discoverable from a non-editable wheel."""

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_explicit_seed_root_for_wheel_install():
    script = """
from pizza_mcp.seed import FIXTURE, SCHEMA, load_fixture
from pizza_mcp.order_seed import FIXTURE as ORDER_FIXTURE, SCHEMA as ORDER_SCHEMA, load_orders
assert FIXTURE.is_file() and SCHEMA.is_file()
assert ORDER_FIXTURE.is_file() and ORDER_SCHEMA.is_file()
assert len(load_fixture()["pizzas"]) == 12
assert len(load_orders()["orders"]) == 6
"""
    env = {**os.environ, "PIZZA_DATA_ROOT": str(ROOT)}
    subprocess.run([sys.executable, "-c", script], cwd=ROOT, env=env, check=True)
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert 'PIZZA_DATA_ROOT="/app"' in dockerfile
