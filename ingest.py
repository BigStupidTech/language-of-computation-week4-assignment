"""Offline book ingestion governed by the shared rules.md."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import sys

HEADERS = 'book_id,goodreads_book_id,best_book_id,work_id,books_count,isbn,isbn13,authors,original_publication_year,original_title,title,language_code,average_rating,ratings_count,work_ratings_count,work_text_reviews_count,ratings_1,ratings_2,ratings_3,ratings_4,ratings_5,image_url,small_image_url'.split(',')
ISBN_ACTION = 'Find the correct ISBN, correct the row, and load the file again.'
CONFLICT_ACTION = 'Check which value or book is correct.'
IDENTITY_ACTION = 'Supply an identifying title and author, then load the file again.'
FILE_ACTION = 'Correct the file error and rerun the files.'
SCI = re.compile(r'[+-]?[0-9]+(?:\.[0-9]+)?[eE][+-]?[0-9]+')
DEC = re.compile(r'[+-]?[0-9]+\.[0-9]+')


def norm(value):
    return ' '.join(value.split()).casefold()


def valid10(s):
    return bool(re.fullmatch(r'[0-9]{9}[0-9X]', s)) and sum((10-i)*(10 if c == 'X' else int(c)) for i,c in enumerate(s)) % 11 == 0


def valid13(s):
    return bool(re.fullmatch(r'(978|979)[0-9]{10}', s)) and sum(int(c)*(1 if i%2 == 0 else 3) for i,c in enumerate(s)) % 10 == 0


def to13(s):
    stem = '978' + s[:9]
    return stem + str(-sum(int(c)*(1 if i%2 == 0 else 3) for i,c in enumerate(stem)) % 10)


def to10(s):
    if not s.startswith('978'):
        return None
    stem = s[3:12]
    check = -sum((10-i)*int(c) for i,c in enumerate(stem)) % 11
    return stem + ('X' if check == 10 else str(check))


def isbn_fields(raw):
    a0,b0 = raw['isbn'],raw['isbn13']
    repair = Counter()
    warnings, errors = [], []
    def error(message, action=ISBN_ACTION):
        errors.append((message,action))
    def clean(value, column):
        s = value.strip()
        if not s:
            return ''
        if SCI.fullmatch(s) or DEC.fullmatch(s):
            if column == 'isbn':
                error('Numeric notation is not permitted in isbn')
            return s
        if s.startswith(('+','-')):
            error(column + ': leading sign is invalid')
            return s
        out = re.sub(r'\s|-','',s).replace('x','X')
        if out != value:
            repair['formatting'] += 1
        return out
    a,b = clean(a0,'isbn'),clean(b0,'isbn13')
    if not a and not b:
        error('Both incoming ISBN fields are blank')
    # Moving a full ISBN-13 precedes scientific-notation confirmation.
    moved = False
    if valid13(a):
        if b and b != a:
            error('Moved ISBN-13 conflicts with destination value',CONFLICT_ACTION)
        else:
            b = a
            a = to10(b) or ''
            repair['move'] += 1
            if a:
                repair['missing_equivalent'] += 1
            moved = True
    good_a = False
    if a:
        if valid10(a):
            good_a = True
        elif not SCI.fullmatch(a) and not DEC.fullmatch(a):
            if not re.fullmatch(r'[0-9]*[0-9X]',a):
                error('isbn contains illegal characters')
            elif len(a) == 10:
                error('isbn has a bad checksum')
            elif 2 <= len(a) <= 9 and valid10(a.zfill(10)):
                a = a.zfill(10)
                good_a = True
                repair['leading_zero'] += 1
            else:
                error('isbn has invalid length or failed padding check')
    stored_b = None
    fallback = False
    if SCI.fullmatch(b):
        if good_a:
            full = to13(a)
            # Thirteen digits rounded to twelve significant digits means tens.
            rounded = Decimal(full).quantize(Decimal('1E1'),rounding=ROUND_HALF_EVEN)
            if rounded == Decimal(b):
                stored_b = full
                repair['scientific_notation'] += 1
            else:
                error('Scientific ISBN-13 does not confirm ISBN-10',CONFLICT_ACTION)
        elif not a:
            fallback = True
            warnings.append('Unconfirmed scientific ISBN-13; loaded without ISBNs')
    elif DEC.fullmatch(b):
        fallback = True
        warnings.append('isbn13 contains another code; left blank')
    elif b:
        if not re.fullmatch(r'[0-9]+',b):
            error('isbn13 contains illegal characters')
        elif len(b) != 13 or b[:3] not in ('978','979'):
            fallback = True
            warnings.append('isbn13 contains another code; left blank')
        elif not valid13(b):
            error('isbn13 has a bad checksum')
        else:
            stored_b = b
    elif good_a and not moved:
        stored_b = to13(a)
        repair['missing_equivalent'] += 1
    if good_a and stored_b and to13(a) != stored_b:
        error('The two ISBNs identify different books',CONFLICT_ACTION)
    if not a and stored_b:
        a = to10(stored_b) or ''
        good_a = bool(a)
        if a:
            repair['missing_equivalent'] += 1
    stored_a = a if good_a else None
    # Field-local invalidity always rejects; do not turn it into a fallback.
    if errors:
        return stored_a,stored_b,repair,warnings,errors
    if not stored_a and not stored_b and fallback:
        forbidden = {'unknown','untitled','untitled manuscript',''}
        if norm(raw['title']) in forbidden or norm(raw['authors']) in forbidden:
            error('No usable ISBN and missing or placeholder identity',IDENTITY_ACTION)
    return stored_a,stored_b,repair,warnings,errors


def counts():
    return dict(read=0,loaded=0,updated=0,skipped=0,rejected=0,warning_rows=0,repair_rows=0)


def save_log(path,history):
    temporary = path.with_suffix('.json.tmp')
    with temporary.open('w',encoding='utf-8') as f:
        json.dump(history,f,ensure_ascii=False,indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary,path)


class Catalog:
    def __init__(self,db):
        self.db = db
        self.rows = {r['id']:dict(r) for r in db.execute('SELECT * FROM books')}
        self.isbns,self.names,self.suppliers = defaultdict(set),defaultdict(set),defaultdict(set)
        for row in self.rows.values():
            self.index(row,True)
    def key(self,row):
        return row['isbn13'] or (to13(row['isbn']) if row['isbn'] else None)
    def index(self,row,add):
        key = self.key(row)
        pairs = [(self.names,(norm(row['title']),norm(row['authors']))),(self.suppliers,row['book_id'])]
        if key:
            pairs.append((self.isbns,key))
        for mapping,k in pairs:
            if add:
                mapping[k].add(row['id'])
            else:
                mapping[k].discard(row['id'])
    def accept(self,raw,a,b,result):
        incoming = dict(raw,isbn=a,isbn13=b)
        key = self.key(incoming)
        name = (norm(raw['title']),norm(raw['authors']))
        matches = set(self.isbns.get(key,())) if key else set()
        if not matches:
            name_matches = self.names.get(name,())
            matches = {i for i in name_matches if not key or not self.key(self.rows[i])}
        if len(matches) > 1:
            return [('Several books match the incoming identity',CONFLICT_ACTION)]
        existing = self.rows[next(iter(matches))] if matches else None
        if existing and key and self.key(existing) and key != self.key(existing):
            return [('Different usable ISBN identity',CONFLICT_ACTION)]
        if existing and key and self.key(existing):
            differences = [c for c in ('title','authors') if norm(raw[c]) != norm(existing[c])]
            if len(differences) == 2:
                return [('Both title and author differ for the same ISBN',CONFLICT_ACTION)]
            if differences:
                result['warnings'].append('One title/author field differs for the same ISBN')
        other_ids = self.suppliers.get(raw['book_id'],set()) - ({existing['id']} if existing else set())
        if other_ids:
            result['warnings'].append('Supplier ID also occurs on a different book')
        if existing:
            updated = dict(existing)
            for c in HEADERS:
                v = incoming[c]
                if v is None or not v.strip():
                    continue
                if c in ('title','authors') and norm(v) == norm(existing[c]):
                    continue
                if v != existing[c]:
                    result['changes'][c] = dict(old=existing[c],new=v)
                    updated[c] = v
            if result['changes']:
                self.db.execute('UPDATE books SET '+','.join('"'+c+'"=?' for c in HEADERS)+' WHERE id=?',[updated[c] for c in HEADERS]+[existing['id']])
                self.index(existing,False)
                self.rows[existing['id']] = updated
                self.index(updated,True)
            result.update(outcome='updated' if result['changes'] else 'skipped',reason='Existing book updated' if result['changes'] else 'Already exists; unchanged')
        else:
            cols = ','.join('"'+c+'"' for c in HEADERS)
            cur = self.db.execute('INSERT INTO books ('+cols+') VALUES ('+','.join('?' for _ in HEADERS)+')',[incoming[c] for c in HEADERS])
            incoming['id'] = cur.lastrowid
            self.rows[incoming['id']] = incoming
            self.index(incoming,True)
            result.update(outcome='loaded',reason='Inserted new book')
        return []


def run(paths,home):
    home = Path(home)
    logpath = home/'ingestion-log.json'
    history = json.loads(logpath.read_text(encoding='utf-8')) if logpath.exists() else []
    if not isinstance(history,list) or any(not isinstance(r,dict) for r in history):
        raise ValueError('Existing log is not an array of run entries; no changes made')
    db = sqlite3.connect(home/'books.db')
    db.row_factory = sqlite3.Row
    try:
        existing_columns = [r['name'] for r in db.execute('PRAGMA table_info(books)')]
        if existing_columns and not set(HEADERS).issubset(existing_columns):
            raise ValueError('Existing database has the old schema. Use a fresh week4 database after saving any needed results.')
        db.execute('CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY,'+','.join('"'+c+'" TEXT' for c in HEADERS)+')')
        db.execute('CREATE TABLE IF NOT EXISTS run_history (id INTEGER PRIMARY KEY,entry TEXT NOT NULL)')
        db.commit()
        for old in db.execute('SELECT entry FROM run_history ORDER BY id'):
            entry = json.loads(old[0])
            if entry not in history:
                history.append(entry)
        result = dict(when=datetime.now(timezone.utc).isoformat(),status='completed',files=[],counts=counts(),book_count_before=db.execute('SELECT count(*) FROM books').fetchone()[0])
        prepared = []
        current = None
        try:
            # Validate all file structures before changing the catalog.
            for path in paths:
                path = Path(path)
                current = dict(file=str(path.resolve()),sha256=None,counts=counts(),rows=[])
                result['files'].append(current)
                rawbytes = path.read_bytes()
                current['sha256'] = hashlib.sha256(rawbytes).hexdigest()
                reader = csv.reader(io.StringIO(rawbytes.decode('utf-8-sig'),newline=''),strict=True)
                current['stopped_at_record'] = 1
                header = next(reader,None)
                if not header or len(header) != len(HEADERS) or set(header) != set(HEADERS):
                    raise ValueError('Missing, duplicate or unexpected CSV headers')
                records = []
                prepared.append((current,records))
                number = 1
                while True:
                    current['stopped_at_record'] = number+1
                    fields = next(reader,None)
                    if fields is None:
                        break
                    number += 1
                    if not fields:
                        continue
                    if len(fields) != len(header):
                        raise ValueError('Wrong CSV field count')
                    records.append((number,dict(zip(header,fields))))
                    current['counts']['read'] += 1
                current.pop('stopped_at_record',None)
            db.execute('BEGIN')
            catalog = Catalog(db)
            for item,records in prepared:
                current = item
                for number,raw in records:
                    current['stopped_at_record'] = number
                    a,b,repairs,warnings,errors = isbn_fields(raw)
                    row = dict(record=number,supplier_id=raw['book_id'],title=raw['title'],interpreted={'isbn':a,'isbn13':b},warnings=warnings,repair_counts=dict(repairs),changes={},outcome=None,reason='',next_action='')
                    item['rows'].append(row)
                    if not errors:
                        errors = catalog.accept(raw,a,b,row)
                    if errors:
                        # Rejected table examples name no completed repairs or warnings.
                        row.update(outcome='rejected',reason='; '.join(dict.fromkeys(e[0] for e in errors)),next_action=errors[0][1],warnings=[],repair_counts={})
                        row['problems'] = [dict(reason=why,next_action=action) for why,action in errors]
                    elif row['warnings']:
                        row['next_action'] = 'Review the warning and confirm the book information.'
                    if row['warnings'] or row['outcome']=='rejected' or row['changes']:
                        row['raw'] = raw
                current.pop('stopped_at_record',None)
        except Exception as exc:
            db.rollback()
            result.update(status='failed',error=str(exc))
            if current is not None:
                current['error'] = str(exc)
                current['next_action'] = FILE_ACTION
                result['error_file'] = current['file']
                result['error_record'] = current.get('stopped_at_record')
            for item,records in prepared:
                item['rows'] = [dict(record=n,supplier_id=r['book_id'],title=r['title'],raw=r,interpreted={},warnings=[],repair_counts={},changes={},outcome='rejected',reason='Run rolled back: '+str(exc),next_action=FILE_ACTION) for n,r in records]
        for item in result['files']:
            rc,wc = Counter(),Counter()
            reasons = Counter()
            for row in item['rows']:
                item['counts'][row['outcome']] += 1
                item['counts']['warning_rows'] += bool(row['warnings'])
                item['counts']['repair_rows'] += bool(row['repair_counts'])
                rc.update(row['repair_counts'])
                wc.update(row['warnings'])
                if row['outcome']=='rejected':
                    reasons.update(p['reason'] for p in row.get('problems',[{'reason':row['reason']}]))
            item.update(repair_counts=dict(rc),warning_counts=dict(wc),rejection_counts=dict(reasons))
            for k,v in item['counts'].items():
                result['counts'][k] += v
        for name in ('repair_counts','warning_counts','rejection_counts'):
            combined = Counter()
            for item in result['files']:
                combined.update(item[name])
            result[name] = dict(combined)
        c = result['counts']
        result['totals_match'] = c['read'] == sum(c[k] for k in ('loaded','updated','skipped','rejected'))
        result['verdict'] = 'Failed' if result['status']=='failed' else ('Some rows need attention' if c['rejected'] else 'Completed')
        result['book_count_after'] = db.execute('SELECT count(*) FROM books').fetchone()[0]
        db.execute('INSERT INTO run_history(entry) VALUES (?)',(json.dumps(result,ensure_ascii=False),))
        db.commit()
        history.append(result)
        save_log(logpath,history)
        print(json.dumps({k:v for k,v in result.items() if k not in ('files','rejection_counts','warning_counts')},indent=2))
        return 0 if result['status']=='completed' else 1
    finally:
        db.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files',nargs='+',type=Path)
    args = parser.parse_args()
    try:
        sys.exit(run(args.files,Path(__file__).resolve().parent))
    except Exception as exc:
        print('Stopped: '+str(exc),file=sys.stderr)
        sys.exit(1)
