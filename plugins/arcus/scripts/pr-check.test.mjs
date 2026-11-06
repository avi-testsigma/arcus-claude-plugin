import assert from "node:assert/strict";
import { test } from "node:test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { diff, request, storyTests, testsOf, withScreenshots } from "./pr-check.mjs";

const run = (p, status, failedStep) => ({
  run: {
    path: p,
    title: p.replace(/^.*\//, "").replace(".sigma", ""),
    status,
    durationMs: 10,
    artifactsDir: "/runs/x",
    ...(failedStep && { failedStep: { description: failedStep, message: "not visible", screenshot: "step-3.jpg" } }),
  },
});
const suite = (...tests) => ({ suite: { status: "failed", tests } });
const steps = () => 'nav "{env.base_url}/x"';

test("the story's tests are the files whose case is one of the story's", () => {
  const lock = [
    { path: "g/tests/a.sigma", qiId: "c1" },
    { path: "g/tests/b.sigma", qiId: "other" },
    { path: "g/elements/e.sigma", anchorType: "ELEMENT" },
    { path: "g/tests/new.sigma", state: "draft" },
  ];
  assert.deepEqual(storyTests({ cases: [{ id: "c1" }] }, lock), [{ path: "g/tests/a.sigma", case_id: "c1" }]);
});

test("a single run and a suite read the same", () => {
  assert.equal(testsOf(run("a", "passed")).length, 1);
  assert.equal(testsOf(suite(run("a", "passed"), run("b", "failed"))).length, 2);
});

test("only a failure on the PR that passes on the base and fails again is a difference", () => {
  const out = diff({
    lane: "regression",
    pr: suite(run("t/broke.sigma", "failed", "verify @list"), run("t/ok.sigma", "passed"), run("t/flaky.sigma", "failed", "x"), run("t/old.sigma", "failed", "y")),
    base: suite(run("t/broke.sigma", "passed"), run("t/ok.sigma", "passed"), run("t/flaky.sigma", "passed"), run("t/old.sigma", "failed", "y")),
    retry: suite(run("t/broke.sigma", "failed", "verify @list"), run("t/flaky.sigma", "passed")),
    caseIds: new Map([["t/broke.sigma", "c1"]]),
    readSteps: steps,
  });
  assert.deepEqual(out.differences.map((d) => d.title), ["broke"]);
  const [d] = out.differences;
  assert.equal(d.case_id, "c1");
  assert.equal(d.pr.failed_step, "verify @list");
  assert.equal(d.pr.screenshot, "/runs/x/step-3.jpg");
  assert.equal(d.base.status, "passed");
  assert.equal(d.pr_retry.status, "failed");
  assert.deepEqual(out.passed, ["ok"]);
  assert.deepEqual(out.not_counted, ["flaky: flaky, passed when re-run on this PR", "old: fails the same way on the base, so not this PR's"]);
});

test("a test that fails on both builds, but in another way on the PR, is a difference", () => {
  const prFail = { ...run("t/tabs.sigma", "failed", "verify url ~ tab=connection") };
  const baseFail = run("t/tabs.sigma", "failed", "verify url ~ tab=connection");
  baseFail.run.failedStep.message = "toast check: element not found";
  const out = diff({ lane: "regression", pr: suite(prFail), base: suite(baseFail), retry: suite(prFail), readSteps: steps });
  assert.deepEqual(out.differences.map((d) => d.title), ["tabs"]);
  assert.equal(out.differences[0].base.message, "toast check: element not found");
});

test("an absolute screenshot path is kept as it is", () => {
  const t = run("t/a.sigma", "failed", "x");
  t.run.failedStep.screenshot = "/abs/run/step.jpg";
  const out = diff({ lane: "break", pr: suite(t), base: suite(run("t/a.sigma", "passed")), readSteps: steps });
  assert.equal(out.differences[0].pr.screenshot, "/abs/run/step.jpg");
});

test("a test that did not compile, or never ran on the base, is said, not judged", () => {
  const out = diff({
    lane: "break",
    pr: suite(run("t/bad.sigma", "refused"), run("t/half.sigma", "failed", "x")),
    base: suite(),
    readSteps: steps,
  });
  assert.equal(out.differences.length, 0);
  assert.deepEqual(out.not_counted, ["bad: did not compile, so it did not run", "half: not run on the base"]);
});

test("the request carries the story, the regression passes, every difference and what was not counted", () => {
  const regression = { lane: "regression", differences: [{ lane: "regression", title: "a" }], passed: ["ok"], not_counted: [] };
  const broke = { lane: "break", differences: [{ lane: "break", title: "b" }], passed: ["ignored"], not_counted: ["c: flaky"] };
  const body = request({
    context: { story: { issue_key: "K-1", title: "t" }, cases: [{ id: "c1" }] },
    prUrl: "http://pr",
    baseUrl: "http://base",
    repo: "o/r",
    pr: "12",
    sha: "abc",
    guessed: true,
    diffs: [regression, broke],
  });
  assert.equal(body.pr_number, 12);
  assert.equal(body.story_guessed, true);
  assert.deepEqual(body.regression_passed, ["ok"]);
  assert.deepEqual(body.differences.map((d) => d.title), ["a", "b"]);
  assert.deepEqual(body.not_run, ["c: flaky"]);
});

test("a side's screenshot is inlined for the judge when the file is there", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "pr-check-"));
  const shot = path.join(dir, "step.jpg");
  fs.writeFileSync(shot, "JPEG");
  const d = withScreenshots({ pr: { status: "failed", screenshot: shot }, base: { status: "passed", screenshot: "" }, pr_retry: { status: "failed", screenshot: path.join(dir, "gone.jpg") } });
  assert.equal(d.pr.screenshot_b64, Buffer.from("JPEG").toString("base64"));
  assert.equal(d.base.screenshot_b64, undefined);
  assert.equal(d.pr_retry.screenshot_b64, undefined);
  fs.rmSync(dir, { recursive: true });
});
