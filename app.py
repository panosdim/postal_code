import re
import sqlite3
import unicodedata
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from flask import Flask, g, jsonify, request
from werkzeug.exceptions import abort

DATABASE = "data.sqlite"


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = make_dicts
    return db


def make_dicts(cursor: sqlite3.Cursor, row: Any) -> Dict[str, Any]:
    return dict((cursor.description[idx][0], value) for idx, value in enumerate(row))


def query_db(
    query: str, args: Union[Tuple[Any, ...], List[Any]] = (), one: bool = False
) -> Union[List[Dict[str, Any]], Dict[str, Any], None]:
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


app = Flask(__name__)


@app.teardown_appcontext
def close_connection(exception: Optional[BaseException]) -> None:
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@app.errorhandler(422)
def missing_parameter(error: Any) -> Tuple[Any, int]:
    return jsonify({"message": "missing address parameter"}), 422


@app.route("/", methods=["GET"])
def postal_code():
    query_parameters = request.args
    address = query_parameters.get("address")

    if address:
        address = re.sub(
            r"[\u0300-\u036f]", "", unicodedata.normalize("NFD", address), re.UNICODE
        )
        ad_re = re.compile(r"(\w+)\s*(\d*)\s*(\w+)\s*(\w*)\s*(\w*)")
        m = ad_re.search(address.upper())

        if m is None:
            return jsonify({"TK": "NOT FOUND"})

        if m.group(4):
            city = m.group(4)
            street = m.group(3)
        else:
            city = m.group(3)
            street = m.group(1)

        number = m.group(2)
        prefecture = m.group(5)

        # Check if city is in ΑΤΤΙΚΗ area
        if query_db(
            "select * from `ΤΚ-ΑΤΤΙΚΗΣ` where `ΠΟΛΗ` like ?",
            ["%" + city + "%"],
            one=True,
        ):
            pc_result = query_db(
                "select * from `ΤΚ-ΑΤΤΙΚΗΣ` where `ΠΟΛΗ` like ? AND `ΟΔΟΣ_ΧΩΡΙΟ` like ?",
                [city + "%", street + "%"],
            )
            if pc_result is not None:
                pc = cast(List[Dict[str, Any]], pc_result)
                if len(pc) > 1:
                    for a in pc:
                        ranges = a["ΑΡΙΘΜΟΣ"].split()
                        for r in ranges:
                            st_end = r.split("-")
                            if st_end[-1] == "ΤΕΛ":
                                if int(number) >= int(st_end[0]):
                                    return jsonify({"TK": a["ΤΚ"]})
                            else:
                                if int(st_end[0]) <= int(number) <= int(st_end[1]):
                                    return jsonify({"TK": a["ΤΚ"]})
                elif len(pc) == 1:
                    return jsonify({"TK": pc[0]["ΤΚ"]})
        # Check if city is in ΘΕΣΣΑΛΟΝΙΚΗ area
        elif query_db(
            "select * from `ΤΚ-ΘΕΣΣΑΛΟΝΙΚΗΣ` where `ΠΟΛΗ` like ?",
            ["%" + city + "%"],
            one=True,
        ):
            pc_result = query_db(
                "select * from `ΤΚ-ΘΕΣΣΑΛΟΝΙΚΗΣ` where `ΠΟΛΗ` like ? AND `ΟΔΟΣ_ΧΩΡΙΟ` like ?",
                [city + "%", street + "%"],
            )
            if pc_result is not None:
                pc = cast(List[Dict[str, Any]], pc_result)
                if len(pc) > 1:
                    for a in pc:
                        ranges = a["ΑΡΙΘΜΟΣ"].split()
                        for r in ranges:
                            st_end = r.split("-")
                            if st_end[-1] == "ΤΕΛ":
                                if int(number) >= int(st_end[0]):
                                    return jsonify({"TK": a["ΤΚ"]})
                            else:
                                if int(st_end[0]) <= int(number) <= int(st_end[1]):
                                    return jsonify({"TK": a["ΤΚ"]})
                elif len(pc) == 1:
                    return jsonify({"TK": pc[0]["ΤΚ"]})
        # Search for postal code in ΛΟΙΠΗ_ΕΛΛΑΣ
        else:
            pc_result = None
            if query_db(
                "select * from `ΤΚ-ΛΟΙΠΗ_ΕΛΛΑΣ` where `ΝΟΜΟΣ` like ?",
                ["%" + city + "%"],
                one=True,
            ):
                prefecture = city
                city = street

                pc_result = query_db(
                    "select * from `ΤΚ-ΛΟΙΠΗ_ΕΛΛΑΣ` where `ΠΟΛΗ` like ? AND `ΟΔΟΣ_ΧΩΡΙΟ` like ? AND `ΝΟΜΟΣ` like ?",
                    [city + "%", street + "%", prefecture + "%"],
                )
            else:
                if prefecture:
                    pc_result = query_db(
                        "select * from `ΤΚ-ΛΟΙΠΗ_ΕΛΛΑΣ` where `ΠΟΛΗ` like ? AND `ΟΔΟΣ_ΧΩΡΙΟ` like ? AND `ΝΟΜΟΣ` like ?",
                        [city + "%", street + "%", prefecture + "%"],
                    )
                else:
                    pc_result = query_db(
                        "select * from `ΤΚ-ΛΟΙΠΗ_ΕΛΛΑΣ` where `ΠΟΛΗ` like ? AND `ΟΔΟΣ_ΧΩΡΙΟ` like ?",
                        [city + "%", street + "%"],
                    )
            if pc_result is not None:
                pc = cast(List[Dict[str, Any]], pc_result)
                if len(pc) > 1:
                    for a in pc:
                        ranges = a["ΑΡΙΘΜΟΣ"].split()
                        for r in ranges:
                            st_end = r.split("-")
                            if st_end[-1] == "ΤΕΛ":
                                if int(number) >= int(st_end[0]):
                                    return jsonify({"TK": a["ΤΚ"]})
                            else:
                                if int(st_end[0]) <= int(number) <= int(st_end[1]):
                                    return jsonify({"TK": a["ΤΚ"]})
                elif len(pc) == 1:
                    return jsonify({"TK": pc[0]["ΤΚ"]})
                else:
                    return jsonify({"TK": "NOT FOUND"})

        return jsonify({"TK": "NOT FOUND"})
    else:
        return abort(422)


if __name__ == "__main__":
    app.run()
