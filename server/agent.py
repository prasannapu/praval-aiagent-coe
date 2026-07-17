"""Enterprise agent and lightweight MCP client adapters for the local POC.

The adapters share the same interface as remote MCP tools, making it simple to
replace their implementations with a production MCP SDK transport later.
"""
import json
import os
from urllib import request
from datetime import date
from pathlib import Path


class MCPClient:
    def __init__(self, root: Path):
        self.data_dir = root / "data"
        self.root = root
        self.activity = []

    def _event(self, source, action, detail):
        self.activity.append({"source": source, "action": action, "detail": detail, "status": "success"})

    def read_enterprise_data(self, filename):
        self._event("Filesystem MCP", "Read resource", filename)
        with open(self.data_dir / filename, encoding="utf-8") as file:
            return json.load(file)

    def search_repository_docs(self, query):
        self._event("GitHub MCP", "Search repository", "README.md · architecture documentation")
        return {
            "title": "Enterprise AI Agent Platform Architecture",
            "repository": "enterprise-ai-agent-poc",
            "summary": "The browser workspace calls a FastAPI AI Agent. The agent selects reusable MCP tools, which access enterprise data and repository knowledge through standardized interfaces.",
            "matches": ["README.md", "docs/architecture.md", "docs/mcp-integration.md"],
            "query": query,
        }


class EnterpriseAgent:
    def __init__(self, root: Path):
        self.mcp = MCPClient(root)
        self.query_count = 0

    def _data(self):
        return (
            self.mcp.read_enterprise_data("customers.json"),
            self.mcp.read_enterprise_data("contracts.json"),
            self.mcp.read_enterprise_data("incidents.json"),
        )

    def dashboard(self):
        customers, contracts, incidents = self._data()
        expiring = [c for c in contracts if c["renewal_date"][:4] <= "2027"]
        return {
            "metrics": {"customers": len(customers), "incidents": len([i for i in incidents if i["status"] == "Open"]), "expiries": len(expiring), "queries": self.query_count},
            "customers": self._customer_rows(customers, contracts, incidents),
            "activity": self.mcp.activity[-5:],
        }

    def _customer_rows(self, customers, contracts, incidents):
        rows = []
        for customer in customers:
            contract = next((x for x in contracts if x["customer"] == customer["name"]), {})
            open_incidents = sum(1 for x in incidents if x["customer"] == customer["name"] and x["status"] == "Open")
            rows.append({**customer, "renewal_date": contract.get("renewal_date", "—"), "open_incidents": open_incidents})
        return rows

    def _gemini_enrichment(self, question, deterministic_answer):
        """Optionally refine the executive summary with Gemini; offline mode stays demo-ready."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return deterministic_answer
        prompt = ("You are an enterprise executive copilot. Rewrite this answer in at most "
                  "two concise sentences. Do not invent data. Question: " + question +
                  " Answer: " + deterministic_answer)
        payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
        endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + api_key
        try:
            call = request.Request(endpoint, data=payload, headers={"Content-Type": "application/json"})
            with request.urlopen(call, timeout=8) as response:
                data = json.loads(response.read().decode())
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return deterministic_answer

    def answer(self, question):
        self.mcp.activity = []
        self.query_count += 1
        query = question.lower()
        customers, contracts, incidents = self._data()
        rows = self._customer_rows(customers, contracts, incidents)
        payload = {"type": "answer", "title": "Enterprise Intelligence", "sections": [], "customers": [], "architecture": None}

        if "architecture" in query or "github" in query:
            payload["title"] = "Architecture Information"
            payload["architecture"] = self.mcp.search_repository_docs(question)
            payload["sections"] = [{"heading": "MCP integration model", "body": "GitHub MCP was used to retrieve repository knowledge. The agent keeps source-specific logic behind MCP tools, so teams can add connectors without changing the user experience."}]
        elif "contract" in query or "expiration" in query or "expiry" in query:
            expiring = sorted(contracts, key=lambda x: x["renewal_date"])
            payload["title"] = "Contract Expirations"
            payload["sections"] = [{"heading": "Renewal pipeline", "body": "{} contracts require forward planning. Prioritize the earliest renewals and accounts with service impact.".format(len(expiring))}]
            payload["customers"] = [r for r in rows if r["name"] in {x["customer"] for x in expiring}]
        elif "open incident" in query or "incidents" in query:
            impacted = [r for r in rows if r["open_incidents"]]
            payload["title"] = "Customers with Open Incidents"
            payload["sections"] = [{"heading": "Service health", "body": "{} customers currently have open incidents. Review critical and high severity work with account leadership.".format(len(impacted))}]
            payload["customers"] = impacted
        elif "microsoft" in query:
            customer = next(r for r in rows if r["name"] == "Microsoft")
            payload["title"] = "Microsoft Account Summary"
            payload["customers"] = [customer]
            recommendation = "Schedule an executive review: Microsoft has {} open incidents, a {} health status, and renews {}.".format(customer["open_incidents"], customer["health"], customer["renewal_date"])
            payload["sections"] = [{"heading": "Executive recommendation", "body": self._gemini_enrichment(question, recommendation)}]
        else:
            payload["type"] = "briefing"
            payload["title"] = "Executive Briefing"
            total_revenue = sum(float(c["revenue_millions"]) for c in customers)
            open_count = sum(r["open_incidents"] for r in rows)
            payload["sections"] = [
                {"heading": "Customer", "body": "{} strategic customers are monitored through the enterprise data layer.".format(len(customers))},
                {"heading": "Revenue", "body": "Managed annual contract value is ${:.1f}M.".format(total_revenue)},
                {"heading": "Incidents", "body": "{} incidents remain open; Microsoft represents the largest concentration.".format(open_count)},
                {"heading": "Contracts", "body": "{} renewals fall within the forward planning horizon.".format(len(contracts))},
                {"heading": "Business Risks", "body": "Medium: active operational incidents could affect renewal confidence for strategic accounts."},
                {"heading": "Recommendations", "body": "Schedule a Microsoft executive review, assign owners to critical incidents, and start renewal readiness plans."},
            ]
            payload["customers"] = [next(r for r in rows if r["name"] == "Microsoft")]
        payload["activity"] = self.mcp.activity
        return payload
