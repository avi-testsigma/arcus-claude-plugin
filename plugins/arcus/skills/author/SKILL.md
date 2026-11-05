---
name: author
description: Use when a developer asks to write, add or generate end-to-end tests for their app in Arcus, or to change an existing Arcus test file. Writes the test as a .sigma file in the repo's Arcus project folder, learns the language from the arcus CLI instead of from memory, and does not stop until arcus check is clean. Does not push. Running the test in a browser is the run skill's job.
---

# Author: write an Arcus test

You write tests as `.sigma` files and let the `arcus` CLI judge them. The CLI knows what the language can express and
what compiles on the project's platforms. You do not. So you never write a step from memory, and you never decide a
file is valid: `arcus check` decides.

If any `arcus` command below fails because the CLI is missing, the user is not signed in (exit `2`), or the repo has
no project, stop and run the `setup` skill (`/arcus:setup`) first.

This skill writes and checks files. It does not push them (`/arcus:push`) and it does not run them (`/arcus:run`). A
clean check means the CLI accepts a test. Only a run shows that it passes against the app.

## 1. Know where the test goes

Read `arcus.json`, found in the current folder or above. It gives the repo's `arcusDir` and each project's folder name,
`projectId` and `platforms`. Never assume the folder is `tests/arcus`.

- **One project:** use it.
- **Several projects:** ask which one the test is for, unless the folder you are in, or the files the user named, make
  it plain. Remember the answer, and pass `--project <folder name>` to every `arcus` command below. At a repo root with
  several projects, the CLI refuses a command that does not say which.

The project's folder is `<arcusDir>/<folder name>/`. Tests go in its `tests/` folder, and element files in its
`elements/` folder.

Look at the tests and elements that are already there. Match their naming and style. Note their titles: a test title
must be unique in the project, ignoring case.

Then compare the project's `platforms` with what the user wants to test. Platforms belong to the project, and `check`
compiles every test for all of them, so a web-only test cannot live in a project that also lists a mobile platform.
`${CLAUDE_PLUGIN_ROOT}/references/platforms.md` says what to do when they do not match. Settle this before writing.

## 2. Know what to test

The user says what to cover (`/arcus:author login flow`). If they did not, ask. Then find out what the test needs, from
the repo first and from the user only for what the repo cannot tell. How to read the app, where selectors and URLs
live, and what you may ask, is in `${CLAUDE_PLUGIN_ROOT}/references/reading-the-app.md`. In short:

- the screens or pages and the steps a person takes,
- the values the test uses (an email, a search word). Never use a real secret. Ask where a credential should come from.
- what a pass looks like: the thing to verify at the end. A test with no `verify` proves nothing. Include at least one.

One test checks one behaviour. If the user's request covers several behaviours, write several tests, one file each, and
say so.

## 3. Learn the language from the CLI

Do this before the first line. The CLI lists only what compiles on the project's platforms.

```
arcus docs --project <name>                 # every action and form, with an example of each
arcus docs <action> --project <name>        # one action, e.g. click
arcus docs --topic gotchas                  # always read this one: it is short, and it lists the easy mistakes
arcus docs --topic <id>                     # locators, elements, conditions, data, control-flow, word-order
```

Read the actions you will use, and the topic for anything you are unsure of (`locators` before you write a target,
`data` before you store or reuse a value, `conditions` before a `verify`). Copy the shape of the examples. Do not invent
a verb, a form or an option. If the user asks for something `docs` does not show, it does not compile: say that, and
offer the closest form that does.

## 4. Write the file

- **One test per file**, at `<project folder>/tests/<name>.sigma`. `<name>` is the title in lower-case words joined by
  hyphens. No sub-folders: they are not supported yet.
- The file holds one `test "<title>" { … }` and nothing else above it. No header lines (`sigmascript`, `platform`,
  `tags`, …): Arcus cannot store them.
- No step keys (`#· s_…`). Arcus makes them, and the CLI finds steps again by their text.
- Open with the first step the person would do, usually `nav`. End with a `verify`.
- **Targets.** A target that appears more than once, or that is hard to find, or that needs a locator per platform, is
  an element: its own file in `elements/`, used as `@<path>`. A one-off target stays inline (`locate …`). Write the
  element files first. When to make one, how to name it and how to order its locators is in
  `${CLAUDE_PLUGIN_ROOT}/references/elements.md`. Use a locator only if you saw it in the app's source or the user gave
  it. Do not invent one.
