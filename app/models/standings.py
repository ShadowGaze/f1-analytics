from app import db


class DriverStanding(db.Model):
    __tablename__ = "f1_driver_standings"

    season = db.Column(db.Integer,    primary_key=True)
    position = db.Column(db.Integer)
    points = db.Column(db.Integer)
    wins = db.Column(db.Integer)
    driver_id = db.Column(db.String(50), db.ForeignKey(
        "f1_drivers.driver_id"), primary_key=True)
    constructor = db.Column(db.String(100))

    def __repr__(self):
        return f"<DriverStanding {self.season} {self.driver_id} P{self.position}>"


class ConstructorStanding(db.Model):
    __tablename__ = "f1_constructor_standings"

    season = db.Column(db.Integer,    primary_key=True)
    position = db.Column(db.Integer)
    points = db.Column(db.Integer)
    wins = db.Column(db.Integer)
    constructor_id = db.Column(db.String(50), db.ForeignKey(
        "f1_constructors.constructor_id"), primary_key=True)
    constructor = db.Column(db.String(100))

    def __repr__(self):
        return f"<ConstructorStanding {self.season} {self.constructor_id} P{self.position}>"
