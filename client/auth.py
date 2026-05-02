import re
import random
import string
from datetime import datetime, timedelta
from flask import (
    Blueprint, render_template, request, redirect, 
    url_for, session, flash, jsonify
)
from models import db, User, Station, Train, TrainSeat, Ticket, Payment, Announcement

auth = Blueprint('auth', __name__)


def generate_order_no():
    """生成订单号"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = ''.join(random.choices(string.digits, k=6))
    return f"SH{timestamp}{random_str}"


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return redirect(url_for('auth.login'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if user.status == 'disabled':
                flash('账号已被禁用，请联系管理员', 'error')
                return redirect(url_for('auth.login'))
            
            session['user_id'] = user.id
            session['username'] = user.username
            session['real_name'] = user.real_name
            session['user_type'] = user.user_type
            
            # 记录登录日志
            log_action(user.id, 'login', 'auth', f'用户登录')
            
            flash(f'欢迎回来，{user.real_name or user.username}', 'success')
            
            # 根据用户类型跳转
            if user.user_type in ['admin', 'staff']:
                return redirect(url_for('ops.dashboard'))
            return redirect(url_for('client.index'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('client/login.html')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        real_name = request.form.get('real_name', '').strip()
        id_card = request.form.get('id_card', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        
        # 验证
        if not all([username, password, confirm_password, real_name]):
            flash('请填写所有必填项', 'error')
            return redirect(url_for('auth.register'))
        
        if password != confirm_password:
            flash('两次密码输入不一致', 'error')
            return redirect(url_for('auth.register'))
        
        if len(password) < 6:
            flash('密码长度不能少于6位', 'error')
            return redirect(url_for('auth.register'))
        
        # 验证身份证格式
        if id_card and not re.match(r'^\d{17}[\dXx]$', id_card):
            flash('身份证号码格式不正确', 'error')
            return redirect(url_for('auth.register'))
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已被注册', 'error')
            return redirect(url_for('auth.register'))
        
        # 创建用户
        user = User(
            username=username,
            real_name=real_name,
            id_card=id_card,
            phone=phone,
            email=email,
            user_type='passenger',
            status='active'
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('client/register.html')


@auth.route('/logout')
def logout():
    """用户登出"""
    user_id = session.get('user_id')
    if user_id:
        log_action(user_id, 'logout', 'auth', '用户登出')
    
    session.clear()
    flash('您已成功退出登录', 'success')
    return redirect(url_for('client.index'))


@auth.route('/api/stations')
def api_stations():
    """获取站点列表API"""
    query = request.args.get('q', '')
    province = request.args.get('province', '')
    
    stations_query = Station.query
    
    if query:
        stations_query = stations_query.filter(
            db.or_(
                Station.station_name.like(f'%{query}%'),
                Station.pinyin.like(f'%{query}%'),
                Station.station_code.like(f'%{query}%')
            )
        )
    
    if province:
        stations_query = stations_query.filter_by(province=province)
    
    stations = stations_query.limit(20).all()
    
    return jsonify([{
        'id': s.id,
        'station_code': s.station_code,
        'station_name': s.station_name,
        'pinyin': s.pinyin,
        'province': s.province,
        'city': s.city
    } for s in stations])


def log_action(user_id, action, module, detail):
    """记录操作日志"""
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
