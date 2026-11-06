# Arcus (Claude Code plugin)

Write Arcus tests in your repo with Claude, check them offline, run them in a browser on your machine, and push them to
an Arcus project. The plugin is a set of skills for Claude Code. The `arcus` command-line tool does all the work and all
the talking to Arcus. The plugin itself sends nothing anywhere.

## What you need

- Claude Code.
- The `arcus` CLI, on your `PATH`: `npm i -g @testsigma/arcus-cli`. It needs Node 22 or newer. `/arcus:run` needs CLI
  0.1.1 or newer. `/arcus:push` names the Arcus project and folder, and links each test, from CLI 0.1.3.
  `/arcus:verify` needs the CLI's sprint, issue and QI push commands (`arcus sprint --help` works).
- An Arcus account. You sign in yourself, in a terminal: `arcus auth login --region us|in|eu`. Only `push` and `init`
  need it. Writing, checking and running do not.
- To run tests: the Testsigma agent, running on your machine. It gives the CLI the browsers.

The plugin holds no list of steps, forms or locators. Claude asks the installed CLI (`arcus docs`) what the language
can say, and `arcus check` decides what is valid. So what you can write is whatever your CLI version accepts.

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
| `/arcus:setup` | Checks the CLI is installed, you are signed in, and the repo is bound to a project with the right platforms. Stops with the exact next step |
| `/arcus:author [what to test]` | Writes tests and elements as `.sigma` files, learns the language from `arcus docs`, and loops `arcus check` and `arcus fmt` until clean |
| `/arcus:run [test]` | Runs one test in a browser on your machine, reads the result and the screenshot, and says whether the test, the app or the setup is wrong. Nothing is sent to Arcus |
| `/arcus:push [files]` | Runs `arcus push --dry-run`, shows the plan in words, pushes after your yes, and explains every result |
| `/arcus:verify [story]` | For a change to a user-facing flow: automates the story's test cases from Arcus, runs them against your local app until they pass, writes one "Ran locally" PR comment, and pushes the tests as pending cases on the story. Never edits what an approved case expects, and never accepts |
| `/arcus:pr-check` | For a deployed PR, in CI or by hand: runs the story's tests on the PR's build and the base build, writes new scenarios to try to break the change, keeps only what fails on the PR alone, and has Arcus judge each against the story into one check and one PR comment. A story case that breaks blocks; the rest is advisory |
| `/arcus:help` | Shows the commands and the usual flow |

**Typical flow:** `/arcus:setup` once per repo, then `/arcus:author <what to test>`, then `/arcus:run`, look at the
files, then `/arcus:push`. Each skill ends by naming the next one. Say `write a test and run it` and Claude goes from
`author` to `run` without asking again.

```text
setup ──► author ──► run ──► push
            ▲         │
            └─ fix ───┘
```

`/arcus:verify` runs the same steps for the cases of one story, ending in a PR comment and a pending push. The developer
accepts the cases into Arcus after the PR merges. Once the PR's build is deployed, `/arcus:pr-check` tests it against
the base build and tries to break it.

## How it behaves

- **Nothing is pushed without a plan you have seen.** `/arcus:push` always starts with a dry run and asks.
- **The CLI decides.** Claude never decides a file is valid, and never writes a step it did not see in `arcus docs`.
- **You sign in, not Claude.** The plugin never handles credentials.
- **Claude does not weaken a test to make it pass the check, or to make it pass a run.** If the only fix loses what a
  test verifies, it stops and tells you. A test that fails because the app is wrong is reported to you, not changed.
- **A run tells you who owns the failure.** Claude reads the failed step and looks at the screenshot, and says whether the
  test, the app or the setup is wrong. It fixes the test when the test is wrong, at most three rounds.
- **Secrets stay out of the command.** Claude never types a password into a run and never reads `.env` files. A secret is
  passed by reference to a variable you set in your own terminal.
- **A story's cases are the bar.** `/arcus:verify` automates what Arcus says must pass, and changes no case to match the
  app. A failure that looks like an intended change is listed for QA or the PM to decide.
- **Arcus is the source of truth.** There is no `pull` yet. When Arcus and your file disagree, the push says so, and
  Claude tells you, and does not work around it.

## This version

- A run is local, one web test at a time, in a browser from the Testsigma agent. It cannot run Android or iOS tests,
  datasets or groups yet, and there is no suite run. A local pass is not an Arcus run.
- Not supported yet, because the CLI refuses them: `api` steps, groups, `host` lines, header lines such as `tags`,
  and sub-folders under `tests/`.
- Session capture, from earlier versions of this plugin, is gone. Stories come back through the CLI's sprint and issue
  commands, for `/arcus:verify`.

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
  skills/{setup,author,run,push,verify,pr-check}/ one SKILL.md each
  scripts/pr-check.mjs              the comparison /arcus:pr-check runs (node --test scripts/)
  references/                       notes the skills read when they need them
  tests/                            tests of the documents (pytest)
  evals/                            behavioural cases: `claude plugin eval plugins/arcus`
notes/                              design notes
```

## Tests

The plugin is documents, so its tests check documents: the manifests parse, every skill has a name and a description
and stays inside a size budget, every pointer resolves, and no document names a CLI command or option that does not
exist. Run them from `plugins/arcus/` with `python -m pytest`.

The evals (`plugins/arcus/evals/`) check that Claude behaves as the skills say. They need the `arcus` CLI on your `PATH`,
and the Testsigma agent running for the cases that open a browser: `claude plugin eval plugins/arcus`.
