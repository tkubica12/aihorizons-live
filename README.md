# aihorizons-live

## Lokální pizza chat

Přihlaste se do Azure CLI (`az login`) pod účtem s přístupem k Foundry projektu
`aihorizons` a spusťte z kořene repozitáře:

```powershell
uv sync --extra dev
uv run uvicorn pizza_mcp.web:app --host 127.0.0.1 --port 8777
```

Otevřete [http://127.0.0.1:8777](http://127.0.0.1:8777). Web komunikuje
s existujícím Foundry agentem `nejlepsi-ai-pizza-na-pankraci`; přístupové údaje
zůstávají pouze v Python backendu. Pro jiný projekt nebo agenta lze nastavit
`FOUNDRY_PROJECT_ENDPOINT` a `FOUNDRY_AGENT_NAME`. Konverzace se udržuje v rámci
jedné záložky, tlačítko „Nový chat“ začne nový rozhovor.

Jde o **lokální demo bez přihlášení zákazníka**. Server nespouštějte na veřejné
síťové adrese a neposílejte do něj skutečná zákaznická data. Pro testy použijte
`uv run pytest tests/test_web.py`.

Definice agenta a evaluací v datové rovině Foundry jsou uložené zvlášť
v [`foundry/`](foundry/README.md). Skript `scripts/foundry_assets.py` umožňuje
validaci, opětovné načtení z portálu a explicitní obnovu bez spuštění evaluace.