# Verifying a change: the story, the cases, the comment

The details behind `/arcus:verify`. The skill says the order. This says the shapes.

## Finding the story

An issue key looks like `<PROJECT>-<number>`. Look, in this order, and stop at the first you find:

1. what the user said,
2. the branch name (`git branch --show-current`),
3. the commit messages on the branch (`git log <base>..HEAD --format=%s`),
4. the PR title and body (`gh pr view --json title,body`).

Two different keys: ask which. None: ask. Then find the sprint: `arcus sprint list --json` gives each sprint's
`work_cycle_id`, and `arcus issue list <work_cycle_id> --json` lists its issues. An issue in no active sprint cannot hold
pending cases: say so.

## A case

`arcus test list --json` gives each case's `id`, `title` and `acceptance_status`. `arcus test show <id>
--json` adds what it expects: `preconditions`, then either `individual_steps` (one entry per step: `order`,
`step_description`, `expected_results`, and for a step group its title and its own steps) or, for a free-text case,
`steps` and `expected_results` as written. Follow `individual_steps` when there are any.

`acceptance_status`:

| `acceptance_status` | Means | Its expected results |
|---|---|---|
| `ACCEPTED` | approved: someone accepted it into Arcus | the bar. Changing one is an intent change |
| `PENDING` | generated or pushed, not yet reviewed | still the bar. A step that looks wrong is proposed, not edited |
| `REJECTED` | turned down in QI | not a case to automate. Skip it and name it |

`human_id` is set once a case is an Arcus test (`TC-12`). Use it in the comment when there is one.

## Intent changes

A test that fails because the app now does, on purpose, what a case says it should not, is not fixed in the test. The
change may be right. The case owner decides. List each one:

| Case | Status | Step | The case expects | The app now does | Why the change looks intended |
|---|---|---|---|---|---|

"Why" cites the diff or the story: a line, a commit message, the story's text. If nothing says it was intended, it is not
an intent change. It is a finding: the code is wrong, so fix the code.

## The comment

The first line is the marker, so a re-run finds the comment and edits it:

```markdown
<!-- arcus:ran-locally -->
### Ran locally: <story key> <story title>

The developer's own run, on their machine. Not an Arcus run and not this PR's check.
Commit `<short sha>` · <browser> <version> · <date and time>

| Case | Kind | Result | Steps | Time |
|---|---|---|---|---|
| TC-12 Sign in with SSO | automated | passed | 6/6 | 14 s |
| Reset a forgotten password | new | failed at step 4: <message> | 3/7 | 9 s |

**Proposed intent changes** (waiting for QA or the PM in QI)
<the intent-change table, or "None.">

**Not run**
<each case or test that did not run, and why, or "Nothing.">

**Tests changed after their first run**
<file: what changed and why, or "None.">

Tests pushed to QI as pending cases on <story key>. They are accepted after this PR merges.
```

Keep screenshots as paths on this machine (`.arcus/runs/…`). Do not attach them, and do not upload them anywhere.

## Posting and editing

Find the PR: `gh pr view --json number,url`. Find an earlier comment by its marker:

```
gh api repos/{owner}/{repo}/issues/<number>/comments --jq '.[] | select(.body | startswith("<!-- arcus:ran-locally -->")) | .id'
```

- None, and the user said yes: `gh pr comment <number> --body-file <file>`.
- One: edit it, `gh api -X PATCH repos/{owner}/{repo}/issues/comments/<id> -F body=@<file>`.
- Write the body to a file under `.arcus/`, never into the command line.
- No PR, or `gh` is not signed in: print the comment and say where to paste it.
