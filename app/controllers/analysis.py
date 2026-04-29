"""
Analysis controller — all charts rendered server-side with matplotlib.
NO JavaScript. Charts are served as PNG image responses.
"""
from sqlalchemy import func
from app.models.race import Race
from app.models.standings import DriverStanding, ConstructorStanding
from app.models.constructor import Constructor
from app.models.driver import Driver
from app import db
from flask import Blueprint, render_template, request, Response
from io import BytesIO
from matplotlib.figure import Figure
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend — must be before Figure import


analysis_bp = Blueprint("analysis", __name__)

# ── Shared chart style ────────────────────────────────────────────────────
BG = "#141414"
SURFACE = "#1e1e1e"
RED = "#E10600"
MUTED = "#888888"
TEXT = "#e0e0e0"
GRID = "#2a2a2a"
PALETTE = ["#E10600", "#1E90FF", "#FFD700", "#00C853",
           "#FF6D00", "#9C27B0", "#00BCD4", "#FF4081",
           "#8BC34A", "#FF9800"]


def _png_response(fig):
    """Convert a matplotlib Figure to a Flask PNG response."""
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    return Response(buf.getvalue(), mimetype="image/png")


def _base_fig(w=10, h=4.5):
    fig = Figure(figsize=(w, h), facecolor=BG)
    return fig


def _style_ax(ax):
    ax.set_facecolor(SURFACE)
    ax.tick_params(colors=MUTED, labelsize=9)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)
    ax.title.set_color(TEXT)
    ax.grid(axis="both", color=GRID, linewidth=0.6, linestyle="--", alpha=0.6)


# ── Main analysis page ────────────────────────────────────────────────────
@analysis_bp.route("/")
def index():
    # All seasons from DB — fully dynamic, no hardcoded year
    seasons = [s[0] for s in
               db.session.query(DriverStanding.season)
               .distinct().order_by(DriverStanding.season.desc()).all()
               ]
    latest = seasons[0] if seasons else None
    season = request.args.get("season", latest, type=int)

    # Season summary data (for table display, not chart)
    season_driver_standings = []
    season_constructor_standings = []

    if season:
        season_driver_standings = (
            db.session.query(
                (Driver.given_name + " " + Driver.family_name).label("name"),
                DriverStanding.points,
                DriverStanding.wins,
                DriverStanding.position,
            )
            .join(DriverStanding, Driver.driver_id == DriverStanding.driver_id)
            .filter(DriverStanding.season == season)
            .order_by(DriverStanding.position)
            .limit(20).all()
        )
        season_constructor_standings = (
            db.session.query(
                Constructor.name,
                ConstructorStanding.points,
                ConstructorStanding.wins,
                ConstructorStanding.position,
            )
            .join(ConstructorStanding,
                  Constructor.constructor_id == ConstructorStanding.constructor_id)
            .filter(ConstructorStanding.season == season)
            .order_by(ConstructorStanding.position)
            .limit(15).all()
        )

    return render_template(
        "analysis/index.html",
        seasons=seasons,
        selected_season=season,
        season_driver_standings=season_driver_standings,
        season_constructor_standings=season_constructor_standings,
    )


# ── Chart routes — return PNG images ─────────────────────────────────────

@analysis_bp.route("/chart/wins")
def chart_wins():
    """Horizontal bar — top 10 drivers by all-time wins."""
    rows = (
        db.session.query(
            (Driver.given_name + " " + Driver.family_name).label("name"),
            func.sum(DriverStanding.wins).label("wins"),
        )
        .join(DriverStanding, Driver.driver_id == DriverStanding.driver_id)
        .group_by(Driver.driver_id)
        .order_by(func.sum(DriverStanding.wins).desc())
        .limit(10).all()
    )
    names = [r[0].split()[-1] for r in rows][::-1]
    values = [int(r[1] or 0) for r in rows][::-1]

    fig = _base_fig(10, 5)
    ax = fig.subplots()
    _style_ax(ax)
    bars = ax.barh(names, values, color=RED, height=0.6)
    ax.bar_label(bars, padding=4, color=MUTED, fontsize=8)
    ax.set_xlabel("Race Wins", color=MUTED)
    ax.set_title("Top 10 Drivers — All-Time Race Wins",
                 color=TEXT, fontsize=11)
    fig.tight_layout()
    return _png_response(fig)


