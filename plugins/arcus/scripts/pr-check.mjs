#!/usr/bin/env node
// The deterministic half of /arcus:pr-check: which tests are the story's, running them on each build, and
// keeping only what fails on the PR's build, passes on the base build, and fails again on a retry.
// Node 22+, no dependencies. Every command writes JSON to stdout.

import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const USAGE = `usage:
  pr-check.mjs story-tests --context <context.json> [--lock arcus.lock]
  pr-check.mjs run --url <url> [--project <name>] [--var name=value ...] <paths...>
  pr-check.mjs diff --lane regression|break --pr <run.json> --base <run.json> [--retry <run.json>] [--lock arcus.lock]
  pr-check.mjs request --context <context.json> --pr-url <url> --base-url <url> --repo <owner/name>
                       [--pr <number>] [--sha <sha>] [--guessed] [--diff <diff.json> ...] [--stats <stats.json>] [--no-images]`;

function parse(argv) {
  const opts = { _: [], var: [], diff: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith("--")) {
      opts._.push(a);
      continue;
    }
    const key = a.slice(2);
    if (key === "guessed" || key === "no-images") {
      opts[key] = true;
      continue;
    }
    const value = argv[++i];
    if (value === undefined) fail(`--${key} needs a value`);
    if (Array.isArray(opts[key])) opts[key].push(value);
    else opts[key] = value;
  }
  return opts;
}

function fail(message) {
  process.stderr.write(`${message}\n${USAGE}\n`);
  process.exit(2);
}

const readJson = (file) => JSON.parse(fs.readFileSync(file, "utf8"));

export function readLock(file) {
  if (!file || !fs.existsSync(file)) return [];
  return fs
    .readFileSync(file, "utf8")
    .split("\n")
    .filter((line) => line.trim())
    .map((line) => JSON.parse(line));
}

/** The test files that automate one of the story's cases, by the case id the lock records for each. */
export function storyTests(context, lock) {
  const caseIds = new Set((context.cases ?? []).map((c) => c.id));
  return lock
    .filter((e) => e.path?.includes("/tests/") && e.qiId && caseIds.has(e.qiId))
    .map((e) => ({ path: e.path, case_id: e.qiId }));
}

/** One `arcus run --json` answer, single test or suite, as a list of test runs. */
export function testsOf(runJson) {
  if (runJson.suite) return runJson.suite.tests;
  if (runJson.run) return [runJson];
  return [];
}

function outcome(test) {
  if (!test) return null;
  const { run } = test;
  const failed = run.failedStep;
  return {
    status: run.status,
    failed_step: failed?.description ?? run.interruptedAt ?? "",
    message: failed?.message ?? run.problem ?? "",
    screenshot: !failed?.screenshot
      ? ""
      : path.isAbsolute(failed.screenshot) || !run.artifactsDir
        ? failed.screenshot
        : path.join(run.artifactsDir, failed.screenshot),
  };
}

const failureOf = (test) => [test.run.failedStep?.description ?? "", test.run.failedStep?.message ?? test.run.problem ?? ""];

function sameFailure(a, b) {
  const [stepA, messageA] = failureOf(a);
  const [stepB, messageB] = failureOf(b);
  return stepA === stepB && messageA === messageB;
}

const byPath = (runJson) => new Map(testsOf(runJson).map((t) => [t.run.path, t]));

/**
 * Splits the tests into what goes to the judge and what does not.
 * A difference fails on the PR and fails again on the retry, while the base passes or fails in another way (another
 * step, or another message). A test that passes on the retry is flaky; one that fails the same way on the base was
 * already broken. Neither is this PR's.
 */
export function diff({ lane, pr, base, retry, caseIds = new Map(), readSteps = (p) => fs.readFileSync(p, "utf8") }) {
  const prs = byPath(pr);
  const bases = byPath(base);
  const retries = retry ? byPath(retry) : new Map();
  const out = { lane, differences: [], passed: [], not_counted: [] };
  for (const [p, t] of prs) {
    const b = bases.get(p);
    const title = t.run.title || path.basename(p, ".sigma");
    if (t.run.status === "passed") {
      if (b?.run.status === "passed") out.passed.push(title);
      else out.not_counted.push(`${title}: passed on this PR, ${b ? `${b.run.status} on the base` : "not run on the base"}`);
      continue;
    }
    if (t.run.status === "refused") {
      out.not_counted.push(`${title}: did not compile, so it did not run`);
      continue;
    }
    if (!b) {
      out.not_counted.push(`${title}: not run on the base`);
      continue;
    }
    if (b.run.status !== "passed" && sameFailure(t, b)) {
      out.not_counted.push(`${title}: fails the same way on the base, so not this PR's`);
      continue;
    }
    const r = retries.get(p);
    if (r?.run.status === "passed") {
      out.not_counted.push(`${title}: flaky, passed when re-run on this PR`);
      continue;
    }
    out.differences.push({
      lane,
      title,
      steps: readSteps(p),
      case_id: caseIds.get(p) ?? "",
      pr: outcome(t),
      base: outcome(b),
      pr_retry: outcome(r),
    });
  }
  return out;
}

