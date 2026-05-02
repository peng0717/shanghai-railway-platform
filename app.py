import os
import sys
import socket

def check_port(port):
    """检查端口是否被占用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('0.0.0.0', port))
    sock.close()
    return result == 0

def install_dependencies():
    """自动安装依赖"""
    try:
        import flask
        import flask_sqlalchemy
        import flask_cors
    except ImportError:
        print("正在安装依赖...")
        os.system("pip install flask flask-sqlalchemy flask-cors -q")
        print("依赖安装完成")

# 启动前先安装依赖
install_dependencies()

from flask import Flask, session, redirect, url_for
from flask_cors import CORS
from config import Config
from models import db
from seed_data import init_database

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)

# 启用CORS
CORS(app)

# 初始化数据库
db.init_app(app)

# 自动初始化数据库
with app.app_context():
    db.create_all()
    from models import User, Station
    if User.query.count() == 0:
        print("正在初始化数据库...")
        init_database(app, db)
        print("数据库初始化完成")

# 注册蓝图
from client.routes import client_bp
from client.auth import auth_bp
from ops.routes import ops_bp
from ops.auth import ops_auth_bp

app.register_blueprint(client_bp)  # 客票系统 /
app.register_blueprint(auth_bp)    # 认证 /
app.register_blueprint(ops_bp, url_prefix='/ops')    # 运营系统 /ops/
app.register_blueprint(ops_auth_bp, url_prefix='/ops/auth')  # 运营系统认证

# 错误页面
@app.route('/error')
def error_page():
    from flask import render_template
    return render_template('error.html', message='页面加载失败，请返回首页重试')

@app.route('/ops/error')
def ops_error_page():
    from flask import render_template
    return render_template('ops/error.html', message='页面加载失败，请返回首页重试')

# 根路径由client蓝图处理，不再重复注册

@app.route('/gate/')
def gate():
    return "闸机检票系统（建设中）"

@app.route('/health')
def health():
    return {'status': 'ok', 'service': 'shanghai-railway-platform'}

# 404处理
@app.errorhandler(404)
def not_found(e):
    from flask import request
    if request.path.startswith('/ops'):
        from flask import render_template
        return render_template('ops/404.html'), 404
    from flask import render_template
    return render_template('client/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    from flask import request
    if request.path.startswith('/ops'):
        from flask import render_template
        return render_template('ops/500.html'), 500
    from flask import render_template
    return render_template('client/500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    # 检查端口是否可用
    if check_port(port):
        print(f"警告：端口 {port} 已被占用，尝试其他端口...")
        for try_port in range(port + 1, port + 100):
            if not check_port(try_port):
                port = try_port
                break
    
    print(f"上海局铁路一体化集成平台启动中...")
    print(f"客票系统访问地址: http://localhost:{port}/")
    print(f"运营管理系统访问地址: http://localhost:{port}/ops/")
    print(f"闸机检票系统（预留）: http://localhost:{port}/gate/")
    print("-" * 50)
    print("演示账号：")
    print("  管理员: admin / admin123")
    print("  旅客: demo / demo123")
    print("  职工: staff / staff123")
    print("-" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=False)
