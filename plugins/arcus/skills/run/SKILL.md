---
name: run
description: Use when a developer asks to run, try, execute or verify an Arcus test on their machine, to watch a test in a browser, or to find out why a test fails. Runs one .sigma test locally with arcus run, reads the result and the screenshot, and says whether the test, the app or the setup is wrong. Sends nothing to Arcus and needs no sign-in. Does not push.
---

# Run: try a test in a browser on this machine

`arcus run` runs **one** web test in a browser on this machine. The browser comes from the local Testsigma agent. Nothing
is sent to Arcus, and no sign-in is needed. The CLI gives you the result. Your job is to read it, look at the evidence,
and tell the user what happened and who owns it: the test, the app, or the setup.

If the CLI is missing, too old for `run` (`arcus run --help` fails), or the repo has no project, stop and run the `setup`
skill (`/arcus:setup`). Do not send the user to sign in: a run does not need it.

Details, the result fields and the failure messages are in `${CLAUDE_PLUGIN_ROOT}/references/running.md`.

## 1. Which test

- The user named a file or a title: use it. They just wrote or changed files in this session: use those.
- Otherwise ask which test. Do not run every test in the project unasked.
- Several tests: run them one after another, and report one line each. The CLI runs one test at a time and has no
  suite result, so never claim one.
- Read `arcus.json`. With several projects, ask which one unless the file makes it plain, and pass
  `--project <folder name>`. The test file must be in that project's `tests/` folder.

## 2. Can this machine run it

```
arcus browsers list
```

- It lists browsers (name, version, engine): good. The default is Chrome for Testing, then Chrome. The user can ask for
  another one in the list.
- `Cannot reach the Testsigma agent` (exit `3`): stop. Say the Testsigma agent is not running and the user must start
  it. You cannot start it. Do not install a browser, and never run `playwright install`.
- Read the project's platforms (`arcus project platforms`). A run needs `web` in them. Without it, `arcus run` stops with
  `device runs are not supported yet`. Say that Android and iOS tests cannot be run yet. Do not edit `arcus.json`. Adding
  `web` (`arcus project platforms add web`) makes `arcus check` stricter for every test in the project, so it is the user's
  decision.

## 3. What the test needs

Read the test, and each element it uses (`@<path>`).

- **Addresses.** Every `nav` target. A test that opens `{env.base_url}/…` needs `--base-url`. There is no relative
  `nav`.
- **Values.** Search the test and its elements for `{env.<name>}`. Each name needs `--var <name>=<value>`.
- Where a value comes from: what the user said, or non-secret test data the repo shows (a dev-server address, a test
  username). Ask for what you cannot find, one question at a time. Never invent a value.
- **A secret** (a password, a token, a key) is never typed by you and never asked for in chat. Pass it by reference:
  `--var password="$ARCUS_TEST_PASSWORD"`. The variable must already be set in the terminal that started Claude Code. Check
  it is set without printing it: `[ -n "$ARCUS_TEST_PASSWORD" ] && echo set`. If it is not set, tell the user to set it
  and restart Claude Code, or to run the command in their own terminal. Do not read `.env*` or credential files.

Before you run, tell the user in two lines: the address or addresses the test opens, and the browser, and whether it is
hidden or visible. Run only when the user asked for the run, or said yes to your offer. Never run a test against an
address the user has not seen, or one that you only guessed.

## 4. Run

```
arcus run <file> --json --project <name> [--base-url <url>] [--var <name>=<value>] [--headed] [--browser <name>]
```

- Headless is the default. Add `--headed` only when the user asks to watch, or when you need to see a failure that the
  screenshot does not explain. Say that a window opens.
- A failed step keeps a screenshot. Ask for `--screenshots all` only if the user wants proof of a pass.
- The default time limit is 300 seconds (`--timeout <seconds>`). Give the Bash tool a longer timeout than that.
- stdout is one JSON object. A setup error is JSON on stderr and stdout is empty.

## 5. Read the result

Read `run.status` first, then the exit code. Exit `1` covers three different things.

| `run.status` | Exit | Say, and do |
|---|---|---|
| `passed` | `0` | Passed: the browser and version, the duration, the step count. A local pass is not an Arcus run. Offer `/arcus:push` |
| `failed` | `1` | The step that failed (`failedStep.description`), the message in plain words, the screenshot. Go to step 6 |
| `refused` | `1` | The test did not compile, so no browser started. `run.diagnostics` is what `arcus check` says. Fix it with the rules of `/arcus:author` |
| `interrupted` | `1` | The run was stopped, or the browser went away (`run.problem`). It is not a verdict on the test. Offer to run again |
| none (setup error) | `3` | The message on stderr, with its `remediation`. See the table in `references/running.md` |

`run.problem` with no `failedStep` means the run failed in a way no step explains. Say it as it is and where the log is
(`run.artifactsDir`). Do not loop on it.

## 6. A failure: who owns it

Look before you edit anything.

1. Read `failedStep`: the step as written, and the message.
2. Open the screenshot with the Read tool. It is a `.jpg` file. It shows the page at the failing step.
3. Read the line in the test, the element it uses, and the app source for that screen.

Then say who owns the failure, with the evidence:

- **The test is wrong.** A locator that is not in the app, an expected text that differs, a missing wait for something that
  loads late. Fix the test: follow `/arcus:author` for the edit (`check`, then `fmt`, then `check`), and
  `${CLAUDE_PLUGIN_ROOT}/references/editing.md` if the file is already pushed. Say what you changed and why. Run again.
- **The app is wrong.** The test states what the app should do, and the app does not. Report it as a finding. Do not
  change the test to match a bug.
- **The setup is wrong.** The address cannot be reached, a `{env.…}` name has no value, the browser cannot start. Tell
  the user what to fix.
- **The evidence does not decide.** Show it, and ask. Never guess which side is right.

Limits:

- At most **three** rounds of fix and run. Stop at once if the same step fails with the same message twice. Then show what
  you know and stop.
- **Never make the test pass by making it weaker.** Do not delete a `verify`, change an expected value to the value the app
  showed, or add a wait to hide a fault, unless the user says the app is right.

## 7. Report

Say, briefly:

- the test, its result, the browser and version, and the time,
- for a failure: the step, the owner, and the evidence in a sentence,
- any file you changed (the user should look at `git diff`),
- the next step: for a pass, `/arcus:push`. For a failure that is the app's, nothing to push yet. For a change on a story,
  `/arcus:verify` runs the story's cases and writes the PR comment.

## Say no to what a local run cannot do yet

Datasets (`for row in dataset …`, refused as `ARC1201`), groups, Android and iOS, running many tests as one suite, and
running on Arcus's own machines. Say it is not supported yet, and offer what is.

## What this skill never does

- Run a test the user did not ask to run, or against an address they have not seen.
- Put a secret on the command line, ask for one in chat, or read `.env*` files.
- Weaken a test so it passes.
- Push, sign in, or edit `arcus.json`, `arcus.lock` or `.arcus/`.
- Install a browser or start the agent.
- Say a test "passes in Arcus": a local run proves only the local run.
