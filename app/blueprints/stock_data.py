from flask import Blueprint, render_template
from app.models.stock_data import StockData

stock_data_bp = Blueprint('stock_data', __name__, url_prefix='/stock_data')

@stock_data_bp.route('/')
def index():
    # 后续补充
    return 200

