# Issue tracker: Local Markdown

Issues and specs for this repo live as markdown files in `.scratch/`, committed
with the work. This overrides the workspace-root GitHub tracker
(`../docs/agents/issue-tracker.md`): this repo has no remote and no GitHub issues.
Never run `gh issue` commands for this repo.

## Conventions

- One feature per directory: `.scratch/<feature-slug>/`
- The spec is `.scratch/<feature-slug>/spec.md`
- Implementation issues are one file per ticket at `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01`, never a single combined tickets file
- Triage state is recorded as a `Status:` line near the top of each issue file (see `triage-labels.md` for the role strings)
- Blocking edges are a `Blocked by:` line near the top of each issue file
- Comments and conversation history append to the bottom of the file under a `## Comments` heading

## When a skill says "publish to the issue tracker"

Create a new file under `.scratch/<feature-slug>/` (creating the directory if needed).

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path. The user will normally pass the path or the issue number directly.

## When a skill says "close" a ticket

Set `Status: done` in the ticket file and append a `## Comments` entry naming the commit(s) that resolved it.
