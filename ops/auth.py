from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, User
from functools import wraps

ops_auth_bp = Blueprint('ops_auth', __name__)


def ops_login_required(f):
    """运营系统登录验证"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'ops_user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('ops_auth.login'))
        
        user = User.query.get(session['ops_user_id'])
        if not user or user.status == 'disabled':
            session.clear()
            flash('账号状态异常，请重新登录', 'error')
            return redirect(url_for('ops_auth.login'))
        
        if user.user_type not in ['admin', 'staff']:
            flash('无权访问运营管理系统', 'error')
            return redirect('/')
        
        return f(*args, **kwargs)
    return decorated_function


def log_ops_action(user_id, action, module, detail):
    """记录运营系统操作日志"""
    from models import OperationLog
    from flask import request
    
    log = OperationLog(
        user_id=user_id,
        action=action,
        module=module,
        detail=detail,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()


@ops_auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """运营系统登录"""
    if 'ops_user_id' in session:
        return redirect('/ops/')
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return redirect(url_for('ops_auth.login'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if user.status == 'disabled':
                flash('账号已被禁用', 'error')
                return redirect(url_for('ops_auth.login'))
            
            if user.user_type not in ['admin', 'staff']:
                flash('无权访问运营管理系统', 'error')
                return redirect(url_for('ops_auth.login'))
            
            session['ops_user_id'] = user.id
            session['ops_username'] = user.username
            session['ops_real_name'] = user.real_name
            session['ops_user_type'] = user.user_type
            
            log_ops_action(user.id, 'login', 'auth', '运营系统登录')
            
            flash(f'欢迎回来，{user.real_name}', 'success')
            return redirect('/ops/')
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('ops/login.html')


@ops_auth_bp.route('/logout')
def logout():
    """运营系统登出"""
    user_id = session.get('ops_user_id')
    if user_id:
        log_ops_action(user_id, 'logout', 'auth', '运营系统登出')
    
    session.pop('ops_user_id', None)
    session.pop('ops_username', None)
    session.pop('ops_real_name', None)
    session.pop('ops_user_type', None)
    
    flash('您已退出运营系统', 'success')
    return redirect(url_for('ops_auth.login'))
