from flask import Blueprint, render_template
from app import db
from app.models.driver import Driver
from app.models.circuit import Circuit
from app.models.constructor import Constructor
from app.models.race import Race
from app.models.standings import DriverStanding, ConstructorStanding
from sqlalchemy import func

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    stats = {
        "drivers":      Driver.query.count(),
        "circuits":     Circuit.query.count(),
        "constructors": Constructor.query.count(),
        "races":        Race.query.count(),
    }

    # Latest season available in DB (fully dynamic)
    latest_season = db.session.query(func.max(DriverStanding.season)).scalar()
    champion = None
    if latest_season:
        champion = DriverStanding.query.filter_by(
            season=latest_season, position=1
        ).first()

    recent_races = (
        Race.query
        .order_by(Race.season.desc(), Race.round.desc())
        .limit(5).all()
    )

    top_drivers = (
        db.session.query(
            Driver.given_name,
            Driver.family_name,
            Driver.driver_id,
            func.sum(DriverStanding.wins).label("total_wins"),
            func.sum(DriverStanding.points).label("total_points"),
        )
        .join(DriverStanding, Driver.driver_id == DriverStanding.driver_id)
        .group_by(Driver.driver_id)
        .order_by(func.sum(DriverStanding.wins).desc())
        .limit(5).all()
    )

    return render_template(
        "index.html",
        stats=stats,
        champion=champion,
        latest_season=latest_season,
        recent_races=recent_races,
        top_drivers=top_drivers,
    )
