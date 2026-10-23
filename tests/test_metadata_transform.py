"""Metadata migrations preserve measurements, judgments and source integrity."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from transforms import public_metadata_v1 as m


class MetadataTransformTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        study = ROOT / 'studies/01-baseline'
        cls.policy = m.read(study / 'config.json')
        cls.results = m.read(study / 'data/results.json')
        cls.answers = m.read(study / 'data/answers.json')['answers']
        cls.cases = m.read(ROOT / 'data/cases.json')
        cls.visibility = m.read(ROOT / 'data/visibility.json')

    def test_transformed_data_matches_recorded_invariants(self):
        m.verify(self.policy, self.results, self.answers, self.cases, self.visibility)
        self.assertEqual(set(self.policy['original_retained_payload_sha256']), {'answers', 'cells'})
        self.assertEqual(sum(c['quality']['unknown_judgments'] for c in self.results['cells']), 253)
        self.assertNotIn('pending_reviews', json.dumps(self.results))

    def test_resigning_payload_hash_does_not_allow_measurement_or_judgment_changes(self):
        # Each mutation also gets a new payload hash: the independent invariant
        # must still detect changes to numeric fields, nulls and status strings.
        award_row = next(i for i, row in enumerate(self.answers) if row['claim_awards'])
        mutations = [
            ('answers', (0, 'score', 'earned_points'), 99),
            ('answers', (0, 'score', 'complete_task_success'), None),
            ('answers', (0, 'score', 'has_material_error'), True),
            ('answers', (award_row, 'claim_awards', 0, 'earned_points'), 1),
            ('answers', (award_row, 'claim_awards', 0, 'status'), 'uncertain'),
            ('answers', (award_row, 'expert_annotation', 'claims', 0, 'status'), 'uncertain'),
            ('answers', (0, 'operations', 'total_output_tokens'), 1),
            ('answers', (0, 'request_timing', 'total_attempt_seconds'), 0.0),
            ('cells', (0, 'quality', 'unknown_judgments'), 999),
            ('cells', (0, 'quality', 'profile_assessed'), 119),
            ('cells', (0, 'timing', 'median_seconds'), 0.0),
        ]
        for name, path, replacement in mutations:
            with self.subTest(name=name, path=path):
                policy, results, answers = copy.deepcopy((self.policy, self.results, self.answers))
                payload = answers if name == 'answers' else results['cells']
                target = payload
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = replacement
                policy['retained_payload_sha256'][name] = m.retained_hash(payload, policy)
                with self.assertRaisesRegex(ValueError, 'Protected measurements or judgments changed'):
                    m.verify(policy, results, answers, self.cases, self.visibility)

    def test_update_checks_input_hash_preserves_data_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            study = root / 'studies/01-baseline'
            (study / 'data').mkdir(parents=True)
            (root / 'data').mkdir()
            results = {'configurations': [], 'cells': [{'configuration': 'example/off',
                       'quality': {'pending_reviews': 2, 'mean_claim_score': 75.5}}]}
            rows = [{'configuration': 'example/off', 'case_id': 'example', 'condition': 'no_source',
                     'score': {'earned_points': 75.5, 'complete_task_success': None},
                     'operations': {'total_output_tokens': 100}}]
            cases, visibility = {'cases': []}, {'case_ids': [], 'public_case_count': 0}
            policy = {'configuration_ids': {'source/off': 'example/off'}}
            policy['retained_payload_sha256'] = {name: m.retained_hash(payload, policy)
                                                for name, payload in [('answers', rows), ('cells', results['cells'])]}
            for path, value in [(study / 'config.json', policy), (study / 'data/results.json', results),
                                (study / 'data/answers.json', {'answers': rows}),
                                (root / 'data/cases.json', cases), (root / 'data/visibility.json', visibility)]:
                m.write(path, value)
            before = m.invariants(results, rows, cases, visibility)
            transformed = m.apply(root)
            self.assertEqual(transformed['invariant_sha256'], before)
            written = {str(p): p.read_bytes() for p in root.rglob('*.json')}
            self.assertEqual(m.apply(root), transformed)
            self.assertEqual(written, {str(p): p.read_bytes() for p in root.rglob('*.json')})
            policy['retained_payload_sha256']['answers'] = '0' * 64
            m.write(study / 'config.json', policy)
            with self.assertRaisesRegex(ValueError, 'Input payload does not match'):
                m.apply(root)

    def test_annotation_text_edits_reject_unrecognized_text(self):
        row = copy.deepcopy(next(r for r in self.answers if r['historical_expert_annotations']))
        row['historical_expert_annotations']['grader_1']['mistakes'][0]['reason'] = 'unrecognized text'
        with self.assertRaisesRegex(ValueError, 'Annotation text hash mismatch'):
            m.apply_annotation_edits([row])


if __name__ == '__main__':
    unittest.main()