@analysis_bp.route("/chart/races-per-season")
def chart_races_per_season():
    """Line chart — number of races per season (all seasons from DB)."""
    rows = (
        db.session.query(Race.season, func.count(Race.round).label("cnt"))
        .group_by(Race.season)
        .order_by(Race.season)
        .all()
    )
    seasons = [r[0] for r in rows]
    counts = [r[1] for r in rows]

    fig = _base_fig(12, 4)
    ax = fig.subplots()
    _style_ax(ax)
    ax.plot(seasons, counts, color=RED, linewidth=2, marker="o",
            markersize=3, markerfacecolor=RED)
    ax.fill_between(seasons, counts, alpha=0.12, color=RED)
    ax.set_xlabel("Season", color=MUTED)
    ax.set_ylabel("Races", color=MUTED)
    ax.set_title("Number of Races Per Season", color=TEXT, fontsize=11)
    fig.tight_layout()
    return _png_response(fig)


@analysis_bp.route("/chart/driver-nationalities")
def chart_driver_nationalities():
    """Pie chart — top 10 driver nationalities."""
    rows = (
        db.session.query(Driver.nationality,
                         func.count(Driver.driver_id).label("cnt"))
        .filter(Driver.nationality.isnot(None))
        .group_by(Driver.nationality)
        .order_by(func.count(Driver.driver_id).desc())
        .limit(10).all()
    )
    labels = [r[0] for r in rows]
    values = [r[1] for r in rows]

    fig = _base_fig(8, 5)
    ax = fig.subplots()
    ax.set_facecolor(BG)
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, colors=PALETTE,
        autopct="%1.1f%%", startangle=140,
        wedgeprops={"linewidth": 1, "edgecolor": BG},
        textprops={"color": TEXT, "fontsize": 8},
    )
    for at in autotexts:
        at.set_color(BG)
        at.set_fontsize(7)
    ax.set_title("Driver Nationalities (Top 10)", color=TEXT, fontsize=11)
    fig.tight_layout()
    return _png_response(fig)


@analysis_bp.route("/chart/constructor-nationalities")
def chart_constructor_nationalities():
    """Pie chart — constructor nationalities."""
    rows = (
        db.session.query(Constructor.nationality,
                         func.count(Constructor.constructor_id).label("cnt"))
        .filter(Constructor.nationality.isnot(None))
        .group_by(Constructor.nationality)
        .order_by(func.count(Constructor.constructor_id).desc())
        .limit(8).all()
    )
    labels = [r[0] for r in rows]
    values = [r[1] for r in rows]

    fig = _base_fig(8, 5)
    ax = fig.subplots()
    ax.set_facecolor(BG)
    ax.pie(
        values, labels=labels, colors=PALETTE,
        autopct="%1.1f%%", startangle=140,
        wedgeprops={"linewidth": 1, "edgecolor": BG},
        textprops={"color": TEXT, "fontsize": 8},
    )
    ax.set_title("Constructor Nationalities", color=TEXT, fontsize=11)
    fig.tight_layout()
    return _png_response(fig)


