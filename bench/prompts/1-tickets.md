/skill:to-tickets [bench:tickets] Break docs/adr/0001-extract-receiver-app-into-pip-package.md into 3 to 5 tickets.

You are running unattended: no human will read your messages or answer questions until the run ends. Never stop to ask or to wait for approval. When something is not settled by the ADR, choose the simplest option consistent with the ADR, record the choice in the ticket's ## Comments, and continue.

Skip the "quiz the user" step: any breakdown of 3 to 5 tickets is approved. Publish the tickets and commit them.

Scope: this repository only, ADR decisions 1-10 and the webhook contract. Out of scope: catalog consumer wiring (decision 12), CMS fan-out (decision 11), the extras switch-over runbook, and any change outside this repository.

Tracker: local markdown, see docs/agents/issue-tracker.md.
