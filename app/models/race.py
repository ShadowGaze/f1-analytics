from app import db


class Race(db.Model):
    __tablename__ = "f1_races"

    season = db.Column(db.Integer,    primary_key=True)
    round = db.Column(db.Integer,    primary_key=True)
    race_name = db.Column(db.String(150))
    circuit_id = db.Column(
        db.String(50), db.ForeignKey("f1_circuits.circuit_id"))
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    url = db.Column(db.Text)

    def __repr__(self):
        return f"<Race {self.season} R{self.round} {self.race_name}>"
