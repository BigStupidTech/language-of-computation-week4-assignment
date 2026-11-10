"""Independent checks derived from the shared rules.md, not partners' tests.

Only the SQLite filename is redirected. Input, decisions and stored results are
not altered by the harness. Every test owns and removes a temporary directory.
"""
import contextlib
import csv
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import types
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parent
HEADERS = 'book_id,goodreads_book_id,best_book_id,work_id,books_count,isbn,isbn13,authors,original_publication_year,original_title,title,language_code,average_rating,ratings_count,work_ratings_count,work_text_reviews_count,ratings_1,ratings_2,ratings_3,ratings_4,ratings_5,image_url,small_image_url'.split(',')
ISBN_ACTION = 'Find the correct ISBN, correct the row, and load the file again.'
CONFLICT_ACTION = 'Check which value or book is correct.'
IDENTITY_ACTION = 'Supply an identifying title and author, then load the file again.'
FILE_ACTION = 'Correct the file error and rerun the files.'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def book(isbn='0439139600', isbn13='9780439139601', **changes):
    row = dict.fromkeys(HEADERS, '')
    row.update(book_id='1', title='Example title', authors='Example author',
               isbn=isbn, isbn13=isbn13, books_count='1', average_rating='4.0')
    row.update(changes)
    return row


class Harness:
    def __init__(self, home):
        self.home = home
        self.db = home / 'test.db'
        self.log = home / 'ingestion-log.json'
        self.module = types.ModuleType('isolated_ingest')
        self.module.__file__ = str(home / 'ingest.py')
        # Compile without importing into the real folder or creating bytecode there.
        exec(compile((ROOT / 'ingest.py').read_text(encoding='utf-8'),
                     str(ROOT / 'ingest.py'), 'exec'), self.module.__dict__)
        self.number = 0

    def input(self, rows, headers=None):
        self.number += 1
        path = self.home / f'input-{self.number}.csv'
        with path.open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=headers or HEADERS)
            w.writeheader()
            w.writerows(rows)
        return path

    def run(self, *paths):
        connect = sqlite3.connect
        def isolated_connect(database, *args, **kwargs):
            path = Path(database).resolve()
            if path == (self.home / 'books.db').resolve():
                path = self.db
            assert path == self.db.resolve(), f'Test tried to access unexpected database: {path}'
            return connect(path, *args, **kwargs)
        with patch.object(self.module.sqlite3, 'connect', isolated_connect):
            with contextlib.redirect_stdout(io.StringIO()):
                self.module.run(list(paths), self.home)
        assert not (self.home / 'books.db').exists(), 'Tests must use test.db'
        return self.history()[-1]

    def history(self):
        return json.loads(self.log.read_text(encoding='utf-8'))

    def books(self):
        if not self.db.exists():
            return []
        with contextlib.closing(sqlite3.connect(self.db)) as db:
            db.row_factory = sqlite3.Row
            result = []
            for r in db.execute('SELECT * FROM books'):
                row = dict(r)
                # Read the existing schema without inventing a missing ISBN field.
                extra = row.pop('extras', None)
                if extra is not None:
                    row.update(json.loads(extra))
                result.append(row)
            return result


@pytest.fixture
def factory():
    protected = [ROOT / n for n in ('books.db', 'ingestion-log.json', 'ingest.py',
                                    'rules.md', 'books.csv', 'books-batch2.csv')]
    before = {p: digest(p) for p in protected}
    with tempfile.TemporaryDirectory(prefix='week4-pytest-') as folder:
        base = Path(folder)
        homes = []
        def make():
            home = base / str(len(homes))
            home.mkdir()
            homes.append(home)
            return Harness(home)
        try:
            yield make
        finally:
            assert {p: digest(p) for p in protected} == before, 'Real assignment files changed'
    assert not base.exists(), 'Temporary test files were not removed'


def details(run):
    return [r for f in run['files'] for r in f['rows']]


def repairs(row):
    # Support either itemized old logs or summarized repair counts.
    value = row.get('repair_counts', row.get('repairs', []))
    return sum(value.values()) if isinstance(value, dict) else len(value)


