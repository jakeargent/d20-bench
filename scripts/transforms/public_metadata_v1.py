"""Version 1 of the public metadata format.

Run once with ``uv run python scripts/transforms/public_metadata_v1.py``.
The input arrays must match the recorded original SHA-256 values. The update
changes descriptive metadata and annotation prose only. Record-specific text
edits use exact text hashes, never pattern-based substitutions. Repeated runs
verify the transformed payload without rewriting it.

Integrity digests protect complete answer records except annotation reasons,
uncertainty-note text and the explicitly normalized metadata below. In
particular, they include every score, claim award, grader status, profile,
candidate answer, request, token count and timing. Complete result records and
case records are protected after the same metadata normalization. No original
answer payload or removed annotation text is stored alongside the new data.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

TRANSFORM_ID = 'public-metadata-v1'
VERSION = 1
ROOT = Path(__file__).resolve().parents[2]
EDIT_PATH = Path(__file__).with_name('annotation_text_v1.json')
CLAIM_DETAIL = 'Final scores and correctness judgments are available; per-claim awards are unavailable.'
VISIBILITY_BASIS = '18 human-reviewed cases: 12 selected randomly by topic and six selected deliberately.'
PRIVATE_DISCLOSURE = 'The other 102 cases contribute aggregate statistics only.'


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def retained_hash(payload, policy):
    source_ids = {v: k for k, v in policy['configuration_ids'].items()}
    original_ids = copy.deepcopy(payload)
    for item in original_ids:
        item['configuration'] = source_ids[item['configuration']]
    return digest(original_ids)


def normalize_answer_metadata(row):
    historical = row.get('historical_review')
    if historical:
        historical.pop('origin', None)
        historical.pop('source', None)
        historical['claim_detail'] = CLAIM_DETAIL
    annotations = row.get('historical_expert_annotations')
    if annotations is not None:
        row['historical_expert_annotations'] = {
            {'gpt': 'grader_1', 'sonnet': 'grader_2'}.get(k, k): v
            for k, v in annotations.items()}
    review = row.get('final_review')
    if review:
        review['kind'] = 'human'
        review['scope'] = {'claim_C004': 'claim', 'material_error_profile': 'material_error',
                           'profile': 'correctness'}.get(review['scope'], review['scope'])
        if review['verdict'] == 'claim_award_accepted':
            review['verdict'] = 'points_awarded'


def normalize_quality(quality):
    if 'pending_reviews' in quality:
        if 'unknown_judgments' in quality:
            raise ValueError('Duplicate uncertainty count')
        quality['unknown_judgments'] = quality.pop('pending_reviews')
    return quality


def normalize_results(results):
    results['random_human_audit'] = 'not performed'
    for cfg in results['configurations']:
        for key in ('runtime_version', 'exact_gpu_placement', 'selected_variant', 'reasoning_effort'):
            if cfg.get(key) in ('not verified', 'not separately specified'):
                cfg[key] = None
        if cfg.get('generation_seed_status') == 'not set; native API does not expose it':
            cfg['generation_seed_status'] = 'not set'
    for cell in results['cells']:
        normalize_quality(cell['quality'])


RUBRIC_TEXT = {
    'The most error-prone requested item: the carryover trap. It includes the explanation of why the earlier two failures are gone.':
        'The tally and the explanation of why the earlier two failures are gone.',
    'The conceptual trap (reset on becoming Stable) is handled correctly, but the tally itself is incomplete.':
        'The reset on becoming Stable is handled correctly, but the tally itself is incomplete.',
    'The Strength-versus-Dexterity trap is the main prerequisite and is handled correctly; the level point is only omitted.':
        'The Strength-or-Dexterity prerequisite is handled correctly; the level point is only omitted.',
    'The answer for Scenario A and the central trap. The source requires only an attack roll against an enemy, so a miss still extends the Rage.':
        'The answer for Scenario A and its explanation. The source requires only an attack roll against an enemy, so a miss still extends the Rage.',
}


def normalize_cases(cases):
    def rubric(value):
        if isinstance(value, dict):
            return {k: rubric(v) for k, v in value.items()}
        if isinstance(value, list):
            return [rubric(v) for v in value]
        if isinstance(value, str):
            return RUBRIC_TEXT.get(value, value).replace('existing full weight', 'full weight')
        return value
    for case in cases['cases']:
        case['requirements'] = rubric(case['requirements'])


def apply_annotation_edits(rows):
    by_key = {(r['configuration'], r['case_id'], r['condition']): r for r in rows}
    changes = []
    for edit in read(EDIT_PATH):
        row = by_key.get(tuple(edit['record']))
        if row is None:
            continue
        path = [dict(gpt='grader_1', sonnet='grader_2').get(p, p) if isinstance(p, str) else p
                for p in edit['path']]
        parent = row
        for key in path[:-1]:
            parent = parent[key]
        key = path[-1]
        if isinstance(parent, dict) and key not in parent and edit['text'] is None:
            continue
        # All paths are checked before any list element is removed.
        old = parent[key]
        if old == edit['text']:
            continue
        if hashlib.sha256(old.encode()).hexdigest() != edit['before_sha256']:
            raise ValueError('Annotation text hash mismatch: ' + '/'.join(edit['record']))
        changes.append((parent, key, edit['text']))
    for parent, key, new in changes:
        if new is not None:
            parent[key] = new
        elif isinstance(parent, dict):
            del parent[key]
    for parent, key, new in sorted((c for c in changes if isinstance(c[0], list) and c[2] is None),
                                    key=lambda c: c[1], reverse=True):
        del parent[key]


def invariants(results, rows, cases, visibility):
    """Return digests with identical meaning before and after version 1."""
    results, rows, cases, visibility = copy.deepcopy((results, rows, cases, visibility))
    normalize_results(results)
    normalize_cases(cases)
    for row in rows:
        normalize_answer_metadata(row)
        def annotation(value):
            if isinstance(value, dict):
                return {k: annotation(v) for k, v in value.items()
                        if k not in {'reason', 'uncertainty_flags'}}
            if isinstance(value, list):
                return [annotation(v) for v in value]
            return value
        for name in ('expert_annotation', 'historical_expert_annotations'):
            if name in row:
                row[name] = annotation(row[name])
    visibility.pop('basis', None)
    visibility.pop('private_disclosure', None)
    return {name: digest(value) for name, value in
            [('results', results), ('cells', results['cells']), ('answers', rows),
             ('cases', cases), ('visibility', visibility)]}


def apply(root=ROOT, slug='01-baseline'):
    root = Path(root)
    study = root / 'studies' / slug
    policy = read(study / 'config.json')
    results = read(study / 'data/results.json')
    answers = read(study / 'data/answers.json')
    cases = read(root / 'data/cases.json')
    visibility = read(root / 'data/visibility.json')
    if policy.get('metadata_transform'):
        verify(policy, results, answers['answers'], cases, visibility)
        return policy['metadata_transform']
    original = {name: retained_hash(payload, policy) for name, payload in
                [('cells', results['cells']), ('answers', answers['answers'])]}
    if original != policy['retained_payload_sha256']:
        raise ValueError('Input payload does not match recorded hashes')
    before = invariants(results, answers['answers'], cases, visibility)
    normalize_results(results)
    for row in answers['answers']:
        normalize_answer_metadata(row)
    apply_annotation_edits(answers['answers'])
    normalize_cases(cases)
    visibility.update(basis=VISIBILITY_BASIS, private_disclosure=PRIVATE_DISCLOSURE)
    after = invariants(results, answers['answers'], cases, visibility)
    if before != after:
        raise ValueError('Metadata update changed protected data')
    policy['original_retained_payload_sha256'] = original
    policy['retained_payload_sha256'] = {name: retained_hash(payload, policy) for name, payload in
                                        [('cells', results['cells']), ('answers', answers['answers'])]}
    policy['metadata_transform'] = {'id': TRANSFORM_ID, 'version': VERSION, 'invariant_sha256': before}
    policy['preservation_basis'] = ('SHA-256 of UTF-8 JSON with sorted object keys, compact separators, '
                                    'ensure_ascii=false and preserved array order. Restore configuration '
                                    'to source_id before hashing retained arrays. Invariant digests '
                                    'use scripts/transforms/public_metadata_v1.py.')
    verify(policy, results, answers['answers'], cases, visibility)
    for path, value in [(study / 'config.json', policy), (study / 'data/results.json', results),
                        (study / 'data/answers.json', answers), (root / 'data/cases.json', cases),
                        (root / 'data/visibility.json', visibility)]:
        write(path, value)
    return policy['metadata_transform']


def verify(policy, results, rows, cases, visibility):
    transform = policy.get('metadata_transform', {})
    if transform.get('id') != TRANSFORM_ID or transform.get('version') != VERSION:
        raise ValueError('Unknown metadata transform')
    for name, payload in [('cells', results['cells']), ('answers', rows)]:
        if retained_hash(payload, policy) != policy['retained_payload_sha256'][name]:
            raise ValueError('Retained ' + name + ' payload hash mismatch')
    if invariants(results, rows, cases, visibility) != transform['invariant_sha256']:
        raise ValueError('Protected measurements or judgments changed')


if __name__ == '__main__':
    print(json.dumps(apply(), indent=2))
