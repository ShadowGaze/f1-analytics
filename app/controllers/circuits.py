from flask import Blueprint, render_template, request
from app import db
from app.models.circuit import Circuit
from app.models.race import Race

circuits_bp = Blueprint("circuits", __name__)


@circuits_bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("q", "").strip()
    country = request.args.get("country", "").strip()

    query = Circuit.query
    if search:
        term = f"%{search}%"
        query = query.filter(
            Circuit.circuit_name.ilike(term) | Circuit.locality.ilike(term)
        )
    if country:
        query = query.filter(Circuit.country == country)

    pagination = query.order_by(Circuit.country, Circuit.circuit_name).paginate(
        page=page, per_page=20, error_out=False
    )
    countries = [c[0] for c in
                 db.session.query(Circuit.country)
                 .filter(Circuit.country.isnot(None))
                 .distinct().order_by(Circuit.country).all()
                 ]
    return render_template(
        "circuits/list.html",
        pagination=pagination,
        search=search,
        country=country,
        countries=countries,
    )


@circuits_bp.route("/<circuit_id>")
def detail(circuit_id):
    circuit = Circuit.query.get_or_404(circuit_id)
    races = (
        Race.query
        .filter_by(circuit_id=circuit_id)
        .order_by(Race.season.desc())
        .all()
    )
    return render_template(
        "circuits/detail.html",
        circuit=circuit,
        races=races,
        total_races=len(races),
        first_race=races[-1] if races else None,
        latest_race=races[0] if races else None,
        seasons_held=len(set(r.season for r in races)),
    )
