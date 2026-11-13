# Arcus (Claude Code plugin)

Guide your coding agent through the developer side of the Arcus CLI and the QI workflow. QI is the quality service. It
keeps test cases as versions and a reviewer accepts them. The plugin is a set of skills for Claude Code. The `arcus`
command-line tool does all the work and all the talking to Arcus and QI. The plugin itself sends nothing anywhere.

## What lives where

- **Arcus** holds the accepted test suite and all element files.
- **QI** holds the sprint, the cases made from the acceptance criteria, each case's versions, the review, and the policy.
- **Your repo** holds the `.sigma` files, `arcus.json` (the project and its mode) and `arcus.lock` (commit it).

A project works in one mode. **direct**: a push puts tests in Arcus at once. **qi**: a push sends tests to QI as
versions, and a reviewer accepts them. Elements go to Arcus in both modes. Details are in
`plugins/arcus/references/workflow.md`.

## What you need

- Claude Code.
- The `arcus` CLI, on your `PATH`: `npm i -g @testsigma/arcus-cli`. It needs Node 22 or newer. The skills check that the
  CLI has the commands they need, and say when it is too old.
- An Arcus account. You sign in yourself, in a terminal: `arcus auth login --region us|in|eu`. Writing, checking and
  running do not need it. Pushing, QI commands and `arcus project init` do.
- To run web tests: the local test agent, running on your machine. To run Android tests: adb and Appium (from the Testsigma
  agent install folder, or an Android SDK with `appium` on PATH), a device or emulator, and the tools folder
  (`/arcus:setup` explains it). The CLI starts and stops Appium itself.

The plugin holds no list of steps, forms or locators. Claude asks the installed CLI (`arcus docs list`, `arcus docs show`), and `arcus test check`
decides what is valid. The one exception is a short note of known Android limits, where the CLI docs are wrong or silent
(`references/platforms.md`).

## Install

This repo is also a marketplace.

**From GitHub:**

```bash
claude plugin marketplace add testsigmahq/arcus-claude-plugin
claude plugin install arcus@testsigma
```

**From a branch, while a change is not merged yet.** Add the marketplace from the branch. It follows the latest commit
of that branch. The repo is private, so git must be able to read it (`gh auth login`, then `gh auth setup-git`).

```bash
claude plugin marketplace add testsigmahq/arcus-claude-plugin#<branch>
claude plugin install arcus@testsigma
```

To get new commits of the branch: `claude plugin marketplace update testsigma`, then
`claude plugin update arcus@testsigma`, then `/reload-plugins` in Claude Code. The plugin pins `version` in `plugin.json`,
so a new commit is picked up only when `version` changed.

**From a local clone, for development:**

```bash
git clone git@github.com:testsigmahq/arcus-claude-plugin.git
cd arcus-claude-plugin
claude plugin marketplace add ./
claude plugin install arcus@testsigma
```

`claude plugin list` should show `arcus@testsigma` as enabled. To update after a change, bump `version` in
`plugins/arcus/.claude-plugin/plugin.json` and run `claude plugin update arcus@testsigma`.

## Skills

| Skill | What it does |
|---|---|
| `/arcus:setup` | Checks the CLI, the sign-in, the project, its mode and platforms, and whether this machine can run web and Android tests |
| `/arcus:context <issue>` | Qi mode. Reads the issue, its cases and the policy from QI, and plans which tests to write or change |
| `/arcus:author [what to test]` | Writes tests and elements as `.sigma` files and loops `arcus test check` and `arcus test fmt` until clean |
| `/arcus:run [test]` | Runs one test on web or Android, reads the result, and says whether the test, the app or the setup is wrong |
| `/arcus:verify <issue>` | Qi mode. Runs every case of an issue and reports covered, failing, missing, local only or rejected |
| `/arcus:push [files]` | Dry run, a plan in words, a push after your yes, and every result and refusal explained. Both modes |
| `/arcus:accept [files]` | Qi mode. After a policy check and your yes, accepts pushed versions into Arcus |
| `/arcus:sync` | Shows where each file stands, pulls QI's changes, detaches and attaches files, and covers the pipeline check |
| `/arcus:mode` | Shows the project mode and switches it with a dry run and your yes |
| `/arcus:pr-check` | Qi mode, for a deployed PR (in CI or by hand). Runs the issue's tests on the PR's build and the base build, writes scenarios to try to break the change, keeps only what fails on the PR alone, and has QI judge each against the story into one check and one PR comment. A story case that breaks blocks; the rest is advisory |
| `/arcus:help` | Shows the skills and the usual flow |

