# Health Manager

## Introduction

Health Manager is a cross-platform personal health metrics and analytics application that helps individuals track and understand their physical condition through everyday body data. By entering basic information—height, weight, age, and gender—the app automatically calculates key indicators (BMI, BMR via Mifflin-St Jeor, TDEE, body-fat percentage via Deurenberg, and a healthy weight range based on Chinese adult standards) and generates a personalized report with diet, exercise, and lifestyle advice. Every report is timestamped and archived, while a weekly auto-summary aggregates history into a sortable, exportable table for trend tracking.

The project ships in two forms: a **desktop app** (Python + PyQt6, also packaged as a Windows .exe) and a **web edition** (a responsive static web app). Both share the same calculation and recommendation engine, guaranteeing consistent results. Data stays local (SQLite on desktop, localStorage on web), keeping it private and offline-friendly. Target users are health-conscious individuals, fitness enthusiasts, and anyone wanting a lightweight, no-signup tool to monitor wellness over time.

## Features

- **Health metrics engine**: BMI (with Chinese-adult grading), BMR (Mifflin-St Jeor, sex-specific), TDEE (by activity level), body-fat % (Deurenberg), healthy weight range.
- **Personalized advice**: structured diet / exercise / lifestyle recommendations generated per indicator grade.
- **Timestamped history**: every report recorded with generation time; viewable and sortable.
- **Weekly auto-summary**: natural-week aggregation into a table; auto-triggered (≥7 days) plus manual refresh; CSV export.
- **Trend visualization**: BMI line chart (PyQt6-Charts on desktop, Chart.js on web).
- **Local-first & private**: no server, no account; works fully offline.
- **CSV export**: one-click browser download on the web edition.

## Tech Stack & Dependencies

| Component | Stack                                             |
| --------- | ------------------------------------------------- |
| Desktop   | Python 3.13, PyQt6, PyQt6-Charts, SQLite (stdlib) |
| Web       | Plain HTML/CSS/JS, Chart.js (bundled locally)     |

## Installation

### Desktop (Windows / Linux / macOS)

```bash
cd health_manager
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

On Windows you may instead run the bundled executable directly (no Python required):

```bash
dist\健康管理.exe
```

### Web Edition

```bash
cd health_manager/mobile
python -m http.server 8080          # serve from mobile/www; any static server works
```

Then open `http://localhost:8080`. No build step or `npm install` is required.

## Usage

**Desktop**: launch `main.py` (or the `.exe`) → fill in height, weight, age, gender, and activity level → click *Generate* → review the results dashboard and trend chart → read the advice report → switch to *History* / *Weekly Summary* tabs.

**Web**: open `www/index.html` (or the served URL) in a browser → same flow; data is saved to the browser's `localStorage`; export CSV from the *History* or *Weekly Summary* pages.

## Directory Structure

```
health_manager/
├── calc.py                 # Health metrics engine (BMI/BMR/TDEE/body-fat/weight range)
├── storage.py              # SQLite persistence + weekly auto-summary (desktop)
├── report_gen.py           # Personalized advice generator (desktop)
├── main.py                 # PyQt6 desktop entry point
├── ui/                     # Desktop UI panels (main_window, input, result, report, history, weekly)
├── tests/                  # Python unit tests for the calc engine
├── smoke_test.py           # Headless (offscreen) smoke test
├── requirements.txt        # Desktop Python dependencies
├── pyproject.toml          # Project metadata
├── run.bat / run.sh        # Launch scripts (Windows / Linux-macOS)
├── 健康管理.spec            # PyInstaller build spec
├── dist/                   # Built Windows exe (git-ignored)
├── LICENSE                 # MIT License
└── mobile/                 # Web edition (static site)
    ├── www/                # Web assets (index.html, css, js, vendor/chart.umd.js)
    └── tests/              # JS unit & JS↔Python consistency tests
```

## Data Storage

- **Desktop**: each user has a local SQLite database at `%APPDATA%\健康管理\health.db` (Windows) / `~/Library/Application Support/健康管理/health.db` (macOS) / `~/.local/share/健康管理/health.db` (Linux). Override with the `HEALTH_DB_PATH` environment variable.
- **Mobile/Web**: reports are stored in the browser's `localStorage` (sandbox-scoped). For reliable persistence across restarts, serve the `www/` folder over HTTP or install as a PWA.
- The schema version is tracked via `PRAGMA user_version` for safe forward migrations.

## Testing

```bash
# Desktop engine
python -m unittest tests.test_calc -v
python smoke_test.py                  # requires a display or QT_QPA_PLATFORM=offscreen

# Mobile engine & consistency
cd mobile
node tests/calc.test.js
node tests/storage.test.js
node tests/validate_consistency.js    # compares JS results against Python calc.py
```

## License

Released under the [MIT License](./LICENSE). See the `LICENSE` file for the full text.
