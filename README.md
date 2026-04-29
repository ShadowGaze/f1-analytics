# F1 Analytics — CS551P Advanced Programming

A Flask web application displaying Formula 1 historical data from the open
[Jolpica F1 API](https://api.jolpi.ca/ergast/), built for University of Aberdeen CS551P Assessment 3.

**Live URL:** `https://f1-analytics.onrender.com` *(replace after deploy)*

---

## Features

- Drivers, Circuits, Constructors, Races — list + detail pages
- Paginated tables with search and filter (pure HTML forms)
- Server-side charts via **Matplotlib** (bar, line, pie — zero JavaScript)
- All data analysis uses fully dynamic year ranges pulled from the database
- Full error handling (404, 500, 403)
- Tested with pytest (routes + models)

---

## Tech Stack

| Layer      | Technology                   |
|------------|------------------------------|
| Framework  | Flask 3.0                    |
| Database   | SQLite (dev) / SQLite (prod) |
| ORM        | Flask-SQLAlchemy             |
| Charts     | Matplotlib (server-side PNG) |
| Deployment | Render                       |
| Tests      | pytest + pytest-flask        |

---

## Installation (Local)

```bash
git clone https://github.com/YOUR_USERNAME/f1-analytics.git
cd f1-analytics

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt

python load_data.py           # loads ~5000+ records from API (takes ~5 min)

flask run
```

Open `http://localhost:5000`

---

## Running Tests

```bash
pytest tests/ -v
```

Generate coverage report:

```bash
pip install pytest-cov
pytest tests/ --cov=app --cov-report=term-missing
```

---

## Git Log

```bash
git log --pretty=format:'%h : %s' --graph > git-log.txt
```

---

## Deployment (Render)

1. Push code to GitHub
2. Create new **Web Service** on [Render](https://render.com)
3. Connect your GitHub repo
4. Set:
   - **Build Command:** `pip install -r requirements.txt && python load_data.py`
   - **Start Command:** `gunicorn run:app`
   - **Environment Variable:** `FLASK_ENV=production`
5. Deploy — Render will build, load data, and serve the app

---

## MVC Structure