@analysis_bp.route("/chart/season-drivers/<int:season>")
def chart_season_drivers(season):
    """Bar chart — driver championship standings for a given season."""
    rows = (
        db.session.query(
            (Driver.given_name + " " + Driver.family_name).label("name"),
            DriverStanding.points,
        )
        .join(DriverStanding, Driver.driver_id == DriverStanding.driver_id)
        .filter(DriverStanding.season == season)
        .order_by(DriverStanding.position)
        .limit(20).all()
    )
    if not rows:
        fig = _base_fig(6, 3)
        ax = fig.subplots()
        ax.text(0.5, 0.5, "No data", transform=ax.transAxes,
                ha="center", va="center", color=MUTED)
        return _png_response(fig)

    names = [r[0].split()[-1] for r in rows]
    points = [r[1] or 0 for r in rows]
    colors = [RED] + ["#555555"] * (len(names) - 1)

    fig = _base_fig(11, 4.5)
    ax = fig.subplots()
    _style_ax(ax)
    bars = ax.bar(names, points, color=colors, width=0.65)
    ax.bar_label(bars, padding=3, color=MUTED, fontsize=8)
    ax.set_xlabel("Driver", color=MUTED)
    ax.set_ylabel("Points", color=MUTED)
    ax.set_title(f"{season} Driver Championship", color=TEXT, fontsize=11)
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    return _png_response(fig)


@analysis_bp.route("/chart/season-constructors/<int:season>")
def chart_season_constructors(season):
    """Bar chart — constructor championship standings for a given season."""
    rows = (
        db.session.query(Constructor.name, ConstructorStanding.points)
        .join(ConstructorStanding,
              Constructor.constructor_id == ConstructorStanding.constructor_id)
        .filter(ConstructorStanding.season == season)
        .order_by(ConstructorStanding.position)
        .limit(15).all()
    )
    if not rows:
        fig = _base_fig(6, 3)
        ax = fig.subplots()
        ax.text(0.5, 0.5, "No data", transform=ax.transAxes,
                ha="center", va="center", color=MUTED)
        return _png_response(fig)

    names = [r[0] for r in rows]
    points = [r[1] or 0 for r in rows]
    colors = ["#1E90FF"] + ["#444444"] * (len(names) - 1)

    fig = _base_fig(10, 4.5)
    ax = fig.subplots()
    _style_ax(ax)
    bars = ax.bar(names, points, color=colors, width=0.65)
    ax.bar_label(bars, padding=3, color=MUTED, fontsize=8)
    ax.set_xlabel("Constructor", color=MUTED)
    ax.set_ylabel("Points", color=MUTED)
    ax.set_title(f"{season} Constructor Championship", color=TEXT, fontsize=11)
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    return _png_response(fig)


@analysis_bp.route("/chart/top-constructors")
def chart_top_constructors():
    """Line chart — points history for top 5 constructors across all seasons."""
    top5 = [r[0] for r in (
        db.session.query(Constructor.name,
                         func.sum(ConstructorStanding.points).label("tp"))
        .join(ConstructorStanding,
              Constructor.constructor_id == ConstructorStanding.constructor_id)
        .group_by(Constructor.constructor_id)
        .order_by(func.sum(ConstructorStanding.points).desc())
        .limit(5).all()
    )]

    # All seasons from DB
    all_seasons = [s[0] for s in
                   db.session.query(ConstructorStanding.season)
                   .distinct().order_by(ConstructorStanding.season).all()
                   ]

    fig = _base_fig(12, 5)
    ax = fig.subplots()
    _style_ax(ax)

    for i, name in enumerate(top5):
        season_pts = dict(
            db.session.query(ConstructorStanding.season,
                             ConstructorStanding.points)
            .join(Constructor,
                  Constructor.constructor_id == ConstructorStanding.constructor_id)
            .filter(Constructor.name == name)
            .all()
        )
        pts = [season_pts.get(s) for s in all_seasons]
        ax.plot(all_seasons, pts, label=name, color=PALETTE[i],
                linewidth=1.8, marker="o", markersize=2)

    ax.set_xlabel("Season", color=MUTED)
    ax.set_ylabel("Points", color=MUTED)
    ax.set_title("Top 5 Constructors — Points Per Season",
                 color=TEXT, fontsize=11)
    legend = ax.legend(facecolor=SURFACE, edgecolor=GRID,
                       labelcolor=TEXT, fontsize=8)
    fig.tight_layout()
    return _png_response(fig)
