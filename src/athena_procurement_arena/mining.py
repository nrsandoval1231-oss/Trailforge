"""Mining pack: reviewed source imports, neutral qualification, and supplier matching.

No acquisition provider or supplier policy participates in demand discovery.
"""
from __future__ import annotations

import argparse
import html
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from athena_arena.contracts import canonical_hash

from .public_capture import load_capture

PHASES = set('EXPLORATION EARLY_WORKS CONSTRUCTION COMMISSIONING INITIAL_OPERATION EXPANSION OPERATIONS RESTART CLOSURE UNKNOWN'.split())
USES = set('CAMP DEWATERING CRUSHING PROCESSING COMMISSIONING BRIDGE PRIME BACKUP SUPPLEMENTAL ELECTRIFICATION OTHER'.split())
STATUSES = set('OBSERVED HYPOTHESIS VERIFIED DISPROVEN SUPERSEDED'.split())
PACKAGES = set('UNKNOWN NOT_STARTED PLANNED SOURCING OPEN AWARDED CANCELED CLOSED'.split())
PROJECT_FIELDS = 'name company operator location commodity mining_method stage construction_date production_date epc epcm decision_makers existing_power'.split()
GROUPS = {
    'demand': 'normal_kw peak_kw duty redundancy distribution_voltage_v frequency_hz load_profile'.split(),
    'delivery': 'needed_by expected_months grid_available grid_ready_by fuel_constraints available_fuel technology_constraints altitude_m temperature_c emissions site_access black_start'.split(),
    'procurement': 'model package_status buyer_entity_id buying_window package_boundary'.split(),
}
NUMBERS = set('normal_kw peak_kw distribution_voltage_v frequency_hz expected_months altitude_m temperature_c'.split())
LISTS = {'fuel_constraints', 'available_fuel', 'technology_constraints'}
DEPENDENCIES = {
    'GRID_DELAY': ('Bridge supply may be needed until grid delivery', 'Confirm grid energization precedes the phase start or existing supply covers the gap'),
    'NO_GRID': ('Off-grid supply may be needed for this phase', 'Verify an adequate grid connection or existing independent supply'),
    'EXPANSION': ('Incremental plant load may exceed available supply', 'Obtain an electrical balance showing existing spare capacity covers expansion'),
    'INSUFFICIENT_GENERATION': ('Additional supply may be needed for new equipment', 'Verify site-rated spare generation covers the new load'),
    'COMMISSIONING': ('Temporary supply may be needed during commissioning', 'Confirm permanent supply is energized and adequate before commissioning'),
    'RESTART': ('Electrical restoration may be needed before restart', 'Verify the electrical infrastructure is serviceable and adequately sized'),
}


def stamp(value):
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError('timestamp must include timezone')
    return parsed


@dataclass(frozen=True)
class Claim:
    value: object
    basis: str
    evidence: tuple[dict, ...] = ()
    method: str | None = None
    range: tuple[float, float] | None = None


@dataclass(frozen=True)
class PowerRequirement:
    requirement_id: str
    project_id: str
    phase: Claim
    use_case: Claim
    status: str
    demand: dict[str, Claim]
    delivery: dict[str, Claim]
    procurement: dict[str, Claim]
    dependencies: tuple[dict, ...]
    review: dict
    schema_version: str = 'mining-power-requirement-v1'


@dataclass(frozen=True)
class SupplierOffering:
    supplier: str
    offering: str
    fuels: tuple[str, ...]
    technologies: tuple[str, ...]
    nominal_kw: float | None = None
    geography: tuple[str, ...] = ()
    commercial_models: tuple[str, ...] = ()
    available_by: str | None = None
    profile_basis: str = 'Operator-entered screening profile; capability requires supplier confirmation'

    def __post_init__(self):
        if not self.supplier or not self.offering:
            raise ValueError('supplier and offering names required')
        for items in (self.fuels, self.technologies, self.geography, self.commercial_models):
            if not isinstance(items, (list, tuple)) or any(not isinstance(v, str) or not v.strip() for v in items):
                raise ValueError('supplier capabilities must be lists of nonempty strings')
        if self.nominal_kw is not None and (isinstance(self.nominal_kw, bool) or not isinstance(self.nominal_kw, (int, float)) or not math.isfinite(self.nominal_kw) or self.nominal_kw <= 0):
            raise ValueError('invalid nominal rating')
        if self.available_by:
            stamp(self.available_by)


