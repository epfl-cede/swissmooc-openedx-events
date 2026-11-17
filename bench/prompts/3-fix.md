[bench:fix] Address every code-review finding you consider valid and say which ones you reject and why. If no code-review report is in this conversation, first read and follow the code-review skill with fixed point bench-base.

You are running unattended: no human will read your messages or answer questions until the run ends. Never stop to ask or to wait for approval. When something is not settled by the ADR, choose the simplest option consistent with the ADR, record the choice in the ticket's ## Comments, and continue.

Then run make lint and make test, fix failures, and commit. Finish with a short summary: tickets done, test count, known gaps.
