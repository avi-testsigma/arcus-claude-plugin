---
name: push
description: Use when a developer wants to send Arcus tests and elements from the repo to their Arcus project, or asks what a push would do. Always runs arcus push --dry-run first, shows the plan in plain words, and pushes only after the user says yes. Then explains every result (created, updated, refused, conflict, missing, failed) and what to do next. Does not write tests and does not run them.
---

# Push: send tests and elements to Arcus

A push changes the project in Arcus, where the team sees it. So this skill never pushes first. It shows what a push would
do, waits for a yes, pushes, and then explains what happened. The `arcus` CLI does the work and makes every decision
about what can be sent. You read its answers and put them in words.

If an `arcus` command fails with exit `2` (not signed in, or the sign-in expired) or because the repo has no project,
stop and run the `setup` skill (`/arcus:setup`). Never sign the user in yourself.

## 1. What to send

Read `arcus.json` for the project. With several projects, ask which one, unless the user's files make it plain, and pass
`--project <folder name>` to every command below.

Decide the paths:

- The user named files or a folder: use those.
- The user just authored or changed files in this session: use those.
- Otherwise the whole project (no path). Files that did not change come back `unchanged`, which is harmless.

Pass element files and test files together if both changed. The CLI sends elements first by itself.

## 2. Dry run, always

```
arcus push --dry-run --json [paths] --project <name>
```

Nothing is sent or written. It does read Arcus, so it needs the sign-in. It applies the same checks, the same title
check, and the same conflict logic as a real push, so what it reports is what a push will do. The exit code is `1` when
any file is `refused`, `conflict` or `failed`.

The JSON has `destination`, `files[]` and a `summary`. `destination` says where the files go: `project` and `folder`
(each an `id` and a `name`, the name `null` when Arcus would not give it), `region` and `arcusUrl`, the web address of
Arcus. **Read it first.** A CLI older than 0.1.2 has no `destination` (and no `url` before 0.1.3): then run `arcus project list --json`, take the
name of the project whose id is `projectId` in `arcus.json`, and say the folder is unknown. **Do not read `summary`:** it counts only the offline check findings. Read each
file's `result`. Each file has `path`, `result`, a `message` when there is a reason, `diagnostics`, and for a test a
`plan` (what happens to each step: `keep`, `edit`, `new`, `remove`, `move`). An element that changes has `locators`,
the old list and the new. The step ids in a plan are placeholders: the real push makes its own.

## 3. Show the plan, in words

Begin with the place, in one line, before any file: `This goes to the Arcus project "<project>", in the folder
"<folder>", at <arcusUrl>.` The user may have several Arcus projects, and cannot tell from a file path which one the
repo is bound to. A name that is `null`: give the id and say Arcus did not give the name.

Then one short table or list, one line per file. Say what Arcus will get:

| Result | Say |
|---|---|
| `created` | A new test "<title>" (or a new element `@<path>`) will be made in Arcus, with N steps |
| `updated` | "<title>" changes: N steps edited, N added, N removed, N moved. Steps that someone changed in Arcus (`fromArcus`) will be merged into the file |
| `renamed` | The test "<old>" will be called "<new>" in Arcus. Everyone sees that |
| `unchanged` | Nothing to send. If it says `remote is ahead`, Arcus has newer edits that the file does not have |
| `refused` | Not sent, and why (the `message` and `diagnostics`) |
| `conflict` | Not sent: the same step was changed in Arcus and in the file. Show Arcus's text of that step |
| `missing` | The file is gone and is skipped. Arcus keeps its copy |

Call out what the user may not expect:

