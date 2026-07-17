# Enterprise AI Agent Platform POC

An executive-ready FastAPI demonstration of MCP as a reusable enterprise integration layer. It runs entirely locally using MCP-shaped filesystem and repository adapters; `GEMINI_API_KEY` is optional and enables Gemini refinement for the Microsoft executive recommendation.

## Run locally

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn server.app:app --reload
```

Open `http://127.0.0.1:8000`.

## MCP demo model

`Browser UI → AI Agent → MCP Client → Filesystem MCP / GitHub MCP → enterprise sources`

The Filesystem MCP adapter reads the JSON data files. The GitHub MCP adapter returns repository architecture knowledge for a fully local POC. Both tool invocations are rendered in the UI’s MCP Activity panel to make the integration visible in an executive demonstration.
