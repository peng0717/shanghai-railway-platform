from flask import Blueprint, render_template, request, redirect, session, flash, jsonify
from models import db, User, Station, Train, TrainStop, TrainSeat, SeatType, Ticket, Payment, Refund, Announcement, TrainScheduleChange, OperationLog
from ops.auth import ops_login_required, log_ops_action
from datetime import datetime, timedelta

ops_bp = Blueprint('ops', __name__)


@ops_bp.route('/')
@ops_login_required
def dashboard():
    """仪表盘"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 今日数据统计
    today_tickets = Ticket.query.filter_by(
        departure_date=today,
        status='paid'
    ).count()
    
    today_revenue = db.session.query(db.func.sum(Ticket.price)).filter(
        Ticket.departure_date == today,
        Ticket.status == 'paid'
    ).scalar() or 0
    
    active_trains = Train.query.filter_by(is_active=1).count()
    total_stations = Station.query.count()
    
    # 近7天售票趋势
    week_dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    week_tickets = []
    week_revenue = []
    
    for date in week_dates:
        count = Ticket.query.filter_by(departure_date=date, status='paid').count()
        revenue = db.session.query(db.func.sum(Ticket.price)).filter(
            Ticket.departure_date == date, Ticket.status == 'paid'
        ).scalar() or 0
        week_tickets.append(count)
        week_revenue.append(float(revenue))
    
    # 各车型售票占比
    train_types = ['高铁', '动车', '城际', '普速']
    type_stats = []
    for t_type in train_types:
        count = db.session.query(Ticket).join(Train).filter(
            Train.train_type == t_type,
            Ticket.departure_date == today,
            Ticket.status == 'paid'
        ).count()
        type_stats.append({'name': t_type, 'count': count})
    
    # 最新公告
    latest_announcements = Announcement.query.filter_by(is_active=1).order_by(
        Announcement.created_at.desc()
    ).limit(3).all()
    
    # 最新调整
    latest_changes = TrainScheduleChange.query.order_by(
        TrainScheduleChange.created_at.desc()
    ).limit(5).all()
    
    return render_template('ops/dashboard.html',
                         today_tickets=today_tickets,
                         today_revenue=float(today_revenue),
                         active_trains=active_trains,
                         total_stations=total_stations,
                         week_dates=week_dates,
                         week_tickets=week_tickets,
                         week_revenue=week_revenue,
                         type_stats=type_stats,
                         latest_announcements=latest_announcements,
                         latest_changes=latest_changes)


@ops_bp.route('/trains')
@ops_login_required
def trains():
    """车次管理"""
    search_code = request.args.get('code', '')
    search_type = request.args.get('type', '')
    page = request.args.get('page', 1, type=int)
    
    query = Train.query
    
    if search_code:
        query = query.filter(Train.train_code.like(f'%{search_code}%'))
    
    if search_type:
        query = query.filter_by(train_type=search_type)
    
    trains_list = query.order_by(Train.train_code).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('ops/trains.html', trains=trains_list)


@ops_bp.route('/trains/new', methods=['GET', 'POST'])
@ops_login_required
def train_new():
    """新建车次"""
    if request.method == 'POST':
        train_code = request.form.get('train_code', '').strip().upper()
        
        if Train.query.filter_by(train_code=train_code).first():
            flash('车次号已存在', 'error')
            return redirect('/ops/trains/new')
        
        start_station_id = request.form.get('start_station_id', type=int)
        end_station_id = request.form.get('end_station_id', type=int)
        
        train = Train(
            train_code=train_code,
            train_type=request.form.get('train_type'),
            start_station_id=start_station_id,
            end_station_id=end_station_id,
            departure_time=request.form.get('departure_time'),
            arrival_time=request.form.get('arrival_time'),
            duration=request.form.get('duration', type=int),
            total_distance=request.form.get('total_distance', type=int),
            is_active=1
        )
        
        db.session.add(train)
        db.session.commit()
        
        log_ops_action(session['ops_user_id'], 'create', 'train', f'创建车次 {train_code}')
        flash('车次创建成功', 'success')
        return redirect(f'/ops/trains/{train.id}/edit')
    
    stations = Station.query.order_by(Station.province, Station.station_name).all()
    return render_template('ops/train_form.html', train=None, stations=stations)


@ops_bp.route('/trains/<int:train_id>/edit', methods=['GET', 'POST'])
@ops_login_required
def train_edit(train_id):
    """编辑车次"""
    train = Train.query.get_or_404(train_id)
    stations = Station.query.order_by(Station.province, Station.station_name).all()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'basic':
            train.train_type = request.form.get('train_type')
            train.start_station_id = request.form.get('start_station_id', type=int)
            train.end_station_id = request.form.get('end_station_id', type=int)
            train.departure_time = request.form.get('departure_time')
            train.arrival_time = request.form.get('arrival_time')
            train.duration = request.form.get('duration', type=int)
            train.total_distance = request.form.get('total_distance', type=int)
            train.is_active = 1 if request.form.get('is_active') else 0
            
            db.session.commit()
            log_ops_action(session['ops_user_id'], 'update', 'train', f'编辑车次 {train.train_code}')
            flash('车次信息已保存', 'success')
        
        elif action == 'stops':
            # 保存停站信息
            TrainStop.query.filter_by(train_id=train_id).delete()
            
            stop_orders = request.form.getlist('stop_order')
            station_ids = request.form.getlist('station_id')
            arrival_times = request.form.getlist('arrival_time')
            departure_times = request.form.getlist('departure_time')
            distances = request.form.getlist('distance')
            
            for i, station_id in enumerate(station_ids):
                if station_id and station_id != '':
                    stop = TrainStop(
                        train_id=train_id,
                        station_id=int(station_id),
                        stop_order=i + 1,
                        arrival_time=arrival_times[i] or None,
                        departure_time=departure_times[i] if 'departure_times' in dir() else None,
                        distance_from_start=int(distances[i]) if distances[i] else 0
                    )
                    db.session.add(stop)
            
            db.session.commit()
            log_ops_action(session['ops_user_id'], 'update', 'train_stops', f'编辑车次停站 {train.train_code}')
            flash('停站信息已保存', 'success')
        
        elif action == 'seats':
            # 保存席别信息
            seat_ids = request.form.getlist('seat_id')
            total_counts = request.form.getlist('total_count')
            prices = request.form.getlist('price')
            
            for i, seat_id in enumerate(seat_ids):
                if seat_id and seat_id != '':
                    train_seat = TrainSeat.query.get(int(seat_id))
                    if train_seat:
                        train_seat.total_count = int(total_counts[i]) if total_counts[i] else 0
                        train_seat.price = float(prices[i]) if prices[i] else 0
                        # 同步更新余票
                        train_seat.available_count = train_seat.total_count - Ticket.query.filter_by(
                            train_id=train_id,
                            seat_type_id=train_seat.seat_type_id,
                            status='paid'
                        ).count()
            
            db.session.commit()
            log_ops_action(session['ops_user_id'], 'update', 'train_seats', f'编辑车次席别 {train.train_code}')
            flash('席别信息已保存', 'success')
    
    stops = TrainStop.query.filter_by(train_id=train_id).order_by(TrainStop.stop_order).all()
    seats = TrainSeat.query.filter_by(train_id=train_id).all()
    seat_types = SeatType.query.all()
    
    return render_template('ops/train_form.html',
                         train=train,
                         stations=stations,
                         stops=stops,
                         seats=seats,
                         seat_types=seat_types)


@ops_bp.route('/trains/<int:train_id>/delete', methods=['POST'])
@ops_login_required
def train_delete(train_id):
    """删除车次"""
    train = Train.query.get_or_404(train_id)
    
    # 检查是否有未完成的订单
    active_tickets = Ticket.query.filter_by(train_id=train_id).filter(
        Ticket.status.in_(['unpaid', 'paid'])
    ).count()
    
    if active_tickets > 0:
        return jsonify({'success': False, 'message': f'该车次存在 {active_tickets} 张未处理的车票，无法删除'})
    
    train_code = train.train_code
    db.session.delete(train)
    db.session.commit()
    
    log_ops_action(session['ops_user_id'], 'delete', 'train', f'删除车次 {train_code}')
    
    return jsonify({'success': True, 'message': '车次已删除'})


@ops_bp.route('/stations')
@ops_login_required
def stations():
    """站点管理"""
    province = request.args.get('province', '')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    query = Station.query
    
    if province:
        query = query.filter_by(province=province)
    
    if search:
        query = query.filter(
            db.or_(
                Station.station_name.like(f'%{search}%'),
                Station.station_code.like(f'%{search}%'),
                Station.pinyin.like(f'%{search}%')
            )
        )
    
    stations_list = query.order_by(Station.province, Station.station_name).paginate(
        page=page, per_page=30, error_out=False
    )
    
    provinces = db.session.query(Station.province).distinct().order_by(Station.province).all()
    provinces = [p[0] for p in provinces]
    
    return render_template('ops/stations.html',
                         stations=stations_list,
                         provinces=provinces,
                         current_province=province,
                         search=search)


@ops_bp.route('/stations/new', methods=['GET', 'POST'])
@ops_login_required
def station_new():
    """新建站点"""
    if request.method == 'POST':
        station_code = request.form.get('station_code', '').strip().upper()
        
        if Station.query.filter_by(station_code=station_code).first():
            flash('站点代码已存在', 'error')
            return redirect('/ops/stations/new')
        
        station = Station(
            station_code=station_code,
            station_name=request.form.get('station_name'),
            pinyin=request.form.get('pinyin'),
            city=request.form.get('city'),
            province=request.form.get('province'),
            station_level=request.form.get('station_level'),
            is_high_speed=1 if request.form.get('is_high_speed') else 0
        )
        
        db.session.add(station)
        db.session.commit()
        
        log_ops_action(session['ops_user_id'], 'create', 'station', f'创建站点 {station_code}')
        flash('站点创建成功', 'success')
        return redirect('/ops/stations')
    
    provinces = db.session.query(Station.province).distinct().order_by(Station.province).all()
    provinces = [p[0] for p in provinces]
    return render_template('ops/station_form.html', station=None, provinces=provinces)


@ops_bp.route('/stations/<int:station_id>/edit', methods=['GET', 'POST'])
@ops_login_required
def station_edit(station_id):
    """编辑站点"""
    station = Station.query.get_or_404(station_id)
    
    if request.method == 'POST':
        station.station_name = request.form.get('station_name')
        station.pinyin = request.form.get('pinyin')
        station.city = request.form.get('city')
        station.province = request.form.get('province')
        station.station_level = request.form.get('station_level')
        station.is_high_speed = 1 if request.form.get('is_high_speed') else 0
        
        db.session.commit()
        log_ops_action(session['ops_user_id'], 'update', 'station', f'编辑站点 {station.station_code}')
        flash('站点信息已保存', 'success')
        return redirect('/ops/stations')
    
    provinces = db.session.query(Station.province).distinct().order_by(Station.province).all()
    provinces = [p[0] for p in provinces]
    return render_template('ops/station_form.html', station=station, provinces=provinces)


@ops_bp.route('/tickets')
@ops_login_required
def tickets():
    """票务管理 - 售票记录"""
    train_code = request.args.get('train_code', '')
    date = request.args.get('date', '')
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    
    query = Ticket.query
    
    if train_code:
        query = query.join(Train).filter(Train.train_code.like(f'%{train_code}%'))
    
    if date:
        query = query.filter_by(departure_date=date)
    
    if status:
        query = query.filter_by(status=status)
    
    tickets_list = query.order_by(Ticket.created_at.desc()).paginate(
        page=page, per_page=30, error_out=False
    )
    
    return render_template('ops/tickets.html', tickets=tickets_list)


@ops_bp.route('/refunds')
@ops_login_required
def refunds():
    """退票管理"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = Refund.query
    
    if status:
        query = query.filter_by(status=status)
    
    refunds_list = query.order_by(Refund.created_at.desc()).paginate(
        page=page, per_page=30, error_out=False
    )
    
    return render_template('ops/refunds.html', refunds=refunds_list)


