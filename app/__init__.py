from flask import Flask
# from config import Config
from .blueprints.main import main_bp
from .blueprints.stock_data import stock_data_bp
from .blueprints.all_info import all_info_bp
from .blueprints.stock_selection_model import stock_selection_model_bp
from flask_cors import CORS

# def create_app(config_class=Config):
def create_app():
    app = Flask(__name__)
    # app.config.from_object(config_class)
    CORS(app, supports_credentials=True, origins=["http://127.0.0.1:8100", "https://www.mfuture.fun", "https://mfuture.fun"])

    # 初始化数据库
    # from app.models import db
    # db.init_app(app)
    
    # 注册蓝图
    app.register_blueprint(main_bp)
    app.register_blueprint(stock_data_bp)
    app.register_blueprint(all_info_bp)
    app.register_blueprint(stock_selection_model_bp)

    return app