REFERENCE_SUPPLIER = SupplierOffering(
    '2G Energy Rental', 'Gas generation rental (unverified screening envelope)',
    ('natural gas', 'propane'), ('gas generation',), commercial_models=('rental',),
    profile_basis='Reference profile only; confirm fuel-specific equipment, fleet availability and site engineering with 2G',
)


def import_project(manifest: dict, base: Path) -> dict:
    """Import analyst-reviewed values against retained captures; fail before writing."""
    if manifest.get('schema_version') != 'trailforge-mining-import-v1':
        raise ValueError('unsupported mining import schema')
    cutoff = stamp(manifest['cutoff'])
    reviewer = manifest.get('reviewed_by')
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ValueError('reviewed_by is required; extraction is not verification')
    sources = {}
    for key, raw in manifest['sources'].items():
        # Rights checked before reading any source bytes. Private intake is not supported.
        if raw.get('access') not in {'PUBLIC', 'LICENSED', 'SYNTHETIC'} or raw.get('share_allowed') is not True:
            raise ValueError('private or unapproved source cannot enter the mining workspace')
        capture = load_capture(base / raw['capture_file'])
        published = stamp(raw['published_at']) if raw.get('published_at') else None
        observed = stamp(raw['first_observed_at'])
        available = stamp(raw['available_at'])
        if available < capture.captured_at or observed < capture.captured_at:
            raise ValueError('current capture cannot establish earlier availability')
        if max(t for t in (capture.captured_at, published, observed, available) if t) > cutoff:
            raise ValueError('future evidence rejected at prediction cutoff')
        sources[key] = (capture, raw)

    def claim(raw, field):
        if raw is None:
            return Claim(None, 'UNKNOWN')
        if not isinstance(raw, dict) or raw.get('value') is None:
            raise ValueError(f'{field}: use null for unknown or an evidence-bound claim')
        value, basis = raw['value'], raw.get('basis', 'OBSERVED')
        if basis not in {'OBSERVED', 'VERIFIED', 'ESTIMATE'}:
            raise ValueError(f'{field}: invalid claim basis')
        if field in NUMBERS and (isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value)
                                 or (field not in {'temperature_c', 'altitude_m'} and value < 0)):
            raise ValueError(f'{field}: invalid numeric value')
        if field in LISTS:
            if not isinstance(value, list) or not value or any(not isinstance(v, str) or not v.strip() for v in value):
                raise ValueError(f'{field}: requires nonempty list of explicit constraints')
        elif field not in NUMBERS and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f'{field}: requires text')
        vocab = {'phase': PHASES, 'use_case': USES, 'package_status': PACKAGES,
                 'grid_available': {'YES', 'NO', 'UNKNOWN'}, 'dependency': set(DEPENDENCIES)}.get(field)
        if vocab and value not in vocab:
            raise ValueError(f'{field}: invalid controlled value')
        if field in {'needed_by', 'grid_ready_by', 'construction_date', 'production_date'}:
            stamp(value)
        evidence = []
        for ref in raw.get('evidence', []):
            capture, metadata = sources[ref['source']]
            quote = ref['quote']
            if not isinstance(quote, str) or not quote.strip() or quote not in capture.content:
                raise ValueError(f'{field}: quote is not an exact source span')
            event = ref.get('event_at')
            if event:
                stamp(event)  # Future planned milestones are permitted, future evidence is not.
            evidence.append({'source_url': capture.source_url, 'capture_hash': capture.capture_hash,
                             'content_sha256': capture.content_sha256, 'quote': quote,
                             'captured_at': capture.captured_at.isoformat(), 'event_at': event,
                             **{k: metadata.get(k) for k in ('access', 'published_at', 'first_observed_at', 'available_at')}})
        if not evidence:
            raise ValueError(f'{field}: every known value requires evidence')
        method, bounds = raw.get('method'), raw.get('range')
        if basis == 'ESTIMATE':
            if field not in NUMBERS or not isinstance(method, str) or not method.strip() or not isinstance(bounds, list) or len(bounds) != 2:
                raise ValueError('estimates require numeric range and method')
            if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in bounds) or not bounds[0] <= value <= bounds[1]:
                raise ValueError('invalid estimate range')
        return Claim(value, basis, tuple(evidence), method, tuple(bounds) if bounds else None)

    def field_claim(raw, field):
        if isinstance(raw, list):
            alternatives = [claim(v, field) for v in raw]
            if len(alternatives) < 2:
                raise ValueError('conflict requires at least two source claims')
            return {'value': None, 'basis': 'CONFLICT', 'alternatives': [asdict(v) for v in alternatives]}
        return asdict(claim(raw, field))

    def fields(raw, names):
        if set(raw) - set(names):
            raise ValueError(f'unrecognized fields: {sorted(set(raw) - set(names))}')
        return {name: field_claim(raw.get(name), name) for name in names}

    project_id = manifest['project_id']
    if not isinstance(project_id, str) or not project_id.strip():
        raise ValueError('project_id required')
    project = fields(manifest['project'], PROJECT_FIELDS)
    requirements, seen = [], set()
    for raw in manifest['requirements']:
        if set(raw) - {'requirement_id', 'phase', 'use_case', 'status', 'demand', 'delivery', 'procurement', 'dependencies'}:
            raise ValueError('unrecognized requirement fields')
        identity = raw['requirement_id']
        if not isinstance(identity, str) or not identity.startswith(project_id + ':') or identity in seen:
            raise ValueError('requirement IDs must be unique and project-scoped')
        seen.add(identity)
        status = raw.get('status', 'OBSERVED')
        if status not in STATUSES:
            raise ValueError('invalid requirement status')
        req = asdict(PowerRequirement(identity, project_id, claim(raw.get('phase'), 'phase'),
                                     claim(raw.get('use_case'), 'use_case'), status, {}, {}, {}, (),
                                     {'state': 'REVIEWED', 'reviewed_by': reviewer}))
        for group, names in GROUPS.items():
            req[group] = fields(raw.get(group, {}), names)
        req['dependencies'] = [asdict(claim(d, 'dependency')) for d in raw.get('dependencies', [])]
        known = [c for g in GROUPS for c in req[g].values() if c['basis'] != 'UNKNOWN'] + [req['phase'], req['use_case']]
        if status == 'VERIFIED' and (any(c['basis'] != 'VERIFIED' for c in known) or not known):
            raise ValueError('verified requirement cannot contain estimates, conflicts or unverified classifications')
        req['unknowns'] = [f'{g}.{k}' for g in GROUPS for k, c in req[g].items() if c['basis'] in {'UNKNOWN', 'CONFLICT'}]
        req['evidence'] = [e for c in known for e in c.get('evidence', [])]
        requirements.append(req)
    if not requirements:
        raise ValueError('at least one phase-specific requirement is required, even if load is unknown')
    return {'schema_version': 'trailforge-mining-project-v1', 'project_id': project_id,
            'cutoff': cutoff.isoformat(), 'reviewed_by': reviewer, 'project': project, 'requirements': requirements,
            'sources': {key: {**capture.as_dict(), 'access': raw['access']} for key, (capture, raw) in sources.items()},
            'discovery_credit': False}


