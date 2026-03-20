# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask-based backend API for a stock analysis tool. It provides data endpoints for A-share, Hong Kong, and US stock market analysis. The app reads pre-processed CSV data files from a sibling data crawl project and also calls external data sources (akshare, tushare, xueqiu) in real time.

## Running the App

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python run.py

# Run in production (gunicorn)
gunicorn -w 4 run:flask_app
```

The app expects a `TUSHARE_TOKEN` environment variable for tushare API access.

## Key Configuration

- `config.py`: defines `root_path` (project root's parent directory) and `SQLALCHEMY_DATABASE_URI`
- `app/utils/common_config.py`: defines `prodPath` — on macOS it is `/quant`, empty on Linux. Used to build paths to index CSV data files.
- `run.py` appends `/usr/src/stock_analyse_tool_back_end_flask` to `sys.path` for production Linux deployment; local dev relies on relative imports.

## Architecture

### App Factory (`app/__init__.py`)
Creates the Flask app, configures CORS (allowed origins: localhost:8100 and mfuture.fun), and registers blueprints. The SQLAlchemy DB is initialized but currently commented out — models exist but are not in active use.

### Blueprints (`app/blueprints/`)
| Blueprint | URL prefix | Responsibility |
|---|---|---|
| `main` | `/` | Health check |
| `stock_data` | (root) | Stock/index K-line, top-bottom probability, limit-up data |
| `all_info` | `/all_info` | Comprehensive stock info, profit queries, async data |
| `stock_selection_model` | `/stock_selection_model` | KDJ screening models |

### Data Sources
Two types of data access are mixed throughout:
1. **File-based**: Reads CSV files from a sibling project at `root_path + '/stock_analyse_tool_data_crawl/database/...'`. The sibling project must exist alongside this one.
2. **Real-time API**: akshare (`ak.*`), tushare (`ts.pro_api()`), xueqiu (via `data_crawl.large_model.crawler_func.get_xueqiu_index`). The xueqiu module is imported from the sibling data crawl project via `sys.path.append`.

### Daily Update Script (`update.py`)
Runs independently (not via Flask) to recalculate index top/bottom probability CSVs and save them to `database/other/`. Called by cron or manually on trade days. It checks whether today is a trade day via `getDate()` (queries Sina Finance) before running.

### Local Database (`database/other/`)
Pre-computed CSV files served by the API:
- `index_top_bottom_percent.csv` — A-share (sh000001) top/bottom signals
- `hk_hsi_top_bottom_percent.csv` — Hang Seng index signals
- `us_dji_top_bottom_percent.csv` — Dow Jones signals
- `a_share_trade_dates.csv` — A-share trade calendar, auto-updated yearly via `app/utils/update_trade.py`

### Utility Modules (`app/utils/`)
- `index.py`: HTTP helpers (`requestForNew`, `requestForQKA`), date utilities (`getDate` queries Sina for latest trade date), JSON key cleaning
- `trend_analysis.py`: Technical analysis on index DataFrames — EMA, MA, trend direction, top/bottom probability (`batching_entry`)
- `hk_hsi_trend_analysis.py`: Same logic adapted for HK HSI data format
- `update_trade.py`: Manages `a_share_trade_dates.csv` via akshare, auto-refreshes when the year rolls over
- `common_config.py`: Platform-aware path prefix

## External Dependencies
- **akshare**: Main market data source (free)
- **tushare**: Secondary data source (requires token via `TUSHARE_TOKEN` env var)
- **xueqiu**: Used for index K-line data; requires cookie file `xueqiu_cookies.json` at project root
- **sibling project** `stock_analyse_tool_data_crawl`: Must exist at `root_path + '/stock_analyse_tool_data_crawl'`; provides crawler functions and pre-built CSV databases

## Deployment
CI/CD via `.github/workflows/deploy-flask-app.yml` — SCP files to server then `systemctl restart flaskapp.service`. Currently only triggers on the `cancle` branch (non-standard, intentional). Secrets required: `SERVER_IP`, `SERVER_USER`, `SERVER_PASSWORD`, `SERVER_PORT`, `DEPLOY_PATH`.
