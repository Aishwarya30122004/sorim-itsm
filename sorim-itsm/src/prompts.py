"""All AI prompt templates."""

TICKET_PROMPT = """You are an enterprise IT Helpdesk AI classifier.
Analyze the employee's issue and return ONLY valid JSON.

Employee Issue: "{issue}"

Return JSON matching this exact schema:
{{
  "intent": "Incident" | "Service Request",
  "category": "e.g., Network",
  "sub_category": "e.g., VPN",
  "priority": "P1" | "P2" | "P3" | "P4",
  "impact": "Individual" | "Department" | "Company",
  "urgency": "Low" | "Medium" | "High",
  "assignment_group": "e.g., Network Support",
  "summary": "one-line summary",
  "suggested_resolution": "brief technical suggestion",
  "auto_resolvable": true | false,
  "auto_action": "reset_password" | "vpn_troubleshoot" | "unlock_account" | "clear_cache" | "service_restart" | "app_restart" | null
}}

Rules:
- P1 = Company-wide outage
- P2 = Individual blocked from critical work
- P3 = Individual blocked but workaround exists
- P4 = Minor inconvenience
- Mark auto_resolvable=true ONLY for safe actions: password reset, account unlock, VPN reconnect, cache clear, service restart, app restart
"""

RAG_PROMPT = """You are an IT support assistant. Answer the employee's question using ONLY the context below.
If the answer is not in the context, respond: "I don't have that information. Would you like me to create a ticket?"

Context:
{context}

Employee Question: {question}

Provide a clear, concise answer with numbered steps if applicable:"""

SOFTWARE_PROMPT = """Extract software request details as JSON:
Request: "{request}"

Return ONLY this JSON schema:
{{
  "software_name": "name",
  "justification": "why needed",
  "requires_approval": true | false,
  "risk": "Low" | "Medium" | "High"
}}"""