const MAX_SCREENSHOT_BYTES = 2 * 1024 * 1024;

/** Each side's failing-step screenshot, inlined so the judge can look at what a user saw. */
export function withScreenshots(difference) {
  const out = { ...difference };
  for (const side of ["pr", "base", "pr_retry"]) {
    const o = difference[side];
    if (!o?.screenshot || !fs.existsSync(o.screenshot) || fs.statSync(o.screenshot).size > MAX_SCREENSHOT_BYTES) continue;
    out[side] = { ...o, screenshot_b64: fs.readFileSync(o.screenshot).toString("base64") };
  }
  return out;
}

/** The body of `arcus pr-check report`. */
export function request({ context, prUrl, baseUrl, repo, pr, sha, guessed, diffs, stats, images = true }) {
  return {
    repo,
    pr_number: pr ? Number(pr) : null,
    head_sha: sha ?? "",
    pr_url_tested: prUrl,
    base_url_tested: baseUrl,
    story: context.story ?? null,
    story_guessed: Boolean(guessed),
    cases: context.cases ?? [],
    regression_passed: diffs.filter((d) => d.lane === "regression").flatMap((d) => d.passed),
    differences: diffs.flatMap((d) => d.differences).map((d) => (images ? withScreenshots(d) : d)),
    not_run: diffs.flatMap((d) => d.not_counted),
    stats: stats ?? {},
  };
}

function runArcus(paths, opts) {
  const args = ["run", ...paths, "--json", "--screenshots", "failed", "--base-url", opts.url];
  if (opts.project) args.push("--project", opts.project);
  for (const v of opts.var) args.push("--var", v);
  try {
    return execFileSync("arcus", args, { encoding: "utf8", maxBuffer: 64 * 1024 * 1024, stdio: ["ignore", "pipe", "inherit"] });
  } catch (e) {
    // A failed test exits 1 with its result on stdout; only an empty stdout is a setup error.
    if (e.stdout) return e.stdout;
    throw e;
  }
}

function main(argv) {
  const [command, ...rest] = argv;
  const opts = parse(rest);
  const lockFile = opts.lock ?? "arcus.lock";
  switch (command) {
    case "story-tests":
      if (!opts.context) fail("story-tests needs --context");
      return storyTests(readJson(opts.context), readLock(lockFile));
    case "run":
      if (!opts.url || opts._.length === 0) fail("run needs --url and at least one path");
      return JSON.parse(runArcus(opts._, opts));
    case "diff": {
      if (!["regression", "break"].includes(opts.lane) || !opts.pr || !opts.base) fail("diff needs --lane, --pr and --base");
      const caseIds = new Map(readLock(lockFile).filter((e) => e.qiId).map((e) => [e.path, e.qiId]));
      return diff({
        lane: opts.lane,
        pr: readJson(opts.pr),
        base: readJson(opts.base),
        retry: opts.retry ? readJson(opts.retry) : null,
        caseIds: opts.lane === "regression" ? caseIds : new Map(),
      });
    }
    case "request":
      if (!opts.context || !opts["pr-url"] || !opts["base-url"] || !opts.repo) {
        fail("request needs --context, --pr-url, --base-url and --repo");
      }
      return request({
        context: readJson(opts.context),
        prUrl: opts["pr-url"],
        baseUrl: opts["base-url"],
        repo: opts.repo,
        pr: opts.pr,
        sha: opts.sha,
        guessed: opts.guessed,
        diffs: opts.diff.map(readJson),
        stats: opts.stats ? readJson(opts.stats) : undefined,
        images: !opts["no-images"],
      });
    default:
      fail(command ? `unknown command ${command}` : "no command");
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  process.stdout.write(`${JSON.stringify(main(process.argv.slice(2)), null, 2)}\n`);
}
