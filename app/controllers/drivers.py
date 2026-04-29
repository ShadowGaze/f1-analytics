from flask import Blueprint, render_template, request
from app import db
from app.models.driver import Driver
from app.models.standings import DriverStanding
from sqlalchemy import func

drivers_bp = Blueprint("drivers", __name__)


class Pagination:
    """Simple pagination wrapper — avoids SQLAlchemy paginate() issues."""

    def __init__(self, items, page, per_page, total):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = max(1, (total + per_page - 1) // per_page)
        self.has_prev = page > 1
        self.has_next = page < self.pages
        self.prev_num = page - 1
        self.next_num = page + 1


@drivers_bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("q", "").strip()
    nationality = request.args.get("nationality", "").strip()
    per_page = 20

    query = Driver.query

    if search:
        term = f"%{search}%"
        query = query.filter(
            db.or_(
                Driver.given_name.ilike(term),
                Driver.family_name.ilike(term)
            )
        )
    if nationality:
        query = query.filter(Driver.nationality == nationality)

    total = query.count()
    offset = (page - 1) * per_page
    drivers = (query
               .order_by(Driver.family_name, Driver.given_name)
               .limit(per_page)
               .offset(offset)
               .all())

    pagination = Pagination(drivers, page, per_page, total)

    nationalities = [
        n[0] for n in
        db.session.query(Driver.nationality)
        .filter(Driver.nationality.isnot(None))
        .distinct()
        .order_by(Driver.nationality)
        .all()
    ]

    return render_template(
        "drivers/list.html",
        pagination=pagination,
        search=search,
        nationality=nationality,
        nationalities=nationalities,
    )


@drivers_bp.route("/<driver_id>")
def detail(driver_id):
    driver = Driver.query.get_or_404(driver_id)

    standings = (
        DriverStanding.query
        .filter_by(driver_id=driver_id)
        .order_by(DriverStanding.season.desc())
        .all()
    )

    career = db.session.query(
        func.sum(DriverStanding.points).label("total_points"),
        func.sum(DriverStanding.wins).label("total_wins"),
        func.min(DriverStanding.position).label("best_finish"),
        func.count(DriverStanding.season).label("seasons"),
    ).filter_by(driver_id=driver_id).first()

    best_season = (
        DriverStanding.query
        .filter_by(driver_id=driver_id)
        .order_by(DriverStanding.points.desc())
        .first()
    )

    # Other drivers from same nationality for context
    similar = (
        Driver.query
        .filter(
            Driver.nationality == driver.nationality,
            Driver.driver_id != driver_id
        )
        .limit(5).all()
    ) if driver.nationality else []

    return render_template(
        "drivers/detail.html",
        driver=driver,
        standings=standings,
        career=career,
        best_season=best_season,
        similar=similar,
    )
