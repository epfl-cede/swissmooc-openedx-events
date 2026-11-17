/skill:implement [bench:implement] Implement every ticket under .scratch/ in dependency order, frontier first. One commit per ticket; set the ticket Status to done when it is finished.

You are running unattended: no human will read your messages or answer questions until the run ends. Never stop to ask or to wait for approval. When something is not settled by the ADR, choose the simplest option consistent with the ADR, record the choice in the ticket's ## Comments, and continue.

Pre-agreed test seams (do not ask to confirm them):
1. The HTTP endpoint, exercised through the Django test client, with the package mounted in a test host project via the documented URL include.
2. The OpenedxEvent manager query methods.
3. Migrations in sync with models (makemigrations --check).

Tooling: there is no host Python. Provide a Makefile with test and lint targets that run in Docker, and use them. Run the full suite at the end.

Code review: fixed point is the tag bench-base; the spec is docs/adr/0001-extract-receiver-app-into-pip-package.md plus the tickets under .scratch/.
