import re
import sqlite3
import unicodedata

from flask import Flask, g, jsonify, request
from werkzeug.exceptions import abort

DATABASE = 'data.sqlite'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = make_dicts
    return db


def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


app = Flask(__name__)


# noinspection PyUnusedLocal
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# noinspection PyUnusedLocal
@app.errorhandler(422)
def missing_parameter(error):
    return jsonify({'message': 'missing address parameter'}), 422


@app.route('/', methods=['GET'])
def postal_code():
    query_parameters = request.args
    address = query_parameters.get('address')

    if address:
        address = re.sub(r'[\u0300-\u036f]', '',
                         unicodedata.normalize('NFD', address), re.UNICODE)
        ad_re = re.compile(r'(\w+)\s*(\d*)\s*(\w+)\s*(\w*)\s*(\w*)')
        m = ad_re.search(address.upper())

        if m.group(4):
            city = m.group(4)
            street = m.group(3)
        else:
            city = m.group(3)
            street = m.group(1)

        number = m.group(2)
        prefecture = m.group(5)

        # Check if city is in ΑΤΤΙΚΗ area
        if query_db('select * from `ΤΚ-ΑΤΤΙΚΗΣ` where `ΠΟΛΗ` like ?',
                    ['%' + city + '%'], one=True):

            pc = query_db('select * from `ΤΚ-ΑΤΤΙΚΗΣ` where `ΠΟΛΗ` like ? AND `ΟΔΟΣ_ΧΩΡΙΟ` like ?',
                          [city + '%', street + '%'])
            if len(pc) > 1:
                for a in pc:
                    ranges = a['ΑΡΙΘΜΟΣ'].split()
                    for r in ranges:
                        st_end = r.split('-')
                        if st_end[-1] == 'ΤΕΛ':
                            if int(number) >= int(st_end[0]):
                                return jsonify({'TK': a['ΤΚ']})
                        else:
                            if int(st_end[0]) <= int(number) <= int(st_end[1]):
                                return jsonify({'TK': a['ΤΚ']})
            else:
                return jsonify({'TK': pc[0]['ΤΚ']})
        # Check if city is in ΘΕΣΣΑΛΟΝΙΚΗ area
        elif query_db('select * from `ΤΚ-ΘΕΣΣΑΛΟΝΙΚΗΣ` where `ΠΟΛΗ` like ?',
                      ['%' + city + '%'], one=True):

            pc = query_db('select * from `ΤΚ-ΘΕΣΣΑΛΟΝΙΚΗΣ` where `ΠΟΛΗ` like ? AND `ΟΔΟΣ_ΧΩΡΙΟ` like ?',
                          [city + '%', street + '%'])
            if len(pc) > 1:
                for a in pc:
                    ranges = a['ΑΡΙΘΜΟΣ'].split()
                    for r in ranges:
                        st_end = r.split('-')
                        if st_end[-1] == 'ΤΕΛ':
                            if int(number) >= int(st_end[0]):
                                return jsonify({'TK': a['ΤΚ']})
                        else:
                            if int(st_end[0]) <= int(number) <= int(st_end[1]):
                                return jsonify({'TK': a['ΤΚ']})
            else:
                return jsonify({'TK': pc[0]['ΤΚ']})
        # Search for postal code in ΛΟΙΠΗ_ΕΛΛΑΣ
        else:
            if query_db('select * from `ΤΚ-ΛΟΙΠΗ_ΕΛΛΑΣ` where `ΝΟΜΟΣ` like ?',
                        ['%' + city + '%'], one=True):
                prefecture = city
                city = street

                pc = query_db(
                    'select * from `ΤΚ-ΛΟΙΠΗ_ΕΛΛΑΣ` where `ΠΟΛΗ` like ? AND `ΟΔΟΣ_ΧΩΡΙΟ` like ? AND `ΝΟΜΟΣ` like ?',
                    [city + '%', street + '%', prefecture + '%'])
            else:
                if prefecture:
                    pc = query_db(
                        'select * from `ΤΚ-ΛΟΙΠΗ_ΕΛΛΑΣ` where `ΠΟΛΗ` like ? AND `ΟΔΟΣ_ΧΩΡΙΟ` like ? AND `ΝΟΜΟΣ` like ?',
                        [city + '%', street + '%', prefecture + '%'])
                else:
                    pc = query_db('select * from `ΤΚ-ΛΟΙΠΗ_ΕΛΛΑΣ` where `ΠΟΛΗ` like ? AND `ΟΔΟΣ_ΧΩΡΙΟ` like ?',
                                  [city + '%', street + '%'])
            if len(pc) > 1:
                for a in pc:
                    ranges = a['ΑΡΙΘΜΟΣ'].split()
                    for r in ranges:
                        st_end = r.split('-')
                        if st_end[-1] == 'ΤΕΛ':
                            if int(number) >= int(st_end[0]):
                                return jsonify({'TK': a['ΤΚ']})
                        else:
                            if int(st_end[0]) <= int(number) <= int(st_end[1]):
                                return jsonify({'TK': a['ΤΚ']})
            elif len(pc) == 0:
                return jsonify({'TK': 'NOT FOUND'})
            else:
                return jsonify({'TK': pc[0]['ΤΚ']})

        return jsonify({'TK': 'NOT FOUND'})
    else:
        return abort(422)


if __name__ == '__main__':
    app.run()
