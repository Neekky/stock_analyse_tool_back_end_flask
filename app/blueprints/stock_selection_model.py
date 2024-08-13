import sys
sys.path.append('/usr/src/stock_analyse_tool_back_end_flask')
import pandas as pd
import akshare as ak
import datetime
from config import root_path
import pywencai
import json
from flask import Blueprint, jsonify, request
from app.models import db
from app.models.stock_limit_movement import StockLimitMovement

singleToday = datetime.datetime.now().strftime("%Y-%m-%d")

stock_selection_model_bp = Blueprint('stock_selection_model', __name__, url_prefix='/stock_selection_model')

# 获取涨停kdj数据
@stock_selection_model_bp.route('/get_limit_kdj_model_data', methods=['GET'])
def get_limit_kdj_model_data():
    date = request.args.get("date") or singleToday
    return '111'

# 获取见底的etf数据
@stock_selection_model_bp.route('/get_etf_data', methods=['GET'])
def get_limit_kdj_model_data():
    date = request.args.get("date") or singleToday
    # 通过趋势分析，选择见底的etf
    fund_etf_spot_em_df = ak.fund_etf_spot_em()

    return '111'

