const { test } = require("node:test");
const assert = require("node:assert/strict");
const model = require("../../src/athena_procurement_arena/ui_assets/product-model.js");
const item = {
  kind: "import",
  p: {
    project: {
      requirements: [
        { requirement_id: "early", phase: { value: "EARLY_WORKS" } },
        { requirement_id: "commissioning", phase: { value: "COMMISSIONING" } },
      ],
    },
    evaluations: [
      {
        requirement_id: "early",
        qualification: { procurement: "UNCONFIRMED" },
        match: { verdict: "DO_NOT_PURSUE" },
      },
      {
        requirement_id: "commissioning",
        qualification: { procurement: "OPEN" },
        match: { verdict: "RESEARCH_REQUIRED" },
      },
    ],
  },
};
test("all active commercial filters must apply to the same requirement", () => {
  assert.deepEqual(
    model.matchingPhases(item, {
      phaseFilter: "EARLY_WORKS",
      procurement: "OPEN",
      fit: "RESEARCH_REQUIRED",
    }),
    [],
  );
  assert.deepEqual(
    model.matchingPhases(item, {
      phaseFilter: "COMMISSIONING",
      procurement: "OPEN",
      fit: "RESEARCH_REQUIRED",
    }),
    [1],
  );
  assert.deepEqual(
    model.matchingPhases(item, {
      phaseFilter: "all",
      procurement: "OPEN",
      fit: "all",
    }),
    [1],
  );
});
test("missing, stale and invalid phase links normalize to the first requirement", () => {
  for (const p of [null, undefined, "", "-1", "1", "10", "garbage", "0.5"])
    assert.equal(model.phaseIndex(1, p), 0);
  assert.equal(model.phaseIndex(3, "2"), 2);
});
test("non-estimate methods without ranges and unknown claims remain renderable", () => {
  assert.equal(
    model.claimRange({
      basis: "OBSERVED",
      method: "reviewed extraction",
      range: null,
    }),
    null,
  );
  assert.equal(
    model.claimRange({ basis: "ESTIMATE", range: [100, 300] }),
    "100 – 300",
  );
  assert.equal(model.claimRange({ basis: "UNKNOWN", value: null }), null);
});