- how many **new** tests will be created;
- any **rename**;
- a changed **element**, with how many tests use it (search the project's `tests/` for `@<path>`): its whole locator
  list is replaced in Arcus, for all of them;
- **`fromArcus`** merges: the file will change on disk to include other people's edits.

## 4. Ask

If a test in this push was never run here, say it once next to the plan, and offer `/arcus:run` first (a web project
only: a run cannot test Android or iOS yet). Do not ask twice, and do not hold the push back for it. The user decides.

Ask for an explicit yes to push exactly this, to that project. A past yes does not carry over: each push gets its own.

If some files are `refused` or in `conflict`, do not push yet unless the user asks you to. Say which files and why, and
offer to fix them. If the user wants the clean files sent now, push with their paths only. If a refusal comes from a
check finding in a file you can edit, fix it with `/arcus:author`, then start again from the dry run.

## 5. Push

```
arcus push --json [paths] --project <name>
```

Compare the results with the plan. They should match. Report any difference. Then say where it went and how to find it,
then report each file in the same words as before, in the past tense:

- The place: `Pushed to the Arcus project "<project>", folder "<folder>".` Never say only "pushed". Take the place from
  `destination` of this push, not from memory.
- How to find it: give the `url` of each pushed test, as a link the user can open. It opens the test in Arcus. A CLI
  older than 0.1.3 gives no `url`, and so does a test that failed to push or whose id Arcus would not give: then say
  to open <arcusUrl>, then the project, then the folder, and look for the test by its title. A **new** test is in the
  folder shown. A test that was only **updated** stays where it already was in Arcus, which may be another folder. Say
  so, and do not claim a folder for it.
- Never build a link yourself. Use a `url` the CLI gave, or none.

A push that stops half way is safe to run again. It continues and does not make duplicates.

## 6. After the push

- **Server lines.** After a test is written, Arcus's own compiler looks at it. Problems come in `serverProblems`
  (`code`, `severity`, `line`, `message`, `platform`). They never undo the push: the test is saved. Read them to the
  user. Offer to fix them (`/arcus:author`) and push again. `serverWarning` means the check could not run, or Arcus
  changed the test after the push. A missing `serverProblems` means Arcus found nothing.
- **The files changed.** The CLI rewrote each pushed file to the text Arcus holds: canonical layout, no step keys, and
  merged edits from others. Tell the user to look at `git diff` before committing.
- **`arcus.lock` changed.** New tests add a row. Tell the user to commit it with the tests: the lock is how a teammate
  works on the same Arcus tests and not on copies. Do not commit for them unless they ask.
- **Pushed from `/arcus:verify`.** The tests are pending cases on the story. Say that the developer accepts them after
  the PR merges, and do not offer `--accept` now.
- **Run status.** Say what you know. If a test was run in this session and passed, say so. If it was run and failed, say
  that it was pushed anyway. If it was never run here, say that a clean check and a push do not prove it passes against
  the app, and offer `/arcus:run`. A run is not a condition for a push.

## What to say for each failure

| What you see | What to tell the user |
|---|---|
| `refused` with a `diagnostics` list | The offline check failed. Fix the findings. `/arcus:author` can do it |
| `refused: A test named "…" already exists` | Another test in Arcus has that title. Pick another title |
| `refused: "<path>" exists in Arcus and this folder does not track it` | That element path is taken in Arcus. Use another path |
| `refused: it uses @<path>, which is not pushed` or `which failed to push in this run` | Push the element first, or fix why it failed |
| `refused: … Arcus has newer edits … adds or moves entries` | Someone changed this test in Arcus. There is no `pull`: make the file match Arcus, then push again |
| `refused: This clone has no base …` | A fresh clone with a file that differs from Arcus. The CLI cannot tell which side changed. There is no `pull`: make the file match Arcus, then push |
| `refused: probably moved from …` | The file was moved or renamed. Move it back. Moving is not supported yet |
| `conflict` | The same step changed on both sides. Two ways out: undo the local edit to that step; or make the file equal Arcus's text, delete the file's base in `.arcus/base/` (same path as the file, `.json` added, at the repo root), and push. Do nothing until the user chooses, and delete the base only if they say to |
| `failed` | An unexpected error; the message is Arcus's. Report it as it is. A network failure also appears here. Running the push again is safe |
| `missing` | A tracked file is not in the folder. Put it back, or leave it: nothing is sent and Arcus keeps the test |

Errors that stop the whole run:

- exit `2`: sign-in expired or Arcus did not accept it, or the project's region differs from the signed-in region. Run
  `/arcus:setup`.
- exit `3`, **automation is turned off** for the Arcus project: a project admin must turn it on. Never try to change
  project settings.
- exit `3`, **Arcus runs another toolchain version**: the message says which side is behind. Tell the user to update the
  CLI (`npm i -g @testsigma/arcus-cli`) or to install the release that matches Arcus.
- exit `3`, **an `arcus.lock` from an older layout**: the message names the fix.

## What this skill never does

- Push without a dry run and a yes from the user for this push.
- Read the `summary` as the outcome. Read each file's `result`.
- Work around a refusal or a conflict by editing `arcus.lock` or `.arcus/`, or by renaming files to get past a check.
- Sign in, change Arcus project settings, or delete anything in Arcus.
- Run the tests. It offers `/arcus:run`, and the user decides.
