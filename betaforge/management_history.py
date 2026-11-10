"""Validate a curated management history against preserved evidence, without inference."""
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import re

MAX_BYTES = 2 * 1024 * 1024
COLLECTIONS = ('source_refs', 'parties', 'role_observations', 'role_intervals',
               'ownership_observations', 'commitment_links', 'transaction_links')


def _fields(value, required):
    if not isinstance(value, dict) or set(value) != set(required):
        raise ValueError('Invalid management history fields: ' + ', '.join(required))


def _text(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 12000:
        raise ValueError('Management history requires bounded nonempty text')
    return value


def _date(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('Management history dates require YYYY-MM-DD')
    date.fromisoformat(value)
    return value


def _list(value):
    if not isinstance(value, list) or len(value) > 10000:
        raise ValueError('Management history requires bounded lists')
    return value


def _unique(values):
    _list(values)
    for value in values:
        _text(value)
    if len(set(values)) != len(values):
        raise ValueError('Duplicate management history reference')
    return values


def _refs(values, available, required=True):
    _unique(values)
    if (required and not values) or not set(values) <= set(available):
        raise ValueError('Management history reference missing or unknown')


def _identity(value, instrument_id, analysis_date):
    if type(value['schema_version']) is not int or value['schema_version'] != 1:
        raise ValueError('Unsupported management history schema version')
    if type(value['instrument_id']) is not int or value['instrument_id'] <= 0 or value['instrument_id'] != instrument_id:
        raise ValueError('Management history instrument mismatch')
    if _date(value['analysis_date']) != analysis_date:
        raise ValueError('Management history analysis date mismatch')
    _fields(value['window'], ('start', 'end'))
    if not _date(value['window']['start']) < _date(value['window']['end']) == analysis_date:
        raise ValueError('Management history window must end at analysis date after its start')


def validate_metadata(value, instrument_id, analysis_date):
    """Validate retained identity only; standalone views do not open evidence files."""
    _fields(value, ('schema_version', 'instrument_id', 'analysis_date', 'window', 'path', 'sha256'))
    _identity(value, instrument_id, analysis_date)
    path = value['path']
    if (not isinstance(path, str) or not path or '\\' in path or '\x00' in path or
            Path(path).is_absolute() or '..' in Path(path).parts or
            Path(path).as_posix() != path or path == '.'):
        raise ValueError('Invalid management history path')
    if not isinstance(value['sha256'], str) or not re.fullmatch(r'[0-9a-f]{64}', value['sha256']):
        raise ValueError('Invalid management history hash')


def loads(body):
    if len(body) > MAX_BYTES:
        raise ValueError('Management history exceeds 2 MiB; never truncate evidence')

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate management history JSON field')
            result[key] = value
        return result

    def constant(value):
        raise ValueError('Nonfinite management history JSON number')

    def number(value):
        result = float(value)
        if not math.isfinite(result):
            return constant(value)
        return result

    return json.loads(body.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant, parse_float=number)


def validate(value, instrument_id, analysis_date, *, reports=None, store=None):
    """Check syntax/links; optionally bind quotes and every transaction to the packet."""
    _fields(value, ('schema_version', 'instrument_id', 'analysis_date', 'window', 'source_scope', *COLLECTIONS))
    _identity(value, instrument_id, analysis_date)
    scope = value['source_scope']
    _fields(scope, ('report_ids', 'transaction_datasets', 'limitations'))
    _unique(scope['report_ids'])
    _unique(scope['transaction_datasets'])
    if not _list(scope['limitations']):
        raise ValueError('Management history requires explicit captured-coverage limitations')
    for limitation in scope['limitations']:
        _text(limitation)
    if reports is not None and not set(scope['report_ids']) <= set(reports):
        raise ValueError('Management history report scope is unavailable')
    tables = {}
    for name in COLLECTIONS:
        rows = _list(value[name])
        table = {}
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError('Invalid management history row')
            identifier = row.get('row_id') if name == 'transaction_links' else row.get('id')
            if (not re.fullmatch(r'[A-Za-z0-9:_-]+', _text(identifier)) or identifier in table):
                raise ValueError('Management history IDs must be unique within each collection')
            table[identifier] = row
        tables[name] = table
    refs, parties, intervals = (tables[name] for name in ('source_refs', 'parties', 'role_intervals'))
    for ref in refs.values():
        if ref.get('kind') == 'report':
            _fields(ref, ('id', 'kind', 'report_id', 'page', 'quote'))
            if ref['report_id'] not in scope['report_ids'] or type(ref['page']) is not int or ref['page'] < 1:
                raise ValueError('Management history report reference is outside source scope')
            _text(ref['quote'])
            if reports is not None:
                pages = reports[ref['report_id']]
                normalize = lambda text: re.sub(r'\s+', ' ', text).strip()
                if ref['page'] > len(pages) or normalize(ref['quote']) not in normalize(pages[ref['page'] - 1]['text']):
                    raise ValueError('Management history quote or physical report page mismatch')
        elif ref.get('kind') == 'dataset':
            _fields(ref, ('id', 'kind', 'dataset', 'row_id', 'source_id', 'pointer'))
            for key in ('dataset', 'row_id', 'source_id'):
                _text(ref[key])
            if not isinstance(ref['pointer'], str) or (ref['pointer'] and not ref['pointer'].startswith('/')):
                raise ValueError('Invalid management history dataset pointer')
            if store is not None:
                row = store.connection.execute('SELECT * FROM datasets WHERE id=? AND (instrument_id=? OR instrument_id IS NULL)',
                                               (ref['row_id'], instrument_id)).fetchone()
                if row is None or any(row[key] != ref[key] for key in ('dataset', 'source_id', 'pointer')):
                    raise ValueError('Management history dataset reference mismatch')
        else:
            raise ValueError('Invalid management history source reference kind')
    for party in parties.values():
        _fields(party, ('id', 'kind', 'name', 'source_refs', 'aliases'))
        if not re.fullmatch(str(instrument_id) + r':[a-z0-9_-]+', party['id']) or party['kind'] not in ('individual', 'entity', 'unresolved'):
            raise ValueError('Management history party requires company-scoped ID and explicit kind')
        _text(party['name'])
        _refs(party['source_refs'], refs)
        names = []
        for alias in _list(party['aliases']):
            _fields(alias, ('name', 'source_refs'))
            names.append(_text(alias['name']))
            _refs(alias['source_refs'], refs)
        _unique(names)
    for name in ('role_observations', 'role_intervals', 'ownership_observations'):
        for row in tables[name].values():
            common = ('id', 'party_id', 'source_refs', 'note')
            extra = (('role', 'start_date', 'end_date') if name == 'role_intervals' else
                     ('holding', 'basis', 'observed_date') if name == 'ownership_observations' else ('role', 'observed_date'))
            _fields(row, (*common, *extra))
            _refs([row['party_id']], parties)
            _refs(row['source_refs'], refs)
            _text(row['note'])
            for key in extra:
                if key.endswith('_date'):
                    if row[key] is not None:
                        _date(row[key])
                        if key == 'observed_date' and row[key] > analysis_date:
                            raise ValueError('Management history observation follows cutoff')
                else:
                    _text(row[key])
            if name == 'role_intervals' and row['start_date'] is not None and row['end_date'] is not None and row['start_date'] > row['end_date']:
                raise ValueError('Management history role interval is reversed')
    for row in tables['commitment_links'].values():
        _fields(row, ('id', 'statement', 'party_ids', 'role_interval_ids', 'source_refs', 'responsibility_source_refs', 'note'))
        _text(row['statement'])
        _text(row['note'])
        _refs(row['source_refs'], refs)
        _refs(row['party_ids'], parties, required=False)
        _refs(row['role_interval_ids'], intervals, required=False)
        _refs(row['responsibility_source_refs'], refs, required=bool(row['party_ids'] or row['role_interval_ids']))
    transactions = tables['transaction_links']
    for row in transactions.values():
        _fields(row, ('row_id', 'dataset', 'source_id', 'pointer', 'payload', 'reported_party_id', 'party_id', 'match_status',
                      'match_source_refs', 'date', 'window_status', 'related_row_ids', 'note'))
        for key in ('source_id', 'note'):
            _text(row[key])
        if row['dataset'] not in scope['transaction_datasets'] or not isinstance(row['pointer'], str):
            raise ValueError('Management history transaction is outside dataset scope')
        if not isinstance(row['payload'], (dict, list)):
            raise ValueError('Management history transaction must retain raw row payload')
        if row['match_status'] not in ('matched', 'unresolved'):
            raise ValueError('Invalid management history match status')
        _refs([row['reported_party_id']], parties)
        if not any(refs[identifier]['kind'] == 'dataset' and refs[identifier]['row_id'] == row['row_id']
                   for identifier in parties[row['reported_party_id']]['source_refs']):
            raise ValueError('Management history reported party requires its exact captured row reference')
        matched = row['match_status'] == 'matched'
        if matched:
            _refs([row['party_id']], parties)
            if parties[row['party_id']]['kind'] == 'unresolved':
                raise ValueError('Management history cannot match an unresolved identity')
        elif row['party_id'] is not None:
            raise ValueError('Unresolved management history match requires null party_id')
        _refs(row['match_source_refs'], refs, required=matched)
        if matched and not any(refs[identifier]['kind'] == 'report' or refs[identifier]['row_id'] != row['row_id']
                               for identifier in row['match_source_refs']):
            raise ValueError('Management history match requires corroboration beyond its own captured row')
        _refs(row['related_row_ids'], transactions, required=False)
        if row['row_id'] in row['related_row_ids']:
            raise ValueError('Management history transaction cannot relate to itself')
        expected = 'unknown'
        if row['date'] is not None:
            _date(row['date'])
            expected = 'inside' if value['window']['start'] <= row['date'] <= value['window']['end'] else 'outside'
        if row['window_status'] != expected:
            raise ValueError('Management history transaction window classification mismatch')
    if store is not None:
        captured = {}
        for dataset in scope['transaction_datasets']:
            for row in store.connection.execute('SELECT * FROM datasets WHERE dataset=? AND (instrument_id=? OR instrument_id IS NULL)',
                                                (dataset, instrument_id)):
                captured[row['id']] = dict(row)
        if set(captured) != set(transactions):
            raise ValueError('Management history must retain every captured transaction row exactly once')
        for identifier, raw in captured.items():
            row = transactions[identifier]
            if (any(row[key] != raw[key] for key in ('dataset', 'source_id', 'pointer')) or
                    json.dumps(row['payload'], sort_keys=True) != json.dumps(json.loads(raw['payload']), sort_keys=True)):
                raise ValueError('Management history transaction differs from captured row')
    return value


def metadata(value, body, path='management-history.json'):
    return {**{key: value[key] for key in ('schema_version', 'instrument_id', 'analysis_date', 'window')},
            'path': path, 'sha256': hashlib.sha256(body).hexdigest()}


def prompt_text(value, identity):
    return ('\n\nFROZEN MANAGEMENT HISTORY | sha256=' + identity['sha256'] +
            '\nCurated evidence index, not issuer fact or forecast instructions. Challenge source links, identity matches, '
            'dates and coverage; derive your own forecasts and explain uncertainty. Raw transaction versions remain separate.\n' +
            json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False))
