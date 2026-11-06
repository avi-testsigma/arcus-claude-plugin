---
description: Show what the Arcus plugin does and how to use it
---

The Arcus plugin helps you write Arcus tests in your repo, try them in a browser, and send them to an Arcus project. Tests
and elements are `.sigma` files. The `arcus` command-line tool checks them offline, runs them on your machine, and
pushes them. The plugin teaches Claude to use it well, and it sends nothing to Arcus by itself.

## Skills

- `/arcus:setup` — Check that the `arcus` CLI is installed, that you are signed in, and that this repo is bound to an
  Arcus project with the right platforms. Also says whether this machine can run tests. Stops with the one thing to do
  when something is missing.
- `/arcus:author [what to test]` — Write a test (and the elements it needs) as `.sigma` files. Claude learns the
  language from `arcus docs`, writes, runs `arcus check`, fixes, and formats. It does not stop until the check is clean.
- `/arcus:run [test]` — Run one test in a browser on your machine, with `arcus run`. Claude reads the result and the
  screenshot, and tells you whether the test, the app or the setup is wrong. It fixes a test that is wrong, up to three
  rounds, and never weakens a test to make it pass. Nothing is sent to Arcus. No sign-in is needed.
- `/arcus:push [files]` — Send tests and elements to Arcus. Always starts with `arcus push --dry-run` and shows you the
  plan. Says which Arcus project and folder it goes to. Pushes only after you say yes, then says where it went and explains every result.
- `/arcus:verify [story]` — After a change to a user-facing flow: finds the story's test cases in Arcus, automates them,
  runs them against your local app until they pass, writes one "Ran locally" comment for the PR, and pushes the tests as
  pending cases on the story. It never changes what an approved case expects, and never accepts.
- `/arcus:pr-check` — Once a PR's build is deployed (in CI, from a "/arcus test" PR comment): runs the story's tests on
  the PR's build and on the base build, then writes scenarios to try to break the change. Only what fails on the PR and
  passes on the base counts. Arcus judges each against the story and writes one check and one PR comment. A story case
  that breaks blocks the merge; the rest is advisory.

## Typical flow

1. `/arcus:setup` once per repo. Sign in yourself when it asks (`arcus auth login --region us|in|eu`).
2. `/arcus:author login flow` — Claude writes the files and checks them.
3. `/arcus:run` — Claude runs the test in a browser and tells you what happened. Say `write a test and run it` to do
   steps 2 and 3 together.
4. Look at the files, and at `git diff`.
5. `/arcus:push` — read the plan, say yes, and commit `arcus.lock` with the tests.

For a change on a story, `/arcus:verify` does steps 2 to 5 for the story's cases. Accept them into Arcus after the PR
merges.

## This version

- A run is local and runs one web test at a time, in a browser from the Testsigma agent. Start the agent first. It cannot
  run Android or iOS tests, datasets or groups yet, and there is no suite run. A local pass is not an Arcus run.
- `/arcus:run` needs `arcus` CLI 0.1.1 or newer. `/arcus:push` names the Arcus project and folder it sent to, and links each test, from 0.1.3.
  The other skills work on older ones.
- There is no `pull`. Arcus is the source of truth. If Arcus has newer edits to a test, the push says so and you bring
  the file to Arcus's text by hand.
- Not supported yet (the CLI refuses them): `api` steps, groups, `host` lines, and sub-folders under `tests/`.

## Files

- `arcus.json` — which Arcus projects this repo holds, their platforms, and where their folders are. Written by
  `arcus init`.
- `arcus.lock` — which file is which Arcus test or element. Commit it.
- `.arcus/` — local state. Not committed.
- `<folder>/<project>/tests/` and `elements/` — the documents.

## Troubleshooting

- `arcus: command not found` — `npm i -g @testsigma/arcus-cli` (needs Node 22 or newer), then `/arcus:setup`.
- `Not signed in` or exit code `2` — run `arcus auth login` yourself, then try again.
- `Which project?` — the repo holds several projects. Say which one, or run from inside its folder.
- A push is refused or in conflict — the plan says which file and why. Run `arcus docs --topic gotchas` for the common
  mistakes.
- Automation is turned off — a project admin must turn it on in Arcus.
- `Cannot reach the Testsigma agent` — start the Testsigma agent. Only `/arcus:run` needs it.
- `device runs are not supported yet` — the project has no `web` platform, and a run tests web only.