def value(req, group, field):
    return req[group][field]['value']


def qualify(req):
    """Supplier-neutral need qualification. No fuel/size/technology rejection."""
    hypotheses = []
    dependencies = list(req['dependencies'])
    inferred_trigger = {'COMMISSIONING': 'COMMISSIONING', 'EXPANSION': 'EXPANSION', 'RESTART': 'RESTART'}.get(req['phase']['value'])
    if inferred_trigger and not any(d['value'] == inferred_trigger for d in dependencies):
        dependencies.append({'value': inferred_trigger, 'evidence': req['phase']['evidence']})
    if value(req, 'delivery', 'grid_available') == 'NO' and not any(d['value'] == 'NO_GRID' for d in dependencies):
        dependencies.append({'value': 'NO_GRID', 'evidence': req['delivery']['grid_available']['evidence']})
    for dep in dependencies:
        statement, falsifier = DEPENDENCIES[dep['value']]
        hypotheses.append({'status': 'HYPOTHESIS', 'statement': f"{req['requirement_id']}: {statement} by {value(req, 'delivery', 'needed_by') or 'phase start (date unknown)' }.",
                           'falsifier': falsifier, 'evidence': dep['evidence']})
    needed, grid = value(req, 'delivery', 'needed_by'), value(req, 'delivery', 'grid_ready_by')
    if needed and grid and stamp(needed) < stamp(grid):
        hypotheses.append({'status': 'HYPOTHESIS', 'statement': f"{req['requirement_id']}: power may be required between {needed} and {grid} before grid delivery.",
                           'falsifier': 'Confirm adequate existing supply or a revised grid date before phase start',
                           'evidence': req['delivery']['needed_by']['evidence'] + req['delivery']['grid_ready_by']['evidence']})
    package = value(req, 'procurement', 'package_status')
    return {'need': req['status'], 'researchable': req['status'] not in {'DISPROVEN', 'SUPERSEDED'},
            'procurement': 'UNAVAILABLE' if package in {'AWARDED', 'CANCELED', 'CLOSED'} else 'OPEN' if package == 'OPEN' else 'UNCONFIRMED',
            'hypotheses': hypotheses, 'unknowns': req['unknowns'],
            'next_action': 'Confirm package scope and any remaining unawarded work' if package in {'AWARDED', 'CANCELED', 'CLOSED'} else
            'Obtain phase load profile and peak demand from the owner/EPC' if value(req, 'demand', 'peak_kw') is None else
            'Confirm buyer, package availability, site-rated capacity and delivery schedule'}


