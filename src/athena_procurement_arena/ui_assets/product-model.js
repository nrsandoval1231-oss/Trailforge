/* Pure presentation selection helpers; qualification remains in the Python engine. */
const TrailforgeModel = (() => {
  function matchingPhases(item, filters) {
    if (item.kind !== "import") return [];
    return item.p.project.requirements.flatMap((req, index) => {
      const result = item.p.evaluations.find(
        (e) => e.requirement_id === req.requirement_id,
      );
      if (!result) return [];
      const matches =
        (filters.phaseFilter === "all" ||
          req.phase.value === filters.phaseFilter) &&
        (filters.procurement === "all" ||
          result.qualification.procurement === filters.procurement) &&
        (filters.fit === "all" || result.match.verdict === filters.fit);
      return matches ? [index] : [];
    });
  }
  function phaseIndex(count, requested) {
    const n = Number(requested);
    return Number.isInteger(n) && n >= 0 && n < count ? n : 0;
  }
  function claimRange(claim) {
    return Array.isArray(claim.range) && claim.range.length === 2
      ? claim.range.join(" – ")
      : null;
  }
  return { matchingPhases, phaseIndex, claimRange };
})();
if (typeof module !== "undefined") module.exports = TrailforgeModel;
