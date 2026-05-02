import re
import random
import string
from datetime import datetime, timedelta
from flask import (
    Blueprint, render_template, request, redirect, 
    url_for, session, flash, jsonify
)
from models import db, User, Station, Train, TrainSeat, TrainStop, SeatType, Ticket, Payment, Announcement

client_bp = Blueprint('client', __name__)


def generate_order_no():
    """生成订单号"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = ''.join(random.choices(string.digits, k=6))
    return f"SH{timestamp}{random_str}"


@client_bp.route('/')
def index():
    """首页"""
    # 获取最新公告
    announcements = Announcement.query.filter_by(is_active=1).order_by(
        Announcement.created_at.desc()
    ).limit(5).all()
    
    # 获取热门车次
    popular_trains = Train.query.filter_by(is_active=1).limit(8).all()
    
    provinces = db.session.query(Station.province).distinct().all()
    provinces = [p[0] for p in provinces]
    
    from datetime import date as date_mod
    return render_template('client/index.html', 
                         announcements=announcements,
                         popular_trains=popular_trains,
                         provinces=sorted(provinces),
                         today=date_mod.today().isoformat())


@client_bp.route('/search')
def search():
    """车次查询"""
    from_station = request.args.get('from', '')
    to_station = request.args.get('to', '')
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    train_type = request.args.get('type', '')
    
    # 验证日期
    try:
        query_date = datetime.strptime(date, '%Y-%m-%d')
    except:
        date = datetime.now().strftime('%Y-%m-%d')
        query_date = datetime.strptime(date, '%Y-%m-%d')
    
    # 构建查询
    query = Train.query.filter_by(is_active=1)
    
    if from_station:
        from_s = Station.query.filter(
            db.or_(
                Station.station_name.like(f'%{from_station}%'),
                Station.station_code.like(f'%{from_station}%')
            )
        ).first()
        if from_s:
            query = query.filter_by(start_station_id=from_s.id)
    
    if to_station:
        to_s = Station.query.filter(
            db.or_(
                Station.station_name.like(f'%{to_station}%'),
                Station.station_code.like(f'%{to_station}%')
            )
        ).first()
        if to_s:
            query = query.filter_by(end_station_id=to_s.id)
    
    if train_type:
        type_map = {
            'G': '高铁', 'D': '动车', 'K': '普速',
            'T': '普速', 'Z': '普速', 'C': '城际'
        }
        if train_type in type_map:
            query = query.filter_by(train_type=type_map[train_type])
    
    trains = query.order_by(Train.departure_time).all()
    
    # 获取每个车次的余票信息
    train_data = []
    for train in trains:
        seats = TrainSeat.query.filter_by(train_id=train.id).all()
        
        seat_info = []
        for seat in seats:
            seat_info.append({
                'type_name': seat.seat_type.name,
                'type_code': seat.seat_type.code,
                'available': seat.available_count,
                'price': seat.price
            })
        
        train_data.append({
            'train': train,
            'seats': seat_info
        })
    
    return render_template('client/search.html',
                         trains=train_data,
                         from_station=from_station,
                         to_station=to_station,
                         date=date,
                         train_type=train_type)


@client_bp.route('/book/<int:train_id>', methods=['GET', 'POST'])
def book(train_id):
    """订单确认页面"""
    if 'user_id' not in session:
        flash('请先登录', 'warning')
        return redirect(url_for('auth.login'))
    
    train = Train.query.get_or_404(train_id)
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # 获取席别信息
    seats = TrainSeat.query.filter_by(train_id=train_id).all()
    
    if request.method == 'POST':
        # 处理订单
        seat_type_id = request.form.get('seat_type_id')
        passenger_name = request.form.get('passenger_name', '').strip()
        passenger_id_card = request.form.get('passenger_id_card', '').strip()
        
        if not all([seat_type_id, passenger_name, passenger_id_card]):
            flash('请填写完整信息', 'error')
            return redirect(url_for('client.book', train_id=train_id, date=date))
        
        # 获取席别
        seat = TrainSeat.query.get(seat_type_id)
        if not seat or seat.available_count <= 0:
            flash('所选席别余票不足', 'error')
            return redirect(url_for('client.book', train_id=train_id, date=date))
        
        # 检查是否重复购票
        existing = Ticket.query.filter_by(
            user_id=session['user_id'],
            train_id=train_id,
            departure_date=date,
            status='paid'
        ).first()
        
        if existing:
            flash('您已购买该车次车票，请勿重复购买', 'error')
            return redirect(url_for('client.book', train_id=train_id, date=date))
        
        # 生成订单号
        order_no = generate_order_no()
        
        # 分配座位号
        car_number = str(random.randint(1, seat.total_count // 100))
        seat_number = f"{car_number}{str(random.randint(1, 20)).zfill(2)}-{random.randint(1, 5)}"
        
        # 创建订单
        ticket = Ticket(
            order_no=order_no,
            user_id=session['user_id'],
            train_id=train_id,
            from_station_id=train.start_station_id,
            to_station_id=train.end_station_id,
            seat_type_id=seat_type_id,
            departure_date=date,
            departure_time=train.departure_time,
            arrival_time=train.arrival_time,
            car_number=car_number,
            seat_number=seat_number,
            price=seat.price,
            status='unpaid',
            passenger_name=passenger_name,
            passenger_id_card=passenger_id_card
        )
        
        # 扣减余票
        seat.available_count -= 1
        
        db.session.add(ticket)
        db.session.commit()
        
        return redirect(url_for('client.order_detail', order_id=ticket.id))
    
    return render_template('client/book.html',
                         train=train,
                         seats=seats,
                         date=date)


@client_bp.route('/order/<int:order_id>')
def order_detail(order_id):
    """订单详情"""
    ticket = Ticket.query.get_or_404(order_id)
    
    # 验证权限
    if 'user_id' not in session:
        flash('请先登录', 'warning')
        return redirect(url_for('auth.login'))
    
    if ticket.user_id != session['user_id']:
        flash('无权查看此订单', 'error')
        return redirect(url_for('client.orders'))
    
    return render_template('client/order_detail.html', ticket=ticket)


@client_bp.route('/order/<int:order_id>/pay', methods=['POST'])
def pay_order(order_id):
    """支付订单"""
    ticket = Ticket.query.get_or_404(order_id)
    
    if ticket.user_id != session['user_id']:
        return jsonify({'success': False, 'message': '无权操作'})
    
    if ticket.status != 'unpaid':
        return jsonify({'success': False, 'message': '订单状态异常'})
    
    pay_method = request.form.get('pay_method', '支付宝')
    
    # 模拟支付
    ticket.status = 'paid'
    ticket.paid_at = datetime.utcnow()
    
    payment = Payment(
        ticket_id=ticket.id,
        amount=ticket.price,
        pay_method=pay_method,
        pay_status='success',
        transaction_no=f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100000, 999999)}"
    )
    
    db.session.add(payment)
    db.session.commit()
    
    flash('支付成功', 'success')
    return redirect(url_for('client.order_detail', order_id=ticket.id))


@client_bp.route('/order/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    """取消订单"""
    ticket = Ticket.query.get_or_404(order_id)
    
    if ticket.user_id != session['user_id']:
        return jsonify({'success': False, 'message': '无权操作'})
    
    if ticket.status != 'unpaid':
        return jsonify({'success': False, 'message': '只能取消未支付的订单'})
    
    # 恢复余票
    seat = TrainSeat.query.filter_by(
        train_id=ticket.train_id,
        seat_type_id=ticket.seat_type_id
    ).first()
    if seat:
        seat.available_count += 1
    
    ticket.status = 'cancelled'
    db.session.commit()
    
    flash('订单已取消', 'success')
    return redirect(url_for('client.orders'))


@client_bp.route('/order/<int:order_id>/refund', methods=['POST'])
def refund_order(order_id):
    """退票"""
    ticket = Ticket.query.get_or_404(order_id)
    
    if ticket.user_id != session['user_id']:
        return jsonify({'success': False, 'message': '无权操作'})
    
    if ticket.status != 'paid':
        return jsonify({'success': False, 'message': '只能退票已支付的订单'})
    
    reason = request.form.get('reason', '旅客申请退票')
    
    # 计算退票费（开车前15天以上免费，15天以内5%，48小时以内10%，24小时以内20%）
    departure_dt = datetime.strptime(f"{ticket.departure_date} {ticket.departure_time}", '%Y-%m-%d %H:%M')
    hours_until_departure = (departure_dt - datetime.now()).total_seconds() / 3600
    
    if hours_until_departure > 360:
        refund_rate = 0
    elif hours_until_departure > 72:
        refund_rate = 0.05
    elif hours_until_departure > 24:
        refund_rate = 0.10
    else:
        refund_rate = 0.20
    
    refund_fee = ticket.price * refund_rate
    refund_amount = ticket.price - refund_fee
    
    # 更新订单状态
    ticket.status = 'refunded'
    
    # 恢复余票
    seat = TrainSeat.query.filter_by(
        train_id=ticket.train_id,
        seat_type_id=ticket.seat_type_id
    ).first()
    if seat:
        seat.available_count += 1
    
    # 创建退款记录
    from models import Refund
    refund = Refund(
        ticket_id=ticket.id,
        refund_amount=refund_amount,
        refund_fee=refund_fee,
        reason=reason,
        status='approved'
    )
    
    db.session.add(refund)
    db.session.commit()
    
    flash(f'退票成功，退款金额：{refund_amount:.2f}元（扣除退票费 {refund_fee:.2f}元）', 'success')
    return redirect(url_for('client.orders'))


@client_bp.route('/orders')
def orders():
    """订单列表"""
    if 'user_id' not in session:
        flash('请先登录', 'warning')
        return redirect(url_for('auth.login'))
    
    status_filter = request.args.get('status', '')
    
    query = Ticket.query.filter_by(user_id=session['user_id'])
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    orders_list = query.order_by(Ticket.created_at.desc()).all()
    
    return render_template('client/orders.html', orders=orders_list, status_filter=status_filter)


@client_bp.route('/profile')
def profile():
    """个人中心"""
    if 'user_id' not in session:
        flash('请先登录', 'warning')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_info':
            user.real_name = request.form.get('real_name', '').strip()
            user.phone = request.form.get('phone', '').strip()
            user.email = request.form.get('email', '').strip()
            user.id_card = request.form.get('id_card', '').strip()
            db.session.commit()
            flash('个人信息已更新', 'success')
        
        elif action == 'change_password':
            old_password = request.form.get('old_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            if not user.check_password(old_password):
                flash('原密码错误', 'error')
                return redirect(url_for('client.profile'))
            
            if new_password != confirm_password:
                flash('两次密码输入不一致', 'error')
                return redirect(url_for('client.profile'))
            
            if len(new_password) < 6:
                flash('新密码长度不能少于6位', 'error')
                return redirect(url_for('client.profile'))
            
            user.set_password(new_password)
            db.session.commit()
            flash('密码已修改', 'success')
    
    return render_template('client/profile.html', user=user)


@client_bp.route('/train/<int:train_id>')
def train_detail(train_id):
    """车次详情"""
    train = Train.query.get_or_404(train_id)
    stops = TrainStop.query.filter_by(train_id=train_id).order_by(TrainStop.stop_order).all()
    
    return render_template('client/train_detail.html', train=train, stops=stops)


@client_bp.route('/timetable')
def timetable():
    """列车时刻表"""
    train_code = request.args.get('code', '')
    station = request.args.get('station', '')
    
    query = Train.query.filter_by(is_active=1)
    
    if train_code:
        query = query.filter(Train.train_code.like(f'%{train_code}%'))
    
    if station:
        s = Station.query.filter(
            db.or_(
                Station.station_name.like(f'%{station}%'),
                Station.station_code.like(f'%{station}%')
            )
        ).first()
        if s:
            query = query.join(TrainStop, Train.id == TrainStop.train_id).filter(
                TrainStop.station_id == s.id
            ).group_by(Train.id)
    
    trains = query.order_by(Train.train_code).paginate(
        page=1, per_page=50, error_out=False
    )
    
    return render_template('client/timetable.html', trains=trains)


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
