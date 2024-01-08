import sys
sys.path.append('/usr/src/stock_analyse_tool_back_end_flask')
from app import create_app
from flask import Flask, request
import pandas as pd
import akshare as ak
import datetime
from config import root_path

singleToday = datetime.datetime.now().strftime("%Y%m%d")

flask_app = create_app()

if __name__ == '__main__':
    flask_app.run()
