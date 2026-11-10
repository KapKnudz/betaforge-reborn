from copy import deepcopy
import hashlib
import json
import unittest

import test_tools
from betaforge import management_history as history
from betaforge.storage import EvidenceStore
from betaforge.tools import EvidenceTools, write_json


def append_transactions(capture, instrument_id=426):
    """Synthetic versions, entities, unknown categories and out-of-window rows."""
    values = [
        {'name': 'Sample Person', 'tradeDate': '2026-09-01', 'type': 1, 'quantity': '20'},
        {'name': 'Sample Person', 'tradeDate': '2026-09-01', 'type': 1, 'quantity': '25', 'correction': 'possible'},
        {'name': 'Sample Holding AB', 'tradeDate': '2024-01-01', 'type': 99, 'quantity': '4'},
        {'name': 'Unmatched Name', 'tradeDate': '2020-01-01', 'type': 1, 'quantity': '5'},
        {'name': 'Other Person', 'tradeDate': None, 'type': 77, 'quantity': '6'},
        {'name': 'Future Dated', 'tradeDate': '2027-01-01', 'type': 1, 'quantity': '7'},
    ]
    body = json.dumps({'list': [{'insId': instrument_id, 'values': values},
                               {'insId': instrument_id + 1, 'values': [{'name': 'Other Issuer Owner'}]}]}).encode()
    (capture / 'insider.json').write_bytes(body)
    manifest = json.loads((capture / 'manifest.json').read_text())
    manifest['requests'].append({'endpoint': '/v1/holdings/insider', 'parameters': {}, 'http_status': 200,
                                 'file': 'insider.json', 'sha256': hashlib.sha256(body).hexdigest()})
    write_json(capture / 'manifest.json', manifest)


def history_fixture(store, *, instrument_id=426, report_id='example', quote='Net revenue was 10.25 million SEK.', analysis_date='2026-11-04'):
    refs = [{'id': 'report', 'kind': 'report', 'report_id': report_id, 'page': 1, 'quote': quote}]
    parties = [
        {'id': f'{instrument_id}:person', 'kind': 'individual', 'name': 'Sample Person', 'source_refs': ['report'],
         'aliases': [{'name': 'S. Person', 'source_refs': ['report']}]},
        {'id': f'{instrument_id}:holding', 'kind': 'entity', 'name': 'Sample Holding AB', 'source_refs': ['report'], 'aliases': []},
    ]
    transactions = []
    reported_parties = {}
    for i, row in enumerate(store.query_dataset('holdings_insider', instrument_id, limit=5000)):
        refs.append(dict(id=f'row{i}', kind='dataset', **{key: row[key] for key in ('dataset', 'source_id', 'pointer')}, row_id=row['id']))
        day = row['payload'].get('tradeDate')
        inside = day is not None and '2021-11-04' <= day <= analysis_date
        owner = row['payload']['name']
        reported_id = f'{instrument_id}:owner-' + hashlib.sha256(owner.encode()).hexdigest()[:12]
        reported = reported_parties.setdefault(reported_id, {'id': reported_id, 'kind': 'unresolved', 'name': owner,
                                                             'source_refs': [], 'aliases': []})
        reported['source_refs'].append(f'row{i}')
        transactions.append({**{key: row[key] for key in ('dataset', 'source_id', 'pointer', 'payload')},
                             'row_id': row['id'], 'reported_party_id': reported_id,
                             'party_id': None, 'match_status': 'unresolved', 'match_source_refs': [],
                             'date': day, 'window_status': 'unknown' if day is None else 'inside' if inside else 'outside',
                             'related_row_ids': [], 'note': 'Preserved raw row; identity and type require source challenge.'})
    return {'schema_version': 1, 'instrument_id': instrument_id, 'analysis_date': analysis_date,
            'window': {'start': '2021-11-04', 'end': analysis_date},
            'source_scope': {'report_ids': [report_id], 'transaction_datasets': ['holdings_insider'],
                             'limitations': ['Frozen captured evidence only; not a complete public register.']},
            'source_refs': refs, 'parties': parties + list(reported_parties.values()),
            'role_observations': [{'id': 'ceo-observed', 'party_id': f'{instrument_id}:person', 'role': 'CEO',
                                   'observed_date': None, 'source_refs': ['report'], 'note': 'Actual observation date unknown.'}],
            'role_intervals': [{'id': 'ceo-tenure', 'party_id': f'{instrument_id}:person', 'role': 'CEO',
                                'start_date': None, 'end_date': None, 'source_refs': ['report'],
                                'note': 'Employment year does not establish role start.'}],
            'ownership_observations': [{'id': 'holding-observed', 'party_id': f'{instrument_id}:holding',
                                       'observed_date': '2025-12-31', 'holding': '1,000 shares as disclosed',
                                       'basis': 'Direct entity ownership; no inferred beneficial owner',
                                       'source_refs': ['report'], 'note': 'No inferred current ownership.'}],
            'commitment_links': [{'id': 'commitment', 'statement': 'A sourced management statement.',
                                  'party_ids': [], 'role_interval_ids': [], 'source_refs': ['report'],
                                  'responsibility_source_refs': [], 'note': 'Responsible management unresolved.'}],
            'transaction_links': transactions}


