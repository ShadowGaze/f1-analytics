from app import db


class Driver(db.Model):
    __tablename__ = "f1_drivers"

    driver_id = db.Column(db.String(50),  primary_key=True)
    given_name = db.Column(db.String(100))
    family_name = db.Column(db.String(100))
    dob = db.Column(db.Date)
    nationality = db.Column(db.String(50))
    number = db.Column(db.Integer)
    code = db.Column(db.String(10))
    url = db.Column(db.Text)

    standings = db.relationship(
        "DriverStanding", backref="driver", lazy="dynamic")

    @property
    def full_name(self):
        parts = [self.given_name or "", self.family_name or ""]
        result = " ".join(p for p in parts if p).strip()
        return result if result else (self.driver_id or "Unknown")

    def __repr__(self):
        return f"<Driver {self.full_name}>"
