import sys
sys.path.append('/usr/src/stock_analyse_tool_back_end_flask')
from app import create_app

flask_app = create_app()

if __name__ == '__main__':
    flask_app.run(debug=True)