def match_supplier(req, supplier=REFERENCE_SUPPLIER, *, location=None):
    q = qualify(req)
    dimensions = {}
    def verdict(name, status, reason):
        dimensions[name] = {'verdict': status, 'reason': reason}
    fuels = value(req, 'delivery', 'fuel_constraints')
    technologies = value(req, 'delivery', 'technology_constraints')
    def compatible(required, offered):
        return bool({v.casefold() for v in required} & {v.casefold() for v in offered})
    verdict('fuel', 'INCOMPATIBLE' if fuels and not compatible(fuels, supplier.fuels) else 'POTENTIAL' if fuels else 'UNKNOWN',
            f"Allowed fuels: {fuels or 'UNKNOWN'}; offering fuels: {supplier.fuels}. Fuel delivery and storage require confirmation.")
    verdict('technical', 'INCOMPATIBLE' if technologies and not compatible(technologies, supplier.technologies) else 'UNKNOWN',
            'Confirm voltage, frequency, duty, emissions, transients and black start; technology compatibility alone is insufficient.')
    verdict('capacity_redundancy', 'UNKNOWN', 'Nominal ratings never establish firm capacity, N+1, parasitic allowance or temperature/altitude derating. Obtain a site engineering study and fleet allocation.')
    verdict('geography_logistics', 'POTENTIAL' if location and location in supplier.geography else 'UNKNOWN',
            'Confirm site access, transport, fuel storage and service coverage.')
    model = value(req, 'procurement', 'model')
    verdict('commercial', 'POTENTIAL' if model and model.casefold() in supplier.commercial_models else 'UNKNOWN',
            'Confirm contract model, duration, pricing, credit and mobilization economics.')
    needed = value(req, 'delivery', 'needed_by')
    verdict('delivery', 'INCOMPATIBLE' if needed and supplier.available_by and stamp(supplier.available_by) > stamp(needed) else 'UNKNOWN',
            'A dated fleet commitment and mobilization plan are required.')
    verdict('procurement', q['procurement'], 'Awarded, canceled and closed packages cannot be pursued as available; absence of an award is not openness.')
    verdict('evidence', 'INCOMPLETE' if req['unknowns'] else 'REVIEWED', 'Source bindings support reviewed claims, not engineering compliance.')
    blocked = any(d['verdict'] in {'INCOMPATIBLE', 'UNAVAILABLE'} for d in dimensions.values()) or not q['researchable']
    return {'supplier': supplier.supplier, 'offering': supplier.offering, 'requirement_id': req['requirement_id'],
            'verdict': 'DO_NOT_PURSUE' if blocked else 'RESEARCH_REQUIRED', 'engineering_compliance': 'NOT_ESTABLISHED',
            'profile_basis': supplier.profile_basis, 'dimensions': dimensions}


