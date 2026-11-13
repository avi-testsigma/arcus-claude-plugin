---
description: Show what the Arcus plugin does and how to use it
---

The Arcus plugin guides you through the developer side of the Arcus CLI and the QI workflow. QI is the quality service:
it keeps test cases as versions and a reviewer accepts them. Tests and elements are `.sigma` files. The `arcus`
command-line tool checks them offline, runs them on your machine, and sends them. The plugin sends nothing by itself.

A project works in one mode. **direct**: a push puts tests in Arcus at once. **qi**: a push sends tests to QI as
versions, and a reviewer accepts them. Elements go to Arcus in both modes.

## Skills

- `/arcus:setup` — Check the CLI, the sign-in, the project, its mode and platforms, and whether this machine can run
  web and Android tests. Stops with the one thing to do.
- `/arcus:context <issue>` — Qi mode. Read the issue, its cases and the policy from QI. Plan which tests to write.
- `/arcus:author [what to test]` — Write tests and elements as `.sigma` files. Loops check and format until clean.
- `/arcus:run [test]` — Run one test on web or Android (`--platform`, `--device`, `--app`). Says whether the test, the
  app or the setup is wrong. Nothing is sent.
- `/arcus:verify <issue>` — Qi mode. Run every case of an issue and report each one.
- `/arcus:push [files]` — Dry run first, a plan in words, a push after your yes. Explains every result and refusal.
- `/arcus:accept [files]` — Qi mode. Accept pushed versions into Arcus, after a policy check and your yes.
- `/arcus:sync` — Show where each file stands. Pull QI's changes. Detach or attach a file. Pipeline check.
- `/arcus:mode` — Show the project mode. Switch it with a dry run and your yes.
- `/arcus:pr-check` — Qi mode, usually in CI from a "/arcus test" PR comment. Run the issue's tests on the deployed PR
  build and on the base build, write scenarios to try to break the change, and have QI judge what fails on the PR
  alone into one check and one PR comment. A story case that breaks blocks the merge; the rest is advisory.

## Typical flow

1. `/arcus:setup` once per repo. Sign in yourself when it asks.
2. Qi mode: `/arcus:context CW-412` to see what QI expects. Direct mode: go to step 3.
3. `/arcus:author` — Claude writes the files and checks them.
4. `/arcus:run` — Claude runs the test and tells you what happened.
5. `/arcus:push` — read the plan, say yes, and commit `arcus.lock` with the tests.
6. Qi mode: `/arcus:sync` to see the review, `/arcus:verify` before a merge, `/arcus:accept` when the policy allows.

## Troubleshooting

- `arcus: command not found` — install the CLI (`/arcus:setup` gives the command).
- Exit code `2` — not signed in, or the region differs. Sign in yourself, then try again.
- Exit code `3` — wrong setup. Read the message and its `remediation`. A mode and lock mismatch: `/arcus:mode`.
- A push is refused — the plan says which file and why. `/arcus:push` explains each reason.
- `Cannot reach the …agent` — start the local test agent. Only web runs need it.
- `The Android tools (adb) were not found` — tell the CLI where the tools are: the `ARCUS_ANDROID_TOOLS_DIR` variable
  in your shell, or `arcus config set android.toolsDir <folder>`. `/arcus:setup` explains it.
- Several Android devices are ready — pass `--device <serial>`. `arcus device list` shows them.
- An Android step fails with only `Step failed` — Claude reads `results.ndjson` and the screenshot of the run. Ask it to.
- Not sure which commands the CLI has — `arcus help --json` prints all of them.
