"""Build the fixed three-family archive-observation cohort from retained bytes."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
PR7 = ROOT / "research/pre-rfp-history/pr7/hc-001"
RECOVERY = ROOT / "research/pre-rfp-history/recovery-attempts"
CASES = ROOT / "research/pre-rfp-history/cases"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy(src: Path, dest: Path) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
    return dest.as_posix()


def _supplemental_ref(evidence_id: str, path: str, quote: str, claims: dict) -> dict:
    from athena_procurement_arena.public_capture import load_capture

    capture_path = (PR7 / path).resolve(strict=True)
    capture = load_capture(capture_path)
    if quote not in capture.content:
        raise ValueError(f"supplemental quote is absent: {evidence_id}")
    return {"evidence_id": evidence_id, "capture_path": "../../pr7/hc-001/" + path,
            "capture_id": capture.capture_id, "capture_hash": capture.capture_hash,
            "content_sha256": capture.content_sha256, "source_url": capture.source_url,
            "source_quote": quote, "reviewed_claims": claims,
            "event_date": "UNKNOWN", "document_date": "UNKNOWN",
            "verified_available_at": "UNKNOWN", "observed_at": "UNKNOWN",
            "replay_included": False, "exclusion_reason": "RETAINED_CONTEXT_WITHOUT_VERIFIED_HISTORICAL_AVAILABILITY"}


def _emit_case(case_id: str, family: str, project: str, facility: str, activity: str,
               body_source: Path, headers_source: Path, receipt: dict,
               original_url: str, memento: str, quote: str, invalidators: list[str],
               claims: dict, supplemental_refs: list[dict] | None = None,
               reported_document_date: str = "UNKNOWN") -> None:
    case_dir = CASES / case_id
    if case_dir.exists() and any(case_dir.iterdir()):
        raise FileExistsError(f"case output is write-once; choose a new case root: {case_dir}")
    case_dir.mkdir(parents=True, exist_ok=True)
    body_path = Path(_copy(body_source, case_dir / "captures/archive.body")).relative_to(case_dir).as_posix()
    headers_path = Path(_copy(headers_source, case_dir / "captures/archive.headers.txt")).relative_to(case_dir).as_posix()
    receipt["body_path"] = body_path
    receipt["headers_path"] = headers_path
    from athena_procurement_arena.historical_cases import archive_representation_text
    from athena_procurement_arena.public_capture import capture_markdown, write_capture
    body_content = archive_representation_text((case_dir / body_path).read_bytes())
    capture_obj = capture_markdown(receipt["source_url"], body_content, capture_id=f"{case_id}-archive",
        captured_by="retained-archive-receipt", captured_at=datetime.now(UTC),
        provider="retained-wayback-http")
    capture_file = case_dir / "captures/archive.capture.json"
    write_capture(capture_obj, capture_file)
    capture = _json(capture_file)
    capture_path = capture_file.relative_to(case_dir).as_posix()
    receipt_path = case_dir / "captures/archive.receipt.json"
    receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    receipt_rel = receipt_path.relative_to(case_dir).as_posix()
    when = datetime.fromisoformat(memento.replace("Z", "+00:00"))
    event_time = when.isoformat()
    claims = {key: value for key, value in claims.items() if not key.startswith("case_")}
    claims = {**claims, "project_specific": True, "archive_representation_observation": True}
    evidence_id = f"{case_id}-archive-observation"
    proof = {"capture_path": capture_path, "receipt_path": receipt_rel,
             "archive_url": capture["source_url"], "original_url": original_url,
             "memento_datetime": memento, "body_path": body_path,
             "body_sha256": _sha(case_dir / body_path), "headers_path": headers_path,
             "headers_sha256": _sha(case_dir / headers_path),
             "header_transformation": receipt["header_transformation"]}
    ref = {"evidence_id": evidence_id, "capture_path": capture_path,
           "capture_id": capture["capture_id"], "capture_hash": capture["capture_hash"],
           "content_sha256": capture["content_sha256"], "source_url": capture["source_url"],
           "source_quote": quote, "reviewed_claims": claims,
           "event_date": event_time, "document_date": event_time,
           "verified_available_at": event_time, "observed_at": capture["captured_at"],
           "replay_included": True, "archive_version_proof": proof,
           "observation_kind": "ARCHIVE_REPRESENTATION_OBSERVATION",
           "date_semantics": "REPRESENTATION_OBSERVATION_ONLY",
           "reported_document_date": reported_document_date, "reported_event_date": "UNKNOWN"}
    scenario = {"schema_version": "procurement-arena-scenario-v1", "scenario_id": case_id,
                "version": "1", "seed": 1, "tenant_id": "default",
                "timeline": [event_time, capture["captured_at"]],
                "evidence": [{"evidence_id": evidence_id, "source_id": capture["capture_id"],
                    "event_date": event_time, "document_date": event_time,
                    "verified_available_at": event_time, "observed_at": capture["captured_at"],
                    "claims": claims, "claim_basis": "REPORTED",
                    "source_version": capture["content_sha256"], "lineage_family": family,
                    "is_prediction": False, "tenant_id": "default", "authority": "UNKNOWN",
                    "source_spans": [quote], "entity_candidates": [], "permission_scope": "PUBLIC",
                    "contradictions": []}],
                "truth": {"procurement_episode_id": family, "outcome": "UNKNOWN", "solicitation_at": None}}
    (case_dir / "scenario.json").write_text(json.dumps(scenario, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    case = {"schema_version": "trailforge-pre-rfp-case-v1", "case_id": case_id,
        "procurement_family_id": family, "project_identity": project, "location": "UNKNOWN",
        "facility_type": facility, "power_activity": activity, "purchase_type": claims.get("case_purchase_type", "UNKNOWN"),
        "outcome": "UNKNOWN", "known_buying_event": "UNKNOWN", "buying_event_date": "UNKNOWN",
        "conventional_milestone": "UNKNOWN", "conventional_milestone_at": "UNKNOWN",
        "conventional_milestone_evidence_id": None, "scenario_path": "scenario.json",
        "holdout_group": "DEVELOPMENT", "buyer_path": [], "evidence_sources": [ref, *(supplemental_refs or [])],
        "historical_milestones": [], "first_buyer_actionable_at": None,
        "research_burden": {"historical_human_research_time": "UNKNOWN",
            "attribution_status": "COHORT_LEVEL_NOT_ALLOCATED",
            "burden_source": "research/pre-rfp-history/recovery-attempts/SUMMARY.json"},
        "invalidators": invalidators,
        "cohort_role": "PURPOSIVE_DEVELOPMENT_FAMILY_NOT_HOLDOUT"}
    (case_dir / "case.json").write_text(json.dumps(case, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def prepare() -> list[Path]:
    existing_cases = [CASES / name / "case.json" for name in ("crusoe-abilene", "montauk-2021", "azure-sky-wind")]
    if all(path.is_file() for path in existing_cases):
        raise FileExistsError("case roots already exist and are immutable; consume the existing cases")
    originals = PR7
    records = _json(originals / "recovery-originals/manifest.json")["records"]
    by_url = {item["source_url"]: item for item in records}
    # Convert retained original manifest rows into per-case receipt records while
    # preserving exact source paths and digests for deterministic verification.
    crusoe_url = "https://web.archive.org/web/20240718155507/https://lancium.com/press-release/crusoe-lancium-clean-campus/"
    crusoe = by_url[crusoe_url]
    crusoe_body, crusoe_headers = originals / crusoe["body_path"], originals / crusoe["headers_path"]
    _emit_case("crusoe-abilene", "crusoe-abilene-lancium-campus", "Crusoe Abilene / Lancium Clean Campus",
        "data_center", "construction", crusoe_body, crusoe_headers,
        {**crusoe, "header_transformation": crusoe["header_transformation"]},
        "https://lancium.com/press-release/crusoe-lancium-clean-campus/", crusoe["memento_datetime_utc"],
        "Crusoe Energy Systems LLC", ["2025 portfolio turbine order is not attributed to Abilene"],
        {"generation_need_supported": False, "need_reason": "UNKNOWN",
         "buyer_organization": "Crusoe", "project_responsibility_supported": True,
         "case_purchase_type": "UNKNOWN",
         "usable_direct_route": False, "required_mw": None},
        [_supplemental_ref("crusoe-2025-expansion", "recovery-captures/crusoe-legacy-target-live.capture.json",
            "natural gas turbines to power its back-up power supply", {
                "project_specific": True, "generation_need_supported": False,
                "need_reason": "backup generation is described; temporary rental need UNKNOWN",
                "buyer_organization": "Crusoe", "project_responsibility_supported": True,
                "usable_direct_route": False, "required_mw": None,
                "scope_note": "2025 campus expansion; not a procurement solicitation"})], "2024-07-18")

    montauk_url = "https://web.archive.org/web/20210507164802/https://www.lipower.org/wp-content/uploads/2021/03/MTK-2021-Neg-Dec-signed.pdf"
    montauk = by_url[montauk_url]
    montauk_body = originals / montauk["body_path"]
    montauk_headers = originals / montauk["headers_path"]
    _emit_case("montauk-2021", "montauk-2021-2024", "Montauk transmission upgrades 2021",
        "utility", "transmission_upgrade", montauk_body, montauk_headers,
        {**montauk, "header_transformation": montauk["header_transformation"]},
        "https://www.lipower.org/wp-content/uploads/2021/03/MTK-2021-Neg-Dec-signed.pdf",
        montauk["memento_datetime_utc"], "Project: Montauk Temporary Generation Facility", [
            "2017 Montauk Energy Storage Center PPA is a different family",
            "The 2021 environmental review is not a verified solicitation release"],
        {"generation_need_supported": True,
         "need_reason": "temporary modular generation supports transmission reliability during outages",
         "buyer_organization": "PSEG Long Island", "project_responsibility_supported": True,
         "usable_direct_route": False, "required_mw": None,
        "case_purchase_type": "temporary_generation_service"}, [
            _supplemental_ref("montauk-pseg-related-infrastructure", "searches/hc-montauk-search.json",
                "Montauk", {"project_specific": False, "buyer_organization": "UNKNOWN",
                            "generation_need_supported": False, "scope_note": "related infrastructure context; exact-family route UNKNOWN"})], "2021-03-11")

    azure_attempt = _json(RECOVERY / "azure-2021-body.json")
    azure_url = azure_attempt["final_url"]
    azure_time = "2021-03-03T17:00:47Z"
    # Retain exact HTML bytes and a matching capture representation.
    html_path = RECOVERY / "azure-2021.html"
    quote = "has started construction of Azure Sky wind + storage"
    _emit_case("azure-sky-wind", "azure-sky-commissioning", "Azure Sky wind / Throckmorton",
        "wind_generation", "construction", html_path, RECOVERY / "azure-2021.headers.txt",
        {"source_url": azure_url, "memento_datetime_utc": azure_time,
         "body_sha256": azure_attempt["sha256"], "headers_sha256": azure_attempt["header_sha256"],
         "header_transformation": azure_attempt["header_transformation"]},
        "https://www.enel.com/media/explore/search-press-releases/press/2021/03/enels-first-large-scale-wind--storage-hybrid-project-will-support-kellogg-company-with-renewable-energy0",
        azure_time, quote, ["Construction and VPPA announcement does not establish temporary generation procurement"],
        {"generation_need_supported": False, "need_reason": "UNKNOWN",
         "buyer_organization": "Enel Green Power North America", "project_responsibility_supported": True,
         "case_purchase_type": "UNKNOWN",
         "usable_direct_route": False, "required_mw": None},
        [_supplemental_ref("azure-commissioning-undated", "captures/azure-power.capture.json",
            "Aggreko", {"project_specific": True, "generation_need_supported": False,
                "need_reason": "commissioning mention; temporary generation requirement UNKNOWN",
                "buyer_organization": "Enel Green Power North America",
                "project_responsibility_supported": False, "usable_direct_route": False,
                "required_mw": None, "availability_status": "UNKNOWN"})], "2021-03-03")
    # Supplemental source says Azure's Enel client needed a commissioning service;
    # preserve that known identity and service type with date/availability UNKNOWN.
    azure_case_path = CASES / "azure-sky-wind" / "case.json"
    azure_case = _json(azure_case_path)
    supplemental = _supplemental_ref("azure-commissioning-undated", "captures/azure-power.capture.json",
        "Aggreko provided off-grid contingency power", {
            "project_specific": True, "generation_need_supported": True,
            "need_reason": "commissioning service documented; release solicitation timing UNKNOWN",
            "buyer_organization": "Enel Green Power", "project_responsibility_supported": True,
            "usable_direct_route": False, "required_mw": None,
            "purchase_type": "commissioning_service", "availability_status": "UNKNOWN"})
    azure_case["evidence_sources"].append(supplemental)
    azure_case["purchase_type"] = "commissioning_service"
    azure_case_path.write_text(json.dumps(azure_case, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return [CASES / name / "case.json" for name in ("crusoe-abilene", "montauk-2021", "azure-sky-wind")]


if __name__ == "__main__":
    print(json.dumps({"cases": [str(path) for path in prepare()]}, sort_keys=True))
