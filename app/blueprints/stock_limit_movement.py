from flask import Blueprint, jsonify, request
from app import db
from app.models.stock_limit_movement import StockLimitMovement

bp_stock = Blueprint('bp_stock', __name__)

@bp_stock.route('/add_movements', methods=['POST'])
def add_movements():
    # 从请求中获取JSON数据
    data = request.get_json()

    # 确保数据是一个列表
    if not isinstance(data, list):
        return jsonify({"message": "Input data should be a list of movements."}), 400

    # 准备要插入的StockLimitMovement对象列表
    movements_to_add = []
    for item in data:
        if 'date' in item and 'limit_up_count' in item and 'limit_down_count' in item:
            new_movement = StockLimitMovement(
                date=item['date'],
                limit_up_count=item['limit_up_count'],
                limit_down_count=item['limit_down_count'],
                notes=item.get('notes')  # .get()方法会在'notes'不存在时返回None
            )
            movements_to_add.append(new_movement)
        else:
            # 如果列表中某个元素缺少必要的数据，返回400错误
            return jsonify({"message": "Each item in the list must contain 'date', 'limit_up_count', and 'limit_down_count'."}), 400
    
    # 批量添加记录到数据库中
    try:
        db.session.add_all(movements_to_add)
        db.session.commit()
        return jsonify({"message": f"{len(movements_to_add)} stock limit movements added successfully."}), 201
    except Exception as e:
        # 如果发生异常，回滚数据库会话
        db.session.rollback()
        return jsonify({"message": "Error occurred while adding stock limit movements."}), 500
