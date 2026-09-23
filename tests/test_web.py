from starlette.testclient import TestClient

from pizza_mcp import web


def test_chat_creates_and_continues_conversation(monkeypatch):
    calls = []

    def fake_agent(message, conversation_id):
        calls.append((message, conversation_id))
        return "Máme Margheritu.", "conv_demo123"

    monkeypatch.setattr(web, "ask_agent", fake_agent)
    with TestClient(web.app) as client:
        first = client.post("/api/chat", json={"message": " Máte pizzu? ", "conversation_id": None})
        assert first.status_code == 200
        assert first.json() == {"answer": "Máme Margheritu.", "conversation_id": "conv_demo123"}
        second = client.post("/api/chat", json={
            "message": "A co alergeny?", "conversation_id": first.json()["conversation_id"],
        })
        assert second.status_code == 200
    assert calls == [("Máte pizzu?", None), ("A co alergeny?", "conv_demo123")]


def test_invalid_requests_do_not_reach_foundry(monkeypatch):
    def fail(*args):
        raise AssertionError("Foundry must not be called")

    monkeypatch.setattr(web, "ask_agent", fail)
    with TestClient(web.app) as client:
        for data in (
            {"message": ""},
            {"message": "x" * 4001},
            {"message": "ahoj", "conversation_id": "wrong"},
            {"message": "ahoj", "conversation_id": 10},
            ["ahoj"],
        ):
            assert client.post("/api/chat", json=data).status_code == 400
        assert client.post("/api/chat", content="not json").status_code == 400


def test_agent_failure_is_reported(monkeypatch):
    def fail(*args):
        raise RuntimeError("service unavailable")

    monkeypatch.setattr(web, "ask_agent", fail)
    with TestClient(web.app) as client:
        response = client.post("/api/chat", json={"message": "Ahoj"})
    assert response.status_code == 502
    assert "error" in response.json()
    assert "service unavailable" not in response.text


def test_page_and_assets():
    with TestClient(web.app) as client:
        assert "Pizza na Pankráci" in client.get("/").text
        for asset in ("style.css", "app.js", "pizza.svg"):
            assert client.get(f"/static/{asset}").status_code == 200
        assert client.get("/static/secret.txt").status_code == 404