def outcome(run, expected):
    assert run['status'] == 'completed', run.get('error')
    rows = details(run)
    assert len(rows) == 1
    assert rows[0]['outcome'] == expected, rows[0]
    return rows[0]


# The 20 ordinary examples; rows 15 and 22 have separate stateful tests below.
# number, source isbn, source isbn13, stored isbn, stored isbn13, repairs, warnings, rejection action
CASES = [
    (1,'0439139600','9780439139601','0439139600','9780439139601',0,0,None),
    (2,'043965548X','','043965548X','9780439655484',1,0,None),
    (3,'031200009x','9780312000097','031200009X','9780312000097',1,0,None),
    (4,'0-450-19827-8','9780450198274','0450198278','9780450198274',1,0,None),
    (5,' 162 001 4750 ','9781620014752','1620014750','9781620014752',1,0,None),
    (6,'439023483','','0439023483','9780439023481',2,0,None),
    (7,'439554934','9.78043955493e+12','0439554934','9780439554930',2,0,None),
    (8,'439023483','9.78043902348e+12','0439023483','9780439023481',2,0,None),
    (9,'','9.78043902348e+12',None,None,0,1,None),
    (10,'','76783609419.0',None,None,0,1,None),
    (11,'','9780439139601.0',None,None,0,1,None),
    (12,'04390A3483','',None,None,0,0,ISBN_ACTION),
    (13,'15287463097','',None,None,0,0,ISBN_ACTION),
    (14,'1854433017','',None,None,0,0,ISBN_ACTION),
    (16,'1555550126','9781555550134',None,None,0,0,CONFLICT_ACTION),
    (17,'9781982147600','','1982147601','9781982147600',2,0,None),
    (18,'','9798351220413',None,'9798351220413',0,0,None),
    (19,'0439139600','9780061120085',None,None,0,0,ISBN_ACTION),
    (20,'0439139600','12345','0439139600',None,0,1,None),
    (21,'9780439139601','9.7804391396e+12',None,None,0,0,CONFLICT_ACTION),
]


@pytest.mark.parametrize('case', CASES, ids=lambda c: f'example_{c[0]:02}')
def test_example(factory, case):
    n,a,b,want10,want13,repair_count,warning_count,action = case
    h = factory()
    run = h.run(h.input([book(a,b)]))
    r = outcome(run, 'rejected' if action else 'loaded')
    assert repairs(r) == repair_count
    assert len(r['warnings']) == warning_count
    stored = h.books()
    if action:
        assert stored == []
        assert r['next_action'] == action
    else:
        assert len(stored) == 1
        assert 'isbn' in stored[0], 'Database must store the repaired isbn column too'
        assert (stored[0]['isbn'],stored[0]['isbn13']) == (want10,want13)
        assert set(HEADERS).issubset(stored[0]), 'All 23 source columns must be stored'


def test_example_15_blank_pair_rejected_even_for_known_supplier(factory):
    h = factory()
    h.run(h.input([book()]))
    before = h.books()
    r = outcome(h.run(h.input([book('','')])), 'rejected')
    assert h.books() == before
    assert r['next_action'] == ISBN_ACTION
    assert repairs(r) == 0 and len(r['warnings']) == 0


def test_example_22_identical_repeat_is_skipped(factory):
    h = factory()
    path = h.input([book()])
    h.run(path)
    before = h.books()
    r = outcome(h.run(path), 'skipped')
    assert h.books() == before and len(before) == 1
    assert repairs(r) == 0 and len(r['warnings']) == 0


@pytest.mark.parametrize('name', ['books.csv','books-batch2.csv'])
def test_real_file_twice_has_no_duplicate_books(factory, name):
    h = factory()
    first = h.run(ROOT / name)
    before = h.books()
    second = h.run(ROOT / name)
    assert first['status'] == second['status'] == 'completed'
    assert second['counts']['loaded'] == 0
    assert second['counts']['updated'] == 0
    assert h.books() == before
    assert second['counts']['read'] == first['counts']['read']
    assert second['counts']['rejected'] == first['counts']['rejected']


def test_log_adds_runs_without_overwriting(factory):
    h = factory()
    path = h.input([book()])
    h.run(path)
    original = h.history()
    h.run(path)
    after = h.history()
    assert len(after) == 2 and after[:-1] == original


