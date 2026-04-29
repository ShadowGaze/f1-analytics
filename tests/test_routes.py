import pytest
from app import create_app, db
from app.models.driver import Driver
from app.models.circuit import Circuit
from app.models.constructor import Constructor
from app.models.race import Race
from app.models.standings import DriverStanding, ConstructorStanding
from datetime import date


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()

        # Seed minimal test data
        db.session.add(Driver(
            driver_id="hamilton", given_name="Lewis", family_name="Hamilton",
            nationality="British", number=44, code="HAM",
            dob=date(1985, 1, 7)
        ))
        db.session.add(Circuit(
            circuit_id="silverstone", circuit_name="Silverstone Circuit",
            locality="Silverstone", country="UK",
            lat=52.0786, lng=-1.0169
        ))
        db.session.add(Constructor(
            constructor_id="mercedes", name="Mercedes", nationality="German"
        ))
        db.session.add(Race(
            season=2020, round=1, race_name="British Grand Prix",
            circuit_id="silverstone", date=date(2020, 8, 2)
        ))
        db.session.add(DriverStanding(
            season=2020, position=1, points=347, wins=11, driver_id="hamilton",
            constructor="Mercedes"
        ))
        db.session.add(ConstructorStanding(
            season=2020, position=1, points=573, wins=13,
            constructor_id="mercedes", constructor="Mercedes"
        ))
        db.session.commit()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()

# ── Main ──────────────────────────────────────────────────


class TestMain:
    def test_homepage_loads(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_homepage_contains_branding(self, client):
        r = client.get("/")
        assert b"F1" in r.data

# ── Drivers ───────────────────────────────────────────────


class TestDrivers:
    def test_drivers_list(self, client):
        r = client.get("/drivers/")
        assert r.status_code == 200
        assert b"Hamilton" in r.data

    def test_driver_detail(self, client):
        r = client.get("/drivers/hamilton")
        assert r.status_code == 200
        assert b"Lewis" in r.data

    def test_driver_not_found(self, client):
        r = client.get("/drivers/nonexistent-driver-xyz")
        assert r.status_code == 404

    def test_driver_search(self, client):
        r = client.get("/drivers/?q=hamilton")
        assert r.status_code == 200
        assert b"Hamilton" in r.data

    def test_driver_nationality_filter(self, client):
        r = client.get("/drivers/?nationality=British")
        assert r.status_code == 200
        assert b"Hamilton" in r.data

# ── Circuits ──────────────────────────────────────────────


class TestCircuits:
    def test_circuits_list(self, client):
        r = client.get("/circuits/")
        assert r.status_code == 200
        assert b"Silverstone" in r.data

    def test_circuit_detail(self, client):
        r = client.get("/circuits/silverstone")
        assert r.status_code == 200
        assert b"Silverstone" in r.data

    def test_circuit_not_found(self, client):
        r = client.get("/circuits/no-such-circuit")
        assert r.status_code == 404

# ── Constructors ──────────────────────────────────────────


class TestConstructors:
    def test_constructors_list(self, client):
        r = client.get("/constructors/")
        assert r.status_code == 200
        assert b"Mercedes" in r.data

    def test_constructor_detail(self, client):
        r = client.get("/constructors/mercedes")
        assert r.status_code == 200
        assert b"Mercedes" in r.data

    def test_constructor_not_found(self, client):
        r = client.get("/constructors/no-such-team")
        assert r.status_code == 404

# ── Races ─────────────────────────────────────────────────


class TestRaces:
    def test_races_list(self, client):
        r = client.get("/races/")
        assert r.status_code == 200
        assert b"British Grand Prix" in r.data

    def test_race_detail(self, client):
        r = client.get("/races/2020/1")
        assert r.status_code == 200
        assert b"British Grand Prix" in r.data

    def test_race_not_found(self, client):
        r = client.get("/races/1800/99")
        assert r.status_code == 404

    def test_races_season_filter(self, client):
        r = client.get("/races/?season=2020")
        assert r.status_code == 200
        assert b"British Grand Prix" in r.data

# ── Analysis ──────────────────────────────────────────────


class TestAnalysis:
    def test_analysis_page(self, client):
        r = client.get("/analysis/")
        assert r.status_code == 200

    def test_chart_wins_returns_png(self, client):
        r = client.get("/analysis/chart/wins")
        assert r.status_code == 200
        assert r.content_type == "image/png"

    def test_chart_races_per_season(self, client):
        r = client.get("/analysis/chart/races-per-season")
        assert r.status_code == 200
        assert r.content_type == "image/png"

    def test_chart_driver_nationalities(self, client):
        r = client.get("/analysis/chart/driver-nationalities")
        assert r.status_code == 200
        assert r.content_type == "image/png"

    def test_chart_constructor_nationalities(self, client):
        r = client.get("/analysis/chart/constructor-nationalities")
        assert r.status_code == 200
        assert r.content_type == "image/png"

    def test_chart_season_drivers(self, client):
        r = client.get("/analysis/chart/season-drivers/2020")
        assert r.status_code == 200
        assert r.content_type == "image/png"

    def test_chart_season_constructors(self, client):
        r = client.get("/analysis/chart/season-constructors/2020")
        assert r.status_code == 200
        assert r.content_type == "image/png"

    def test_chart_top_constructors(self, client):
        r = client.get("/analysis/chart/top-constructors")
        assert r.status_code == 200
        assert r.content_type == "image/png"

# ── Error Handlers ────────────────────────────────────────


class TestErrors:
    def test_404_returns_html(self, client):
        r = client.get("/this-page-does-not-exist-at-all")
        assert r.status_code == 404
        assert b"404" in r.data
