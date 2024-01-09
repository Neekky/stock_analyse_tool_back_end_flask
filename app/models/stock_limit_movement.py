from . import db

class StockLimitMovement(db.Model):
    __tablename__ = 'stock_limit_movements'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    limit_up_count = db.Column(db.Integer, nullable=False, default=0)
    limit_down_count = db.Column(db.Integer, nullable=False, default=0)
    notes = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<StockLimitMovement {self.date}>'