- Keep the title short and specific. It is what people see in Arcus.
- If a file for this test already exists, edit it. Do not make a second file with the same title.
- **Is the file already pushed?** Search `arcus.lock` for its path. If it is there, the file is tracked: it exists in
  Arcus. Read `${CLAUDE_PLUGIN_ROOT}/references/editing.md` before changing it. Never rename, move or delete a tracked
  file, and do not rename its title unless the user asks.

## 5. Check, fix, repeat

```
arcus check <files> --project <name> --json
```

Pass the test files and the element files you wrote or changed.

`files[].diagnostics[]` has, for each finding: `code`, `severity`, `line`, `message`, `platform` (for compile
findings), and `fixes`. `summary` counts the errors and warnings. The exit code is `1` when there is an error.

For each **error**, in this order of preference:

1. **A fix with `certainty: "certain"`.** Apply it as written. A fix replaces the lines from `from` to `to` (1-based,
   inclusive) with `text`. Give every line of `text` the indent of the first line it replaces. When there are several
   fixes in one file, apply them from the bottom of the file up, so the line numbers stay right.
2. **A fix with `certainty: "suggested"`.** Show it to the user and ask before applying.
3. **No fix.** Read the message. Then run `arcus docs <action>` for the action on that line and rewrite the step into a
   form that is listed there.

For each **warning**, read it. Fix it when it points at a real problem. A step with an empty value (`nav ""`) is a
warning plus a blocked step, and `check` refuses it: fill the value.

After each round of fixes, run `check` again. Stop when `summary` is `{errors: 0}` for the file.

**Do not make the check pass by making the test weaker.** Never delete a `verify`, remove a step, or lower what is
checked just to clear a diagnostic. If the only way to make a step compile is to lose what it checks, stop and tell the
user. If you are still failing after five rounds, stop and show the user what is left. Do not loop.

**A step that does not run on a platform** is `ARC2001 … [platform]`. The compile would skip it, and a skipped step
silently does not run. Do not leave it. Rewrite it into a form that `arcus docs --all` marks for that platform, or tell
the user and ask whether to drop that platform for this project or to split the test.

## 6. Format

```
arcus fmt <files> --project <name>
```

This rewrites layout only. If it refuses a file, the message says why (usually a comment at the end of a step line:
move it to its own line). Fix it, and run `check` once more, because the last run was before `fmt`.

## 7. Report

Say, briefly:

- the files written or changed, and what each test covers in a sentence,
- the platforms they were checked for,
- that `arcus check` is clean,
- that the tests were **checked, not run**: a clean check means the CLI accepts the test, not that it passes against
  the app. Targets that were written without seeing the app may need adjusting when the test first runs.

Then hand over. The next step is a run, then a push:

- The user asked to run or verify the test (`write a test and run it`, `check that it works`): hand over to the `run`
  skill now. Do not ask again.
- Otherwise offer `/arcus:run` first, and `/arcus:push` after it. Offer a run only for a project with `web` in its
  platforms. A run cannot test Android or iOS yet.
- The user wants a change on a story proven with the story's own cases: that is `/arcus:verify`, which calls this skill
  for each case.
- The user asks to push now: hand over to the `push` skill. It will say that the test was not run. Do not run
  `arcus push` or `arcus run` from here.

## Say no to what Arcus cannot hold yet

`api` steps, groups, `host` lines, header lines, sub-folders under `tests/`, and any action or form that `arcus docs --all`
does not list. Tell the user it is not supported yet, offer the nearest thing that is, and do not work around it. The
list and the reasons are in `${CLAUDE_PLUGIN_ROOT}/references/platforms.md`.

## What this skill never does

- Write a step it did not see in `arcus docs`, or a locator it did not see in the app or get from the user.
- Edit `arcus.json`, `arcus.lock` or anything in `.arcus/`. The CLI owns them.
- Push, or run anything that changes Arcus. Running a test is the `run` skill's, and it needs the user's ask.
- Put a real credential, token or personal data in a test.
