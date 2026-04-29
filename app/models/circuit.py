from app import db


class Circuit(db.Model):
    __tablename__ = "f1_circuits"

    circuit_id = db.Column(db.String(50),   primary_key=True)
    circuit_name = db.Column(db.String(150))
    locality = db.Column(db.String(100))
    country = db.Column(db.String(100))
    lat = db.Column(db.Numeric(9, 6))
    lng = db.Column(db.Numeric(9, 6))
    url = db.Column(db.Text)

    races = db.relationship("Race", backref="circuit", lazy="dynamic")

    def __repr__(self):
        return f"<Circuit {self.circuit_name}>"
