from app import db


class Constructor(db.Model):
    __tablename__ = "f1_constructors"

    constructor_id = db.Column(db.String(50),  primary_key=True)
    name = db.Column(db.String(150))
    nationality = db.Column(db.String(100))
    url = db.Column(db.Text)

    standings = db.relationship(
        "ConstructorStanding", backref="constructor_ref", lazy="dynamic")

    def __repr__(self):
        return f"<Constructor {self.name}>"
