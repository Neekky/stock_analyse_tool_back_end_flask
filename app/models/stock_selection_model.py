from . import db

class StockSelectionModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    # ... 其他字段和方法