@ops_bp.route('/refunds/<int:refund_id>/process', methods=['POST'])
@ops_login_required
def refund_process(refund_id):
    """处理退款"""
    refund = Refund.query.get_or_404(refund_id)
    action = request.form.get('action')
    
    if refund.status != 'pending':
        return jsonify({'success': False, 'message': '该退款已处理'})
    
    if action == 'approve':
        refund.status = 'approved'
    elif action == 'reject':
        refund.status = 'rejected'
    
    db.session.commit()
    log_ops_action(session['ops_user_id'], 'process', 'refund', f'处理退款 {refund.id}')
    
    return jsonify({'success': True, 'message': f'退款已{("批准" if action == "approve" else "拒绝")}'})


@ops_bp.route('/users')
@ops_login_required
def users():
    """用户管理"""
    search = request.args.get('search', '')
    user_type = request.args.get('type', '')
    page = request.args.get('page', 1, type=int)
    
    query = User.query
    
    if search:
        query = query.filter(
            db.or_(
                User.username.like(f'%{search}%'),
                User.real_name.like(f'%{search}%'),
                User.phone.like(f'%{search}%')
            )
        )
    
    if user_type:
        query = query.filter_by(user_type=user_type)
    
    users_list = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=30, error_out=False
    )
    
    return render_template('ops/users.html', users=users_list)


