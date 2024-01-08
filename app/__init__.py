from flask import Flask
from config import Config
from .blueprints.main import main_bp
from .blueprints.auth import auth_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 初始化数据库
    from app.models import db
    db.init_app(app)
    
    # 注册蓝图
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    return app
