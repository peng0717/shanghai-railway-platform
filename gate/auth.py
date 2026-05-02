from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

gate_auth_bp = Blueprint('gate_auth', __name__)


def gate_login_required(f):
    """闸机系统登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'gate_user_id' not in session:
            flash('请先登录闸机检票系统', 'warning')
            return redirect(url_for('gate_auth.login'))
        
        # 检查用户类型
        if session.get('gate_user_type') not in ['admin', 'staff']:
            flash('您没有权限访问闸机检票系统', 'error')
            return redirect(url_for('gate_auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function


@gate_auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """闸机系统登录"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return redirect(url_for('gate_auth.login'))
        
        # 从数据库验证用户
        from models import db, User
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if user.status == 'disabled':
                flash('账号已被禁用，请联系管理员', 'error')
                return redirect(url_for('gate_auth.login'))
            
            # 检查用户类型
            if user.user_type not in ['admin', 'staff']:
                flash('您没有权限访问闸机检票系统', 'error')
                return redirect(url_for('gate_auth.login'))
            
            # 设置闸机系统session（不覆盖客票系统session）
            session['gate_user_id'] = user.id
            session['gate_username'] = user.username
            session['gate_real_name'] = user.real_name
            session['gate_user_type'] = user.user_type
            
            # 记录登录日志
            log_gate_action(user.id, 'login', '闸机系统登录')
            
            flash(f'欢迎，{user.real_name or user.username}', 'success')
            return redirect(url_for('gate.dashboard'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('gate/login.html')


@gate_auth_bp.route('/logout')
def logout():
    """退出登录"""
    user_id = session.get('gate_user_id')
    if user_id:
        log_gate_action(user_id, 'logout', '闸机系统退出')
    
    # 只清除闸机系统相关的session
    session.pop('gate_user_id', None)
    session.pop('gate_username', None)
    session.pop('gate_real_name', None)
    session.pop('gate_user_type', None)
    
    flash('您已退出闸机检票系统', 'success')
    return redirect(url_for('gate_auth.login'))


def log_gate_action(user_id, action, detail):
    """记录闸机系统操作日志"""
    from models import OperationLog
    from flask import request
    
    log = OperationLog(
        user_id=user_id,
        action=action,
        module='gate',
        detail=detail,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
