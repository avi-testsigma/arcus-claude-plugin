# Design: the Arcus authoring plugin (0.7.0)

The first plugin captured Claude Code sessions and pushed `*.spec.ts` tests with the old `testsigma` CLI. The
`arcus` CLI changes the flow completely, so this plugin starts over. What the CLI does is in
`arcus-cli/docs/cli-docs/` (the features and behaviours document). This note says what the plugin does with it.

## Decisions

- **Session capture is gone.** No hooks, no ingest, no ticket mapping, no session-linking. The plugin sends nothing
  itself; the CLI is the only thing that talks to Arcus.
- **Sprint and story mapping is gone.** The new CLI had no such concept. It came back with the CLI's sprint, issue and
  QI push commands, for `verify`: see `design-verify-flow.md`.
- **No run in 0.7.0.** The CLI did not run tests then. Running arrived in 0.8.0: see `design-run-skill.md`. What 0.7.0
  skipped for want of a run (the live-target preflight, reading run results, a verify-by-running loop) is there. The
  Android device and `adb` flow is still skipped: `arcus run` tests web only.
- **Version 0.7.0** (the capture plugin was 0.6.0). The plugin keeps the name `arcus` and the marketplace `testsigma`.
- **The migration plugin stays separate** (`plugins/testsigma`, on its own branches).
- **No Python, no scripts, no hooks.** The plugin is skills and one command, plus tests for the documents.

## Principles

1. **The CLI carries the catalogue.** The plugin holds no list of steps, forms or locators. It tells the agent to ask:
   `arcus docs --json`, `arcus docs <action>`, `arcus docs --topic <id>`. What compiles is whatever the installed CLI
   says. (Same rule as the migration plugin's ADR on the catalogue.)
2. **`arcus check` is the gate.** The agent never decides that a document is valid. It runs `check --json` and acts on
   the diagnostics: apply a `certain` fix, ask before a `suggested` one, re-run.
3. **Nothing is sent without a plan the user has seen.** `push` starts with `push --dry-run` and shows it. A real push
   needs a yes.
4. **The user signs in, not the agent.** The agent runs `arcus auth status`. If it is not signed in, it tells the user
   to run `arcus auth login` and stops. It never handles credentials.
5. **Arcus is the source of truth.** There is no `pull`. The skills say so and never invent a way around a conflict.
6. **Read the repo before writing.** `arcus.json` says the project, the platforms and `arcusDir`. The agent reads it and
   never assumes `tests/arcus`.

## Skills

| Skill | Does |
|---|---|
| `setup` | Checks the CLI is installed and recent enough, the user is signed in, the repo has a project (`arcus init`), and the platforms are right. Stops with an exact next step when one is missing |
| `author` | Writes tests and elements as `.sigma` files for what the user asks. Learns the language from `arcus docs`, writes, runs `check`, fixes, runs `fmt`. Uses element files for `@refs` and respects the platforms |
| `push` | `push --dry-run`, shows the plan, asks, pushes, then explains every result (`refused`, `conflict`, `missing`, server lines) and what to do next |

One command: `/arcus:help`. The skills are called as `/arcus:setup`, `/arcus:author`, `/arcus:push`.

## Skipped in 0.7.0 (needed a run)

Done in 0.8.0, except the device preflight: see `design-run-skill.md`.

- Run a test and read the results.
- Device and app preflight for Android and iOS (still skipped: a run is web only).
- Any "verify by running" loop in `author`.

## Tests and evals

The plugin is documents, so its tests check documents: manifests parse, each skill has a name and a description, a
skill stays inside a size budget, no skill names a command or option the CLI does not have (checked against a real CLI
when one is on the PATH), and no skill carries a copy of the language.

**Evals were deferred** until the run version, and came with 0.8.0 (`plugins/arcus/evals/`). The cases it listed: `push` refuses to push before a dry run;
`author` does not delete a `verify` to make a check pass; `author` stops with a message on a request for an `api`
step; `setup` does not guess the region. Run-related cases (read a failed step, a missing device) join them then.
