from flask import Blueprint, render_template, request
from app import db
from app.models.race import Race

races_bp = Blueprint("races", __name__)


@races_bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    season = request.args.get("season", type=int)
    search = request.args.get("q", "").strip()

    query = Race.query
    if season:
        query = query.filter(Race.season == season)
    if search:
        query = query.filter(Race.race_name.ilike(f"%{search}%"))

    pagination = query.order_by(Race.season.desc(), Race.round.desc()).paginate(
        page=page, per_page=25, error_out=False
    )
    # All seasons available in DB — fully dynamic
    seasons = [s[0] for s in
               db.session.query(Race.season)
               .distinct().order_by(Race.season.desc()).all()
               ]
    return render_template(
        "races/list.html",
        pagination=pagination,
        seasons=seasons,
        selected_season=season,
        search=search,
    )


@races_bp.route("/<int:season>/<int:round_num>")
def detail(season, round_num):
    race = Race.query.filter_by(season=season, round=round_num).first_or_404()
    season_races = (
        Race.query
        .filter_by(season=season)
        .order_by(Race.round).all()
    )
    idx = next((i for i, r in enumerate(season_races)
               if r.round == round_num), None)
    prev_race = season_races[idx - 1] if idx and idx > 0 else None
    next_race = season_races[idx +
                             1] if idx is not None and idx < len(season_races) - 1 else None
    return render_template(
        "races/detail.html",
        race=race,
        season_races=season_races,
        prev_race=prev_race,
        next_race=next_race,
    )
