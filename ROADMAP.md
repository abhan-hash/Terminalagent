# Roadmap

## Where we are
A working terminal coding agent: LangGraph loop, `read_file` / `write_file` /
`run_command` tools, y/n approval before writes and commands, repository
context, and LangSmith tracing.

## How this list works
Each phase adds one big capability. Small things (new tools, flags, approval
changes) get added during a phase, only when that phase actually needs them.

---

## 1. Docker sandbox
**Adds:** commands run inside a container, not on your machine.
- Workspace mounted into the container, no network, CPU/memory limits, timeout.
- *On the way:* an auto-approve mode that is only allowed inside the sandbox.

**Done when:** `rm -rf /` from the agent can't touch your real system.
**Resume line:** "Sandboxed tool execution in Docker with network isolation and resource limits."

## 2. Eval harness
**Adds:** a score that shows how good the agent is.
- 20–30 small tasks of your own. Each one is a starting repo, a prompt, and a check script.
- 20–50 tasks from SWE-bench Lite or Verified, so the score is on a benchmark people know.
- A runner that copies the repo, runs the agent in the sandbox, runs the check,
  and records pass/fail, steps, tokens, cost, and time.
- Run the same evals on 2–3 models and compare pass rate, cost, and latency.
- Group failed tasks by cause (wrong file, context overflow, gave up, bad command).
  Each later change should say which group it fixes.
- *On the way:* a `run_task()` function so the agent can run without the
  terminal. Add `edit_file` or code search only if failed tasks show they're needed.

**Done when:** one command prints a pass rate per model. Write the baseline numbers down.
**Resume line:** "Built an eval harness on SWE-bench Lite and 30 custom tasks. Raised pass rate from X% to Y%."

## 3. Context management
**Adds:** the agent can handle long tasks without running out of context.
- Count tokens per call, trim old tool output, summarize old turns.
- Add a few long tasks to the eval set to measure it.

**Done when:** long tasks pass and tokens per task drop. Measure both with the evals.
**Resume line:** "Cut tokens per task by Z% with no drop in pass rate."

## 4. Persistent sessions and memory
**Adds:** the agent remembers things after you close it.
- Save sessions to SQLite and resume them by ID.
- The agent writes notes about the repo to a file that loads on the next run.

**Done when:** you can quit, restart, and continue the same task.

## 5. GitHub issue to pull request
**Adds:** point the agent at a GitHub issue and it opens a PR.
- Fetch the issue, work on a branch in the sandbox, run tests, push, open the PR.
- *On the way:* git tools and the permission rules this needs.

**Done when:** a real issue on a test repo becomes a real PR.
**Resume line:** "Agent resolves GitHub issues end to end and opens PRs."

## 6. Ship it
- README with an architecture diagram, eval results table, model comparison,
  failure breakdown, and a demo GIF.
- Unit tests for the tools, and CI that runs them plus a small eval set.
- Installable as a CLI command.

---

## Rules for the numbers
- Every claim on the resume must come from a run you can repeat.
- Compare against the baseline from phase 2, on the same tasks and model.

## Interview check
Before calling it done, answer these without looking at the code:
- Why does `interrupt()` re-run the tool from the start, and how are side effects kept safe?
- What can the sandbox still not stop?
- How do you know the custom eval tasks aren't too easy?
- Where does the agent fail most often, and why?

## Target roles
Agent, tool-use, LLM-eval, and developer-tools roles. For RAG or fine-tuning
roles, add one small second project later.
