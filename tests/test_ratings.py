import io
import json

import pytest

from codemix_bench.ratings import CONDITIONS, Store, ValidationError, make_app, validate
from codemix_bench.schemas import RUBRIC_KEYS

GOOD = {"rater": "r1", "persona": "te01", "scenario": "s02_recipe", "condition": "profile",
        "scores": {k: 4 for k in RUBRIC_KEYS}}


def call(app, method, path, body=None):
    raw = json.dumps(body).encode() if body is not None else b""
    env = {"REQUEST_METHOD": method, "PATH_INFO": path, "CONTENT_LENGTH": str(len(raw)), "wsgi.input": io.BytesIO(raw)}
    out = {}
    res = b"".join(app(env, lambda s, h: out.update(status=s)))
    return out["status"], json.loads(res)


@pytest.fixture
def app():
    return make_app(Store(), [{"persona": "te01", "scenario": "s02_recipe", "condition": "bare", "user": "u", "response": "r"}])


def test_validate_accepts_good_and_rejects_bad():
    assert validate(GOOD)["rater"] == "r1"
    for mutate in (lambda d: d.pop("rater"), lambda d: d.update(condition="x"),
                   lambda d: d["scores"].update(helpfulness=6), lambda d: d["scores"].update(helpfulness=True),
                   lambda d: d["scores"].pop("helpfulness"), lambda d: d.update(rater="  ")):
        bad = json.loads(json.dumps(GOOD))
        mutate(bad)
        with pytest.raises(ValidationError):
            validate(bad)


def test_health_and_cells(app):
    assert call(app, "GET", "/api/health") == ("200 OK", {"ok": True})
    assert len(call(app, "GET", "/api/cells")[1]["cells"]) == 1


def test_post_rating_and_summary(app):
    assert call(app, "POST", "/api/ratings", GOOD)[0] == "201 Created"
    s = call(app, "GET", "/api/summary")[1]
    assert s["profile"]["n"] == 1 and s["profile"]["mean"]["helpfulness"] == 4 and s["bare"]["n"] == 0


def test_same_rater_updates_instead_of_duplicating(app):
    call(app, "POST", "/api/ratings", GOOD)
    call(app, "POST", "/api/ratings", {**GOOD, "scores": {k: 2 for k in RUBRIC_KEYS}})
    s = call(app, "GET", "/api/summary")[1]
    assert s["profile"]["n"] == 1 and s["profile"]["mean"]["helpfulness"] == 2


def test_bad_post_is_400_and_unknown_is_404(app):
    assert call(app, "POST", "/api/ratings", {"rater": "x"})[0] == "400 Bad Request"
    assert call(app, "GET", "/api/nope")[0] == "404 Not Found"


def test_malformed_json_is_400(app):
    env = {"REQUEST_METHOD": "POST", "PATH_INFO": "/api/ratings", "CONTENT_LENGTH": "5", "wsgi.input": io.BytesIO(b"{oops")}
    out = {}
    b"".join(app(env, lambda s, h: out.update(status=s)))
    assert out["status"] == "400 Bad Request"


def test_conditions_constant():
    assert CONDITIONS == ("bare", "profile")