@pytest.mark.parametrize('name', ['books.csv','books-batch2.csv'])
def test_outcome_totals_equal_rows_read(factory, name):
    h = factory()
    run = h.run(ROOT / name)
    assert run['status'] == 'completed'
    for c in [run['counts']] + [f['counts'] for f in run['files']]:
        assert c['read'] == sum(c[k] for k in ('loaded','updated','skipped','rejected'))


@pytest.mark.parametrize('name', ['books.csv','books-batch2.csv'])
def test_two_empty_databases_give_same_catalog(factory, name):
    left, right = factory(), factory()
    left.run(ROOT / name)
    right.run(ROOT / name)
    # Compare book data, not run timestamps, temporary paths or SQLite file bytes.
    def catalog(h):
        return sorted(json.dumps({k:v for k,v in r.items() if k != 'id'},sort_keys=True)
                      for r in h.books())
    assert catalog(left) == catalog(right)


def test_changed_nonblank_value_updates_and_blank_does_not_erase(factory):
    h = factory()
    h.run(h.input([book()]))
    changed = outcome(h.run(h.input([book(average_rating='4.5')])), 'updated')
    assert changed['changes']['average_rating'] == {'old':'4.0','new':'4.5'}
    outcome(h.run(h.input([book(average_rating='  ')])), 'skipped')
    assert h.books()[0]['average_rating'] == '4.5'


def test_no_isbn_title_author_match_ignores_case_and_spaces(factory):
    h = factory()
    h.run(h.input([book('','12345')]))
    r = outcome(h.run(h.input([book('','12345',title=' EXAMPLE   TITLE ',authors='EXAMPLE AUTHOR')])), 'skipped')
    assert len(h.books()) == 1 and len(r['warnings']) == 1


@pytest.mark.parametrize('field', ['title','authors'])
def test_no_isbn_placeholder_identity_is_rejected(factory, field):
    h = factory()
    r = outcome(h.run(h.input([book('','12345', **{field:' Unknown '})])), 'rejected')
    assert h.books() == [] and r['next_action'] == IDENTITY_ACTION


def test_one_changed_title_warns_but_both_identity_fields_reject(factory):
    h = factory()
    h.run(h.input([book()]))
    r = outcome(h.run(h.input([book(title='A changed title')])), 'updated')
    assert len(r['warnings']) == 1
    assert h.books()[0]['title'] == 'A changed title'
    before = h.books()
    r = outcome(h.run(h.input([book(title='Another title',authors='Another author')])), 'rejected')
    assert r['next_action'] == CONFLICT_ACTION and h.books() == before


def test_supplier_id_does_not_merge_different_isbns(factory):
    h = factory()
    h.run(h.input([book()]))
    r = outcome(h.run(h.input([book('0439554934','9780439554930',title='Another book')])), 'loaded')
    assert len(h.books()) == 2 and len(r['warnings']) == 1


def test_broken_second_file_rolls_back_entire_run(factory):
    h = factory()
    good = h.input([book()])
    bad = h.home / 'broken.csv'
    bad.write_text(','.join(HEADERS)+'\n1,too,few\n',encoding='utf-8')
    run = h.run(good,bad)
    assert run['status'] == 'failed' and h.books() == []
    assert run['counts']['loaded'] == run['counts']['updated'] == 0
    assert run['counts']['read'] == run['counts']['rejected']
    assert all(r['next_action'] == FILE_ACTION for r in details(run))


def test_missing_header_fails_the_file(factory):
    h = factory()
    row = book()
    row.pop('image_url')
    run = h.run(h.input([row], headers=[c for c in HEADERS if c != 'image_url']))
    assert run['status'] == 'failed' and h.books() == []


def test_unreadable_log_preserves_catalog(factory):
    h = factory()
    path = h.input([book()])
    h.run(path)
    before = digest(h.db)
    h.log.write_text('{broken',encoding='utf-8')
    try:
        h.run(path)
    except (ValueError, json.JSONDecodeError):
        pass
    assert digest(h.db) == before
    assert h.log.read_text(encoding='utf-8') == '{broken'