def render_report(project, supplier=REFERENCE_SUPPLIER):
    def esc(v):
        return html.escape(str(v))
    parts = ['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Mining opportunity intelligence</title><link rel="stylesheet" href="style.css"><body><main class="mining-report">',
             '<p><a href="/">TrailForge workbench</a> / <a href="/mining">Mining intelligence</a></p><h1>Mining opportunity report</h1>',
             f'<p>Prediction cutoff: {esc(project["cutoff"])} · Reviewed by {esc(project["reviewed_by"])}. Independent discovery credit: false.</p>',
             '<p>Source permissions: ' + esc(', '.join(sorted({s['access'] for s in project['sources'].values()}))) + '</p>']
    def show_claim(name, c):
        parts.append(f'<li><strong>{esc(name.replace("_", " "))}</strong>: {esc(c["value"] if c["value"] is not None else c["basis"])} <small>({esc(c["basis"])})</small>')
        if c.get('method'):
            parts.append(f'<p>Estimate method: {esc(c["method"])}; range: {esc(c["range"])}</p>')
        for alternative in c.get('alternatives', []):
            parts.append('<ul>')
            show_claim('Conflicting source value', alternative)
            parts.append('</ul>')
        if c.get('evidence'):
            parts.append('<details><summary>Source evidence & timestamps</summary>')
        for e in c.get('evidence', []):
            parts.append(f'<blockquote>{esc(e["quote"])}<br><a href="{esc(e["source_url"])}">Original source</a> · {esc(e["access"])}<br>Capture {esc(e["capture_hash"])}<br>Published {esc(e["published_at"])} · Captured {esc(e["captured_at"])} · Observed {esc(e["first_observed_at"])} · Available {esc(e["available_at"])} · Event {esc(e["event_at"])}</blockquote>')
        if c.get('evidence'):
            parts.append('</details>')
        parts.append('</li>')
    parts.append('<section><h2>Project overview & buying chain</h2><ul>')
    for name, c in project['project'].items():
        show_claim(name, c)
    parts.append('</ul></section>')
    for req in project['requirements']:
        q, match = qualify(req), match_supplier(req, supplier, location=project['project']['location']['value'])
        parts.append(f'<section><h2>{esc(req["requirement_id"])}</h2><p>Requirement: {esc(req["status"])} · Package: {esc(q["procurement"])}</p><ul>')
        show_claim('Phase', req['phase'])
        show_claim('Use case', req['use_case'])
        parts.append('</ul>')
        for group, title in [('demand', 'Power requirement'), ('delivery', 'Operating envelope & timing'), ('procurement', 'Commercial intelligence')]:
            parts.append(f'<h3>{title}</h3><ul>')
            for name, c in req[group].items():
                show_claim(name, c)
            parts.append('</ul>')
        parts.append('<h3>Infrastructure dependencies & falsifiable hypotheses</h3><ul>')
        for dep in req['dependencies']:
            show_claim('Observed dependency', dep)
        parts.append('</ul>')
        for hypothesis in q['hypotheses']:
            parts.append(f'<p><strong>HYPOTHESIS:</strong> {esc(hypothesis["statement"])}<br>Test / falsifier: {esc(hypothesis["falsifier"])}</p>')
        parts.append(f'<h3>Supplier match: {esc(match["supplier"])}</h3><p>{esc(match["offering"])} · {esc(match["verdict"])} · Engineering compliance NOT ESTABLISHED.</p><p>{esc(match["profile_basis"])}</p><ul>')
        for name, d in match['dimensions'].items():
            parts.append(f'<li><strong>{esc(name)}: {esc(d["verdict"])}</strong> — {esc(d["reason"])}</li>')
        parts.append(f'</ul><h3>Next action</h3><p>{esc(q["next_action"])}</p></section>')
    return ''.join(parts) + '</main></body></html>'


def load_supplier(path=None):
    return SupplierOffering(**json.loads(Path(path).read_text(encoding='utf-8'))) if path else REFERENCE_SUPPLIER


def load_project(path):
    path = Path(path)
    return import_project(json.loads(path.read_text(encoding='utf-8')), path.parent)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Import reviewed mining evidence and produce a readable opportunity report')
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--supplier', type=Path, help='optional supplier offering profile JSON')
    args = parser.parse_args(argv)
    project = load_project(args.input)
    supplier = load_supplier(args.supplier)
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / canonical_hash({'project': project, 'supplier': asdict(supplier)})
    target.mkdir()  # immutable version, never overwrite
    (target / 'project.json').write_text(json.dumps(project, indent=2) + '\n', encoding='utf-8')
    (target / 'supplier.json').write_text(json.dumps(asdict(supplier), indent=2) + '\n', encoding='utf-8')
    (target / 'report.html').write_text(render_report(project, supplier), encoding='utf-8')
    from importlib.resources import files
    (target / 'style.css').write_bytes(files('athena_procurement_arena').joinpath('ui_assets', 'style.css').read_bytes())
    print(target / 'report.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
