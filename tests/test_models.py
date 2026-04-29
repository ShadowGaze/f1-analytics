import pytest
from datetime import date
from app import create_app, db
from app.models.driver import Driver
from app.models.circuit import Circuit
from app.models.constructor import Constructor
from app.models.race import Race
from app.models.standings import DriverStanding, ConstructorStanding


@pytest.fixture
def app_ctx():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


class TestDriverModel:
    def test_create_driver(self, app_ctx):
        d = Driver(driver_id="vettel", given_name="Sebastian",
                   family_name="Vettel", nationality="German", number=5, code="VET")
        db.session.add(d)
        db.session.commit()
        assert Driver.query.get("vettel") is not None

    def test_full_name_property(self, app_ctx):
        d = Driver(driver_id="leclerc", given_name="Charles",
                   family_name="Leclerc")
        assert d.full_name == "Charles Leclerc"

    def test_full_name_partial(self, app_ctx):
        d = Driver(driver_id="anon", given_name=None, family_name="Anon")
        assert d.full_name == "Anon"

    def test_driver_repr(self, app_ctx):
        d = Driver(driver_id="max", given_name="Max", family_name="Verstappen")
        assert "Max Verstappen" in repr(d)

    def test_driver_primary_key(self, app_ctx):
        d = Driver(driver_id="alonso", given_name="Fernando",
                   family_name="Alonso")
        db.session.add(d)
        db.session.commit()
        assert Driver.query.count() == 1


class TestCircuitModel:
    def test_create_circuit(self, app_ctx):
        c = Circuit(circuit_id="monza", circuit_name="Autodromo di Monza",
                    locality="Monza", country="Italy", lat=45.6156, lng=9.2811)
        db.session.add(c)
        db.session.commit()
        assert Circuit.query.get("monza") is not None

    def test_circuit_repr(self, app_ctx):
        c = Circuit(circuit_id="spa", circuit_name="Circuit de Spa")
        assert "Spa" in repr(c)


class TestConstructorModel:
    def test_create_constructor(self, app_ctx):
        c = Constructor(constructor_id="ferrari",
                        name="Ferrari", nationality="Italian")
        db.session.add(c)
        db.session.commit()
        assert Constructor.query.get("ferrari") is not None


class TestRaceModel:
    def test_create_race_with_circuit(self, app_ctx):
        db.session.add(Circuit(
            circuit_id="monaco", circuit_name="Circuit de Monaco",
            locality="Monte Carlo", country="Monaco"
        ))
        db.session.add(Race(
            season=2019, round=6, race_name="Monaco Grand Prix",
            circuit_id="monaco", date=date(2019, 5, 26)
        ))
        db.session.commit()
        r = Race.query.filter_by(season=2019, round=6).first()
        assert r is not None
        assert r.race_name == "Monaco Grand Prix"
        assert r.circuit.country == "Monaco"

    def test_race_composite_primary_key(self, app_ctx):
        db.session.add(Circuit(circuit_id="c1", circuit_name="C1",
                               locality="X", country="Y"))
        db.session.add(Race(season=2021, round=1,
                       race_name="R1", circuit_id="c1"))
        db.session.add(Race(season=2021, round=2,
                       race_name="R2", circuit_id="c1"))
        db.session.commit()
        assert Race.query.filter_by(season=2021).count() == 2


class TestStandingsModel:
    def test_driver_standing(self, app_ctx):
        db.session.add(Driver(driver_id="d1", given_name="A", family_name="B"))
        db.session.add(DriverStanding(
            season=2022, position=1, points=454, wins=15,
            driver_id="d1", constructor="Red Bull"
        ))
        db.session.commit()
        s = DriverStanding.query.filter_by(season=2022, driver_id="d1").first()
        assert s.position == 1
        assert s.points == 454

    def test_constructor_standing(self, app_ctx):
        db.session.add(Constructor(constructor_id="rb", name="Red Bull"))
        db.session.add(ConstructorStanding(
            season=2022, position=1, points=759, wins=17,
            constructor_id="rb", constructor="Red Bull"
        ))
        db.session.commit()
        s = ConstructorStanding.query.filter_by(
            season=2022, constructor_id="rb").first()
        assert s.wins == 17

    def test_driver_standing_relationship(self, app_ctx):
        db.session.add(Driver(driver_id="d2", given_name="X", family_name="Y"))
        db.session.add(DriverStanding(
            season=2023, position=2, points=200, wins=3,
            driver_id="d2", constructor="Ferrari"
        ))
        db.session.commit()
        drv = Driver.query.get("d2")
        assert drv.standings.count() == 1