class ManagementHistoryTests(unittest.TestCase):
    def setUp(self):
        test_tools.ToolsTests.setUp(self)
        self.addCleanup(self.temp.cleanup)
        self.tools.store.close()
        append_transactions(self.root / 'source')
        with EvidenceStore(self.root / 'live/evidence.sqlite3') as store:
            store.ingest_snapshot(self.root / 'source')
            store.freeze(self.root / 'history-snapshot')
        packet = json.loads(self.packet.read_text())
        packet.update(snapshot_dir='history-snapshot', analysis_date='2026-11-04')
        write_json(self.packet, packet)
        self.tools = EvidenceTools(self.packet, self.root / 'history-fixture')
        self.addCleanup(self.tools.store.close)
        self.value = history_fixture(self.tools.store)

    def validate(self, value):
        return history.validate(value, 426, '2026-11-04', reports=self.tools.reports, store=self.tools.store)

    def test_preserves_all_raw_versions_entities_unmatched_and_outside_rows(self):
        self.assertEqual(self.validate(self.value), self.value)
        rows = self.value['transaction_links']
        self.assertEqual(len(rows), 6)
        self.assertEqual(sorted(row['window_status'] for row in rows), ['inside'] * 3 + ['outside'] * 2 + ['unknown'])
        self.assertTrue(all(row['party_id'] is None for row in rows))
        parties = {party['id']: party for party in self.value['parties']}
        self.assertTrue(all(parties[row['reported_party_id']]['kind'] == 'unresolved' for row in rows))
        self.assertEqual({parties[row['reported_party_id']]['name'] for row in rows},
                         {row['payload']['name'] for row in rows})
        linked = deepcopy(self.value)
        first, second = linked['transaction_links'][:2]
        first.update(party_id='426:person', match_status='matched', match_source_refs=['report'], related_row_ids=[second['row_id']])
        self.validate(linked)
        linked['role_intervals'][0].update(start_date='2027-01-01', end_date=None)
        self.validate(linked)  # An announced future effective date is not an actual observation date.

    def test_strict_structure_sources_dates_and_row_preservation(self):
        mutations = [
            lambda v: v.update(schema_version=True), lambda v: v.update(instrument_id=427),
            lambda v: v.update(analysis_date='2026-11-05'), lambda v: v.update(extra='unversioned'),
            lambda v: v['window'].update(start=v['analysis_date']), lambda v: v['window'].update(end='2026-11-03'),
            lambda v: v['source_scope'].update(limitations=[]), lambda v: v['source_scope'].update(report_ids=['missing']),
            lambda v: v['source_refs'][0].update(page=3), lambda v: v['source_refs'][0].update(quote='Invented quote'),
            lambda v: v['source_refs'][1].update(pointer='/invented'),
            lambda v: v['source_refs'][1].update(row_id='unknown'),
            lambda v: v['parties'][0].update(id='427:person'),
            lambda v: v['parties'][0]['aliases'][0].update(source_refs=[]),
            lambda v: v['role_observations'][0].update(observed_date='2027-01-01'),
            lambda v: v['role_intervals'][0].update(start_date='2025-01-01', end_date='2024-01-01'),
            lambda v: v['ownership_observations'][0].update(observed_date='2026-02-30'),
            lambda v: v['commitment_links'][0].update(party_ids=['426:person']),
            lambda v: v['transaction_links'].pop(), lambda v: v['transaction_links'].append(v['transaction_links'][0]),
            lambda v: v['transaction_links'][0]['payload'].update(quantity='999'),
            lambda v: v['transaction_links'][0].update(pointer='/invented'),
            lambda v: v['transaction_links'][0].update(party_id='426:person'),
            lambda v: v['transaction_links'][0].update(reported_party_id='426:person'),
            lambda v: v['transaction_links'][0].update(reported_party_id='missing'),
            lambda v: v['transaction_links'][0].update(match_status='matched', party_id='426:person'),
            lambda v: v['transaction_links'][0].update(match_status='matched', party_id='426:person', match_source_refs=['row0']),
            lambda v: v['transaction_links'][0].update(window_status='unknown'),
            lambda v: v['transaction_links'][0].update(related_row_ids=['missing']),
        ]
        for mutate in mutations:
            value = deepcopy(self.value)
            mutate(value)
            with self.subTest(mutation=mutate), self.assertRaises(ValueError):
                self.validate(value)

    def test_loading_and_pure_identity_reject_ambiguous_or_unsafe_json(self):
        for body in (b'{"schema_version":1,"schema_version":1}', b'{"value":NaN}', b'{"value":1e999}', b'\xff',
                     b' ' * (history.MAX_BYTES + 1)):
            with self.subTest(body=body[:60]), self.assertRaises(ValueError):
                history.loads(body)
        body = json.dumps(self.value).encode()
        metadata = history.metadata(self.value, body)
        history.validate_metadata(metadata, 426, '2026-11-04')
        for change in ({'path': '../outside.json'}, {'path': '/absolute.json'}, {'path': 'a\\b.json'},
                       {'path': './history.json'}, {'path': 'a//b.json'}, {'sha256': 'bad'}, {'instrument_id': 427},
                       {'schema_version': True}, {'window': {'start': '2021-11-04', 'end': '2026-11-03'}}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                history.validate_metadata(dict(metadata, **change), 426, '2026-11-04')

    def test_foreign_rows_are_excluded_and_cannot_be_used_as_company_references(self):
        all_rows = self.tools.store.query_dataset('holdings_insider', limit=5000)
        foreign = next(row for row in all_rows if row['instrument_id'] != 426)
        self.assertNotIn(foreign['id'], {row['row_id'] for row in self.value['transaction_links']})
        value = deepcopy(self.value)
        value['source_refs'].append({'id': 'foreign', 'kind': 'dataset', 'row_id': foreign['id'],
                                     **{key: foreign[key] for key in ('dataset', 'source_id', 'pointer')}})
        with self.assertRaisesRegex(ValueError, 'dataset reference mismatch'):
            self.validate(value)

    def test_explicit_empty_scope_does_not_create_trades_or_matches(self):
        capture = self.root / 'empty-capture'
        capture.mkdir()
        body = json.dumps({'list': []}).encode()
        (capture / 'empty.json').write_bytes(body)
        write_json(capture / 'manifest.json', {'retrieved_at': '2026-11-04T00:00:00Z', 'requests': [
            {'endpoint': '/v1/holdings/insider', 'parameters': {}, 'http_status': 200,
             'file': 'empty.json', 'sha256': hashlib.sha256(body).hexdigest()}]})
        with EvidenceStore(self.root / 'empty/evidence.sqlite3') as store:
            store.ingest_snapshot(capture)
            value = history_fixture(store)
            self.assertEqual(value['transaction_links'], [])
            history.validate(value, 426, '2026-11-04', reports=self.tools.reports, store=store)
            self.assertTrue(value['source_scope']['limitations'])


if __name__ == '__main__':
    unittest.main()
