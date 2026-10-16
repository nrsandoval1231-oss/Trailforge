"""Unresolved classifications retain evidence without becoming decisions."""
import copy

import pytest
from test_mining import imported, raw

from athena_procurement_arena.mining import match_supplier, qualify, render_report


@pytest.mark.parametrize('field', ['phase', 'use_case'])
def test_classification_conflicts_preserve_alternatives_and_evidence(field):
    manifest = raw()
    requirement = manifest['requirements'][1]
    alternatives = [copy.deepcopy(manifest['requirements'][0][field]), copy.deepcopy(requirement[field])]
    requirement[field] = alternatives
    project = imported(manifest)
    req = project['requirements'][1]
    conflict = req[field]
    assert conflict['basis'] == 'CONFLICT' and conflict['value'] is None
    assert [c['value'] for c in conflict['alternatives']] == [c['value'] for c in alternatives]
    for claim, original in zip(conflict['alternatives'], alternatives, strict=True):
        assert claim['basis'] == original['basis']
        assert claim['evidence'][0]['quote'] == original['evidence'][0]['quote']
        assert claim['evidence'][0]['capture_hash'] == project['sources']['notice']['capture_hash']
        assert claim['evidence'][0] in req['evidence']
    assert field in qualify(req)['unknowns']
    assert match_supplier(req)['dimensions']['evidence']['verdict'] == 'INCOMPLETE'
    assert match_supplier(req)['verdict'] == 'RESEARCH_REQUIRED'
    assert 'Resolve phase/use-case classifications' in qualify(req)['next_action']
    assert 'Conflicting source value' in render_report(project)
    if field == 'phase':
        assert not any('during commissioning' in h['statement'] for h in qualify(req)['hypotheses'])
    else:
        assert any('during commissioning' in h['statement'] for h in qualify(req)['hypotheses'])


@pytest.mark.parametrize('field', ['phase', 'use_case'])
@pytest.mark.parametrize('mode', ['omitted', 'null'])
def test_missing_classifications_are_explicit_unknowns(field, mode):
    manifest = raw()
    requirement = manifest['requirements'][1]
    if mode == 'omitted':
        requirement.pop(field)
    else:
        requirement[field] = None
    req = imported(manifest)['requirements'][1]
    assert req[field]['value'] is None and req[field]['basis'] == 'UNKNOWN'
    assert field in qualify(req)['unknowns']
    assert match_supplier(req)['dimensions']['evidence']['verdict'] == 'INCOMPLETE'
    assert 'Resolve phase/use-case classifications' in qualify(req)['next_action']
    if field == 'phase':
        assert not any('during commissioning' in h['statement'] for h in qualify(req)['hypotheses'])


@pytest.mark.parametrize('field', ['phase', 'use_case'])
@pytest.mark.parametrize('invalid', ['quote', 'value', 'missing_evidence', 'singleton'])
def test_conflict_alternatives_still_require_valid_source_claims(field, invalid):
    manifest = raw()
    req = manifest['requirements'][1]
    claims = [copy.deepcopy(manifest['requirements'][0][field]), copy.deepcopy(req[field])]
    if invalid == 'quote':
        claims[1]['evidence'][0]['quote'] = 'unsupported invented quote'
    elif invalid == 'value':
        claims[1]['value'] = 'INVENTED_CLASSIFICATION'
    elif invalid == 'missing_evidence':
        claims[1]['evidence'] = []
    else:
        claims = claims[:1]
    req[field] = claims
    with pytest.raises(ValueError):
        imported(manifest)


@pytest.mark.parametrize('field', ['phase', 'use_case'])
def test_conflicted_classification_cannot_be_verified(field):
    manifest = raw()
    req = manifest['requirements'][1]
    req[field] = [manifest['requirements'][0][field], req[field]]
    req['status'] = 'VERIFIED'
    with pytest.raises(ValueError, match='verified requirement'):
        imported(manifest)


def test_valid_classifications_keep_existing_qualification():
    req = imported()['requirements'][1]
    assert req['phase']['value'] == req['use_case']['value'] == 'COMMISSIONING'
    assert 'phase' not in req['unknowns'] and 'use_case' not in req['unknowns']
    assert len(qualify(req)['hypotheses']) == 3
    assert qualify(req)['procurement'] == 'OPEN'
    assert match_supplier(req)['dimensions']['fuel']['verdict'] == 'POTENTIAL'