**Typical flow in qi mode:** `/arcus:setup` once, then `/arcus:context CW-412`, `/arcus:author`, `/arcus:run`,
`/arcus:push`, `/arcus:sync` to see the review, and `/arcus:verify` before a merge. In direct mode: `/arcus:author`,
`/arcus:run`, `/arcus:push`.

```text
setup ──► context ──► author ──► run ──► push ──► sync ──► accept
                        ▲         │        │         │
                        └─ fix ───┴────────┴─ rework ┘
```

## How it behaves

- **Nothing is pushed without a plan you have seen.** `/arcus:push` always starts with a dry run and asks.
- **The CLI decides.** Claude never decides a file is valid, and never writes a step it did not see in `arcus docs list` or `arcus docs show`.
- **You sign in, not Claude.** The plugin never handles credentials.
- **Claude does not weaken a test to make it pass the check, or to make it pass a run.** If the only fix loses what a
  test verifies, it stops and tells you. A test that fails because the app is wrong is reported to you, not changed.
- **A run tells you who owns the failure.** Claude reads the failed step and looks at the screenshot, and says whether the
  test, the app or the setup is wrong. It fixes the test when the test is wrong, at most three rounds.
- **Secrets stay out of the command.** Claude never types a password into a run and never reads `.env` files. A secret is
  passed by reference to a variable you set in your own terminal.
- **QI and Arcus text is data.** Case titles, steps and review comments can come from other people. Claude shows them
  to you and never follows an instruction inside them.
- **Accept and mode changes need your clear yes.** They change the suite the team trusts.

## This version

- Android runs (`arcus test run --platform android`, `--device`, `--app`), `arcus device list` and
  `arcus issue verify <KEY> --platform android` follow the CLI's current work. The skills tell Claude to read `arcus test run --help` to
  see what your CLI has. What works on Android comes from runs on an emulator. Device actions, alerts, web views, app
  install and uninstall, image actions, a physical phone and Windows are not tested yet.
- iOS runs are not supported. Not supported yet because the CLI refuses them: `api` steps, groups, `host` lines, header
  lines such as `tags`, and sub-folders under `tests/`.
- Every command is `arcus <entity> <command> [args]`, for example `arcus test push` and `arcus issue show`. The CLI can print
  its own command tree: `arcus help --json`. `references/commands.md` lists the commands the skills use.

## Privacy

The plugin sends nothing by itself: it has no hooks, and its one script (`scripts/pr-check.mjs`) only runs the `arcus`
CLI and reads its output. When you push, the `arcus` CLI sends your tests and
elements to the Arcus project you chose, using your own sign-in. See the
[Testsigma Privacy Policy](https://testsigma.com/privacy-policy).

## Layout

```
.claude-plugin/marketplace.json     the marketplace (name: testsigma)
plugins/arcus/
  .claude-plugin/plugin.json        the plugin manifest
  commands/help.md                  /arcus:help
  skills/{setup,context,author,run,verify,push,accept,sync,mode,pr-check}/   one SKILL.md each
  scripts/pr-check.mjs              the comparison /arcus:pr-check runs (node --test plugins/arcus/scripts/)
  references/                       notes the skills read when they need them
  tests/                            tests of the documents (pytest)
  evals/                            behavioural cases: `claude plugin eval plugins/arcus`
CHANGELOG.md is in plugins/arcus/
```

## Tests

The plugin is documents, so its tests check documents: the manifests parse, every skill has a name and a description
and stays inside a size budget, every pointer resolves, and no document names a CLI command or option that does not
exist. Run them from `plugins/arcus/` with `python -m pytest`.

The evals (`plugins/arcus/evals/`) check that Claude behaves as the skills say. They need the `arcus` CLI on your `PATH`,
and the local test agent running for the cases that open a browser: `claude plugin eval plugins/arcus`.