@ops_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@ops_login_required
def user_toggle(user_id):
    """启用/禁用用户"""
    user = User.query.get_or_404(user_id)
    
    if user.user_type == 'admin':
        return jsonify({'success': False, 'message': '无法禁用管理员账号'})
    
    user.status = 'disabled' if user.status == 'active' else 'active'
    db.session.commit()
    
    log_ops_action(session['ops_user_id'], 'toggle', 'user', f'{"禁用" if user.status == "disabled" else "启用"}用户 {user.username}')
    
    return jsonify({'success': True, 'message': f'用户已{"禁用" if user.status == "disabled" else "启用"}'})


@ops_bp.route('/announcements')
@ops_login_required
def announcements():
    """公告管理"""
    page = request.args.get('page', 1, type=int)
    
    announcements_list = Announcement.query.order_by(
        Announcement.created_at.desc()
    ).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('ops/announcements.html', announcements=announcements_list)


@ops_bp.route('/announcements/new', methods=['GET', 'POST'])
@ops_login_required
def announcement_new():
    """新建公告"""
    if request.method == 'POST':
        announcement = Announcement(
            title=request.form.get('title'),
            content=request.form.get('content'),
            type=request.form.get('type', 'notice'),
            is_active=1,
            created_by=session['ops_user_id']
        )
        
        db.session.add(announcement)
        db.session.commit()
        
        log_ops_action(session['ops_user_id'], 'create', 'announcement', f'创建公告 {announcement.title}')
        flash('公告发布成功', 'success')
        return redirect('/ops/announcements')
    
    return render_template('ops/announcement_form.html', announcement=None)


