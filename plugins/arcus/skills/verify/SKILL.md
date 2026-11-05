---
name: verify
description: Use when a developer or their coding agent has changed a user-facing flow and wants to prove the change works, or asks to verify a story, a branch or a PR with Arcus. Finds the test cases Arcus holds for the story, automates them as .sigma tests, runs them against the local app until they pass, writes one "Ran locally" comment for the PR, and pushes the tests as pending cases on the story. Never edits what an approved case expects, and never accepts.
---

# Verify: prove a change with the story's own cases

The story's test cases in Arcus say what must work. You automate those, run them against the app on this machine, and
show the result on the PR. You do not decide from the diff what to check: the cases do. The diff only tells you which
cases this change touches.

This skill is a flow over the others. Each step follows that skill's rules and gates: `/arcus:author` for writing,
`/arcus:run` for running, `/arcus:push` for sending. Read each one when you reach its step.

If `arcus sprint --help` fails, the CLI is too old for this flow. Stop and run `/arcus:setup`. A command that fails with
exit `2` (not signed in) also goes to `/arcus:setup`. Never sign the user in yourself.

The comment's shape, the marker and the intent-change table are in `${CLAUDE_PLUGIN_ROOT}/references/verifying.md`.

## 1. The story

You need an issue key and the sprint that holds it.

- The user named the story: use it.
- Otherwise look at the branch name and the commit messages for an issue key. Say which one you found and where.
- Then find the sprint: `arcus sprint list --json`, and `arcus issue list <sprint> --json` for each active sprint
  until the key is there.
- Neither is plain: ask. Never guess a story. A wrong story means the wrong bar.

Say the story's title and the sprint in one line before going on.

## 2. Can this machine run it

As in `/arcus:run`: `arcus browsers list`, and the project's platforms need `web`.

Then the app: where the tests run. The repo's README may name targets (local, edge, a preview). Use local unless the user
names another, or the change is only on a deployed target. Say the address before the first run. Check it answers
(`curl -sS -o /dev/null -w '%{http_code}' <url>`). If the agent or the app is down, stop and say the one thing to
start. Do not start it yourself. The target never changes where cases live or where the push goes.

## 3. The cases

```
arcus test list --sprint <id> --issue-id <key> --json
```

Each entry is a case: its id, title and `acceptance_status`. Then read what each one expects:

```
arcus test show <case id> --json
```

It gives the case's preconditions, its steps and each step's expected result. Read them all before you write a line.

- **No cases.** Stop. QI generates a story's cases: tell the user to generate them in QI for this story, then run
  `/arcus:verify` again. Do not invent cases to fill the gap.
- **Cases.** Read the diff (`git diff <base>...HEAD`). Say which cases the change touches, and why in a few words. Those
  are the cases to automate. A case the change does not touch is left alone; name it as not touched.
- **A changed flow no case covers.** One candidate test for it, marked **new** in the comment. It is pushed pending like
  the rest and someone reviews it in QI. Never more than the change needs.

Show the list (case, touched or new, why) and go on. Ask only if the list is long or unclear.

## 4. Author

For each case, one test through `/arcus:author`'s rules, with these additions:

- The test's title is the case's title, exactly. That is how the push links the file to the case.
- The steps follow the case's steps, in its order. Each expected result is a `verify`. A case step that the language
  cannot express is a gap: say so in the comment. Do not drop it quietly.
- If a file for the case already exists in the repo, edit that one.

`arcus check` must be clean for each file before you run it.

## 5. Run until green

Each test through `/arcus:run`'s rules, against the address from step 2. Run them one after another, one line each.
When a test fails, find the owner first, as `/arcus:run` says, with the screenshot. Then:

| Owner | Do |
|---|---|
| The code of this change | Fix the code. Run again. This is the point of the loop |
| The test (a wrong locator, a missing wait) | Fix the test, with `/arcus:author`'s rules. Run again |
| The case: the app now does on purpose what the case says it should not | **Do not edit the step or the `verify`.** It is an intent change. Leave the test failing and list it (step 6) |
| The setup | Say what to fix and stop |
| The evidence does not decide | Show it and ask |

The limits of `/arcus:run` hold: three rounds per test, stop at once on the same failure twice.

**Never weaken a test to make it pass.** No deleted `verify`, no expected value changed to what the app showed, no wait
added to hide a fault. Any edit to a test's steps or `verify` lines after its first run is listed in the comment.

## 6. The comment

Write one "Ran locally" comment, in the shape `references/verifying.md` gives, every time you ran anything, including
when a setup or data problem stopped the run early: then the comment is how the reviewer learns what was not proven. It
says:

- that this is the developer's own run on their machine, with the commit, browser and version,
- each case: automated or new, passed or failed, steps, duration, and for a failure the step and the screenshot path,
- proposed intent changes: the case, the step, what the case expects, what the app now does,
- what did not run, and why,
- any change to a test's steps or `verify` lines after its first run.

It never says "passed in Arcus", and never calls itself the PR's check.

Posting it shows it to the team. Show the comment, and post it only after a yes, once per PR. Find the PR with `gh pr
view --json number,url`. A later run edits the same comment, found by its marker, and needs no new yes. With no PR,
print the comment for the user to paste.

## 7. Push, pending

If `ARCUS_PUSH_DIRECT_LIBRARY` is set in the environment, stop: say it writes straight to the library, and to unset it.

Hand over to `/arcus:push` for the tests from step 4, with `--sprint <id> --issue-id <key>`. Its dry run and its yes
apply. The tests land in QI as pending cases on the story. Never pass `--accept`: accepting is the developer's, after
the PR merges.

## 8. Report

Say, briefly: the story, the cases automated and new, the run result of each, the intent changes waiting for a decision,
where the comment is, and what was pushed. Then the next step:

- Failures that are the code's: fix and run `/arcus:verify` again.
- Intent changes: QA or the PM decides them in QI. Nothing to do here until they do.
- All passed and pushed: once the PR merges, the developer accepts the cases into Arcus, and QA confirms them.

## What this skill never does

- Choose what to test from the diff alone, or invent cases for a story that has none.
- Edit a step or a `verify` of an approved case to match what the app now does.
- Weaken a test, or hide a gap.
- Post the comment without a yes, or add a second one.
- Say a local run passed in Arcus.
- Push with `--accept`, or with `ARCUS_PUSH_DIRECT_LIBRARY` set. Accept anything.
- Start the agent or the app, sign in, or edit `arcus.json`, `arcus.lock` or `.arcus/`.
