from flask import Blueprint, render_template, request
from app import db
from app.models.constructor import Constructor
from app.models.standings import ConstructorStanding
from sqlalchemy import func

constructors_bp = Blueprint("constructors", __name__)


@constructors_bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("q", "").strip()
    nationality = request.args.get("nationality", "").strip()

    query = Constructor.query
    if search:
        query = query.filter(Constructor.name.ilike(f"%{search}%"))
    if nationality:
        query = query.filter(Constructor.nationality == nationality)

    pagination = query.order_by(Constructor.name).paginate(
        page=page, per_page=20, error_out=False
    )
    nationalities = [n[0] for n in
                     db.session.query(Constructor.nationality)
                     .filter(Constructor.nationality.isnot(None))
                     .distinct().order_by(Constructor.nationality).all()
                     ]
    return render_template(
        "constructors/list.html",
        pagination=pagination,
        search=search,
        nationality=nationality,
        nationalities=nationalities,
    )


@constructors_bp.route("/<constructor_id>")
def detail(constructor_id):
    constructor = Constructor.query.get_or_404(constructor_id)
    standings = (
        ConstructorStanding.query
        .filter_by(constructor_id=constructor_id)
        .order_by(ConstructorStanding.season.desc())
        .all()
    )
    career = db.session.query(
        func.sum(ConstructorStanding.points).label("total_points"),
        func.sum(ConstructorStanding.wins).label("total_wins"),
        func.min(ConstructorStanding.position).label("best_finish"),
        func.count(ConstructorStanding.season).label("seasons"),
    ).filter_by(constructor_id=constructor_id).first()

    return render_template(
        "constructors/detail.html",
        constructor=constructor,
        standings=standings,
        career=career,
    )