@ops_bp.route('/announcements/<int:announcement_id>/edit', methods=['GET', 'POST'])
@ops_login_required
def announcement_edit(announcement_id):
    """编辑公告"""
    announcement = Announcement.query.get_or_404(announcement_id)
    
    if request.method == 'POST':
        announcement.title = request.form.get('title')
        announcement.content = request.form.get('content')
        announcement.type = request.form.get('type', 'notice')
        announcement.is_active = 1 if request.form.get('is_active') else 0
        
        db.session.commit()
        log_ops_action(session['ops_user_id'], 'update', 'announcement', f'编辑公告 {announcement.title}')
        flash('公告已保存', 'success')
        return redirect('/ops/announcements')
    
    return render_template('ops/announcement_form.html', announcement=announcement)


@ops_bp.route('/announcements/<int:announcement_id>/delete', methods=['POST'])
@ops_login_required
def announcement_delete(announcement_id):
    """删除公告"""
    announcement = Announcement.query.get_or_404(announcement_id)
    
    db.session.delete(announcement)
    db.session.commit()
    
    log_ops_action(session['ops_user_id'], 'delete', 'announcement', f'删除公告 {announcement.title}')
    
    return jsonify({'success': True, 'message': '公告已删除'})


@ops_bp.route('/schedule-changes')
@ops_login_required
def schedule_changes():
    """列车调整管理"""
    page = request.args.get('page', 1, type=int)
    
    changes_list = TrainScheduleChange.query.order_by(
        TrainScheduleChange.created_at.desc()
    ).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('ops/schedule_changes.html', changes=changes_list)


@ops_bp.route('/schedule-changes/new', methods=['GET', 'POST'])
@ops_login_required
def schedule_change_new():
    """新建列车调整"""
    if request.method == 'POST':
        train_id = request.form.get('train_id', type=int)
        
        change = TrainScheduleChange(
            train_id=train_id,
            change_type=request.form.get('change_type'),
            reason=request.form.get('reason'),
            effective_date=request.form.get('effective_date'),
            description=request.form.get('description'),
        )
        
        # 如果是停运，更新车次状态
        if request.form.get('change_type') == 'cancel':
            train = Train.query.get(train_id)
            if train:
                train.is_active = 0
        
        db.session.add(change)
        db.session.commit()
        
        log_ops_action(session['ops_user_id'], 'create', 'schedule_change', f'创建列车调整')
        flash('调整信息已发布', 'success')
        return redirect('/ops/schedule-changes')
    
    trains = Train.query.filter_by(is_active=1).order_by(Train.train_code).all()
    return render_template('ops/schedule_change_form.html', change=None, trains=trains)


@ops_bp.route('/schedule-changes/<int:change_id>/delete', methods=['POST'])
@ops_login_required
def schedule_change_delete(change_id):
    """删除列车调整"""
    change = TrainScheduleChange.query.get_or_404(change_id)
    
    # 如果是停运，恢复车次状态
    if change.change_type == 'cancel':
        train = Train.query.get(change.train_id)
        if train:
            train.is_active = 1
    
    db.session.delete(change)
    db.session.commit()
    
    log_ops_action(session['ops_user_id'], 'delete', 'schedule_change', f'删除列车调整')
    
    return jsonify({'success': True, 'message': '调整信息已删除'})


@ops_bp.route('/logs')
@ops_login_required
def logs():
    """操作日志"""
    page = request.args.get('page', 1, type=int)
    module = request.args.get('module', '')
    user_id = request.args.get('user_id', type=int)
    
    query = OperationLog.query
    
    if module:
        query = query.filter_by(module=module)
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    logs_list = query.order_by(OperationLog.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    return render_template('ops/logs.html', logs=logs_list)
