from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, timedelta
from models import db, User, Station, Train, TrainStop, Ticket, Gate, GateCheck, CheckPlan
from gate.auth import gate_login_required

gate_bp = Blueprint('gate', __name__)


@gate_bp.route('/')
@gate_login_required
def dashboard():
    """实时监控台"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 统计数据
    today_checks = GateCheck.query.filter(
        db.func.date(GateCheck.checked_at) == today
    ).all()
    
    total_today = len(today_checks)
    pass_count = len([c for c in today_checks if c.check_result == 'pass'])
    reject_count = total_today - pass_count
    pass_rate = (pass_count / total_today * 100) if total_today > 0 else 0
    
    # 在线闸机数
    online_gates = Gate.query.filter_by(status='online').count()
    total_gates = Gate.query.count()
    
    # 当前检票中的车次
    current_check_plans = CheckPlan.query.filter(
        CheckPlan.status == 'checking'
    ).all()
    
    # 获取各检票计划的进度
    checking_trains = []
    for plan in current_check_plans:
        train = Train.query.get(plan.train_id)
        station = Station.query.get(plan.station_id)
        if train and station:
            # 计算已检票人数
            checked_count = GateCheck.query.filter(
                GateCheck.check_plan_id == plan.id,
                GateCheck.check_result == 'pass'
            ).count()
            
            checking_trains.append({
                'plan': plan,
                'train': train,
                'station': station,
                'checked_count': checked_count
            })
    
    # 闸机状态矩阵
    all_gates = Gate.query.order_by(Gate.station_id, Gate.gate_code).all()
    gates_by_station = {}
    for gate in all_gates:
        station_name = gate.station.station_name if gate.station else '未知'
        if station_name not in gates_by_station:
            gates_by_station[station_name] = []
        gates_by_station[station_name].append(gate)
    
    # 最近的检票记录
    recent_checks = GateCheck.query.order_by(
        GateCheck.checked_at.desc()
    ).limit(20).all()
    
    return render_template('gate/dashboard.html',
                         total_today=total_today,
                         pass_count=pass_count,
                         reject_count=reject_count,
                         pass_rate=round(pass_rate, 1),
                         online_gates=online_gates,
                         total_gates=total_gates,
                         checking_trains=checking_trains,
                         gates_by_station=gates_by_station,
                         recent_checks=recent_checks)


@gate_bp.route('/check', methods=['GET', 'POST'])
@gate_login_required
def check():
    """检票操作台"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        check_method = request.form.get('check_method', 'id_card')
        id_card = request.form.get('id_card', '').strip()
        order_no = request.form.get('order_no', '').strip()
        
        # 获取当前选中的闸机和检票计划
        gate_id = request.form.get('gate_id', type=int)
        check_plan_id = request.form.get('check_plan_id', type=int)
        
        # 查找车票
        ticket = None
        passenger_name = None
        passenger_id = None
        
        if check_method == 'id_card' and id_card:
            # 身份证检票
            ticket = Ticket.query.filter_by(
                passenger_id_card=id_card,
                departure_date=today,
                status='paid'
            ).first()
        elif check_method == 'qrcode' and order_no:
            # 订单号检票
            ticket = Ticket.query.filter_by(
                order_no=order_no,
                status='paid'
            ).first()
        
        if ticket:
            passenger_name = ticket.passenger_name
            passenger_id = ticket.passenger_id_card
            train = ticket.train
            
            # 验证车次是否在检票中
            plan = None
            if check_plan_id:
                plan = CheckPlan.query.get(check_plan_id)
            else:
                # 查找该车次在当前车站的检票计划
                plan = CheckPlan.query.filter(
                    CheckPlan.train_id == train.id,
                    CheckPlan.station_id == ticket.from_station_id,
                    CheckPlan.status.in_(['pending', 'checking'])
                ).first()
            
            now = datetime.now()
            current_time = now.strftime('%H:%M')
            current_minutes = int(current_time.split(':')[0]) * 60 + int(current_time.split(':')[1])
            
            is_valid = True
            reject_reason = None
            
            # 检查车票状态
            if ticket.status != 'paid':
                is_valid = False
                reject_reason = '车票状态异常：' + ticket.status
            
            # 检查日期
            if ticket.departure_date != today:
                is_valid = False
                reject_reason = '车票日期不符：需今日有效车票'
            
            # 检查车次是否在检票时间
            if plan and plan.status == 'checking':
                start_minutes = int(plan.check_start_time.split(':')[0]) * 60 + int(plan.check_start_time.split(':')[1])
                end_minutes = int(plan.check_end_time.split(':')[0]) * 60 + int(plan.check_end_time.split(':')[1])
                
                if current_minutes < start_minutes:
                    is_valid = False
                    reject_reason = f'检票尚未开始，{plan.check_start_time}开始检票'
                elif current_minutes > end_minutes:
                    is_valid = False
                    reject_reason = f'已过检票时间，{plan.check_end_time}停止检票'
            elif not plan:
                # 没有检票计划，检查是否在开车前30分钟到前5分钟
                dep_parts = train.departure_time.split(':')
                dep_minutes = int(dep_parts[0]) * 60 + int(dep_parts[1])
                
                if current_minutes < dep_minutes - 30:
                    is_valid = False
                    reject_reason = '距离开车不足30分钟，请稍后检票'
                elif current_minutes > dep_minutes - 5:
                    is_valid = False
                    reject_reason = '距离开车不足5分钟，停止检票'
            
            # 创建检票记录
            gate_check = GateCheck(
                gate_id=gate_id,
                ticket_id=ticket.id if ticket else None,
                check_plan_id=plan.id if plan else None,
                check_method=check_method,
                check_result='pass' if is_valid else 'reject',
                reject_reason=reject_reason,
                passenger_name=passenger_name,
                passenger_id_card=passenger_id,
                train_code=train.train_code if train else None,
                checked_at=now,
                operator_id=session.get('gate_user_id')
            )
            
            # 如果是二维码扫描，还需要更新车票状态
            if is_valid and check_method == 'qrcode' and ticket:
                ticket.status = 'used'
            
            db.session.add(gate_check)
            db.session.commit()
            
            return render_template('gate/check.html',
                                 result='pass' if is_valid else 'reject',
                                 ticket=ticket,
                                 train=train,
                                 reject_reason=reject_reason,
                                 gate_id=gate_id,
                                 check_plan_id=check_plan_id)
        else:
            # 未找到车票
            gate_id = request.form.get('gate_id', type=int)
            check_plan_id = request.form.get('check_plan_id', type=int)
            
            # 创建拒绝记录
            gate_check = GateCheck(
                gate_id=gate_id,
                check_method=check_method,
                check_result='reject',
                reject_reason='未找到有效车票，请核实订单信息',
                checked_at=datetime.now(),
                operator_id=session.get('gate_user_id')
            )
            db.session.add(gate_check)
            db.session.commit()
            
            return render_template('gate/check.html',
                                 result='reject',
                                 ticket=None,
                                 train=None,
                                 reject_reason='未找到有效车票，请核实订单信息',
                                 gate_id=gate_id,
                                 check_plan_id=check_plan_id)
    
    # GET请求：显示检票页面
    # 获取当前检票中的车次列表
    checking_plans = CheckPlan.query.filter(
        CheckPlan.status == 'checking'
    ).all()
    
    # 获取所有闸机
    all_gates = Gate.query.all()
    
    # 获取今天的检票记录（用于显示流水）
    recent_checks = GateCheck.query.filter(
        GateCheck.checked_at >= datetime.now().replace(hour=0, minute=0, second=0)
    ).order_by(GateCheck.checked_at.desc()).limit(10).all()
    
    return render_template('gate/check.html',
                         checking_plans=checking_plans,
                         gates=all_gates,
                         recent_checks=recent_checks)


@gate_bp.route('/manual-review')
@gate_login_required
def manual_review():
    """人工复核列表"""
    # 获取需要人工复核的记录
    # 逻辑：创建时标记为需要复核的记录
    pending_reviews = GateCheck.query.filter(
        GateCheck.check_result == 'pending_review'
    ).order_by(GateCheck.checked_at.desc()).all()
    
    return render_template('gate/manual_review.html',
                         pending_reviews=pending_reviews)


@gate_bp.route('/manual-review/<int:check_id>/approve', methods=['POST'])
@gate_login_required
def manual_approve(check_id):
    """人工放行"""
    check_record = GateCheck.query.get_or_404(check_id)
    
    check_record.check_result = 'pass'
    check_record.operator_id = session.get('gate_user_id')
    
    # 如果有关联车票，更新状态
    if check_record.ticket_id:
        ticket = Ticket.query.get(check_record.ticket_id)
        if ticket:
            ticket.status = 'used'
    
    db.session.commit()
    
    flash('人工放行成功', 'success')
    return redirect(url_for('gate.manual_review'))


@gate_bp.route('/manual-review/<int:check_id>/reject', methods=['POST'])
@gate_login_required
def manual_reject(check_id):
    """人工拒绝"""
    check_record = GateCheck.query.get_or_404(check_id)
    reason = request.form.get('reason', '人工复核拒绝')
    
    check_record.check_result = 'reject'
    check_record.reject_reason = reason
    check_record.operator_id = session.get('gate_user_id')
    
    db.session.commit()
    
    flash('已标记为拒绝', 'success')
    return redirect(url_for('gate.manual_review'))


@gate_bp.route('/check-plans')
@gate_login_required
def check_plans():
    """检票计划列表"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 获取所有检票计划
    plans = CheckPlan.query.order_by(CheckPlan.created_at.desc()).all()
    
    # 按状态分组
    plans_by_status = {
        'checking': [],
        'pending': [],
        'finished': []
    }
    
    for plan in plans:
        # 检查日期是否有效
        if plan.effective_date not in [today, 'daily']:
            continue
            
        if plan.status == 'checking':
            plans_by_status['checking'].append(plan)
        elif plan.status == 'pending':
            plans_by_status['pending'].append(plan)
        else:
            plans_by_status['finished'].append(plan)
    
    # 获取关联信息
    plans_info = []
    for status, plan_list in plans_by_status.items():
        for plan in plan_list:
            train = Train.query.get(plan.train_id)
            station = Station.query.get(plan.station_id)
            
            # 计算已检票人数
            checked_count = GateCheck.query.filter(
                GateCheck.check_plan_id == plan.id,
                GateCheck.check_result == 'pass'
            ).count()
            
            plans_info.append({
                'plan': plan,
                'train': train,
                'station': station,
                'checked_count': checked_count
            })
    
    return render_template('gate/check_plans.html',
                         plans_info=plans_info)


@gate_bp.route('/check-plans/new', methods=['GET', 'POST'])
@gate_login_required
def new_check_plan():
    """新建检票计划"""
    if request.method == 'POST':
        train_id = request.form.get('train_id', type=int)
        station_id = request.form.get('station_id', type=int)
        gate_ids = request.form.getlist('gate_ids')
        check_start_time = request.form.get('check_start_time')
        check_end_time = request.form.get('check_end_time')
        effective_date = request.form.get('effective_date')
        
        if not all([train_id, station_id, check_start_time, check_end_time, effective_date]):
            flash('请填写所有必填项', 'error')
            return redirect(url_for('gate.new_check_plan'))
        
        # 创建检票计划
        plan = CheckPlan(
            train_id=train_id,
            station_id=station_id,
            gate_ids=','.join(map(str, gate_ids)),
            check_start_time=check_start_time,
            check_end_time=check_end_time,
            effective_date=effective_date,
            status='pending',
            created_by=session.get('gate_user_id')
        )
        
        db.session.add(plan)
        db.session.commit()
        
        flash('检票计划创建成功', 'success')
        return redirect(url_for('gate.check_plans'))
    
    # 获取车次列表（今天有票的车次）
    today = datetime.now().strftime('%Y-%m-%d')
    trains_with_tickets = db.session.query(Train).join(
        Ticket, Ticket.train_id == Train.id
    ).filter(
        Ticket.departure_date == today,
        Ticket.status.in_(['paid', 'used'])
    ).distinct().all()
    
    # 获取所有车站
    stations = Station.query.filter(
        Station.is_high_speed == 1
    ).order_by(Station.station_name).all()
    
    # 获取所有闸机
    gates = Gate.query.order_by(Gate.station_id, Gate.gate_code).all()
    
    return render_template('gate/check_plan_form.html',
                         trains=trains_with_tickets,
                         stations=stations,
                         gates=gates,
                         today=today)


@gate_bp.route('/check-plans/<int:plan_id>/start')
@gate_login_required
def start_check_plan(plan_id):
    """开始检票"""
    plan = CheckPlan.query.get_or_404(plan_id)
    
    plan.status = 'checking'
    db.session.commit()
    
    flash(f'车次 {plan.train.train_code if plan.train else ""} 开始检票', 'success')
    return redirect(url_for('gate.check_plans'))


@gate_bp.route('/check-plans/<int:plan_id>/finish')
@gate_login_required
def finish_check_plan(plan_id):
    """结束检票"""
    plan = CheckPlan.query.get_or_404(plan_id)
    
    plan.status = 'finished'
    db.session.commit()
    
    flash(f'车次 {plan.train.train_code if plan.train else ""} 结束检票', 'success')
    return redirect(url_for('gate.check_plans'))


@gate_bp.route('/gates')
@gate_login_required
def gates():
    """闸机设备列表"""
    all_gates = Gate.query.order_by(Gate.station_id, Gate.gate_code).all()
    
    # 按车站分组
    gates_by_station = {}
    for gate in all_gates:
        station_name = gate.station.station_name if gate.station else '未知'
        if station_name not in gates_by_station:
            gates_by_station[station_name] = {
                'station': gate.station,
                'gates': []
            }
        gates_by_station[station_name]['gates'].append(gate)
    
    return render_template('gate/gates.html',
                         gates_by_station=gates_by_station)


@gate_bp.route('/gates/new', methods=['GET', 'POST'])
@gate_login_required
def new_gate():
    """新增闸机"""
    if request.method == 'POST':
        gate_code = request.form.get('gate_code', '').strip()
        gate_name = request.form.get('gate_name', '').strip()
        station_id = request.form.get('station_id', type=int)
        gate_type = request.form.get('gate_type', 'entry')
        location = request.form.get('location', '').strip()
        
        if not all([gate_code, gate_name, station_id]):
            flash('请填写所有必填项', 'error')
            return redirect(url_for('gate.new_gate'))
        
        # 检查编号是否已存在
        if Gate.query.filter_by(gate_code=gate_code).first():
            flash('闸机编号已存在', 'error')
            return redirect(url_for('gate.new_gate'))
        
        gate = Gate(
            gate_code=gate_code,
            gate_name=gate_name,
            station_id=station_id,
            gate_type=gate_type,
            location=location,
            status='offline',
            last_heartbeat=datetime.now()
        )
        
        db.session.add(gate)
        db.session.commit()
        
        flash('闸机添加成功', 'success')
        return redirect(url_for('gate.gates'))
    
    stations = Station.query.filter(
        Station.is_high_speed == 1
    ).order_by(Station.station_name).all()
    
    return render_template('gate/gate_form.html',
                         stations=stations,
                         gate=None)


@gate_bp.route('/gates/<int:gate_id>/edit', methods=['GET', 'POST'])
@gate_login_required
def edit_gate(gate_id):
    """编辑闸机"""
    gate = Gate.query.get_or_404(gate_id)
    
    if request.method == 'POST':
        gate.gate_code = request.form.get('gate_code', '').strip()
        gate.gate_name = request.form.get('gate_name', '').strip()
        gate.station_id = request.form.get('station_id', type=int)
        gate.gate_type = request.form.get('gate_type', 'entry')
        gate.location = request.form.get('location', '').strip()
        
        db.session.commit()
        
        flash('闸机信息更新成功', 'success')
        return redirect(url_for('gate.gates'))
    
    stations = Station.query.filter(
        Station.is_high_speed == 1
    ).order_by(Station.station_name).all()
    
    return render_template('gate/gate_form.html',
                         stations=stations,
                         gate=gate)


@gate_bp.route('/gates/<int:gate_id>/toggle-status', methods=['POST'])
@gate_login_required
def toggle_gate_status(gate_id):
    """切换闸机状态"""
    gate = Gate.query.get_or_404(gate_id)
    
    # 切换状态
    status_cycle = {
        'online': 'maintenance',
        'maintenance': 'online',
        'offline': 'online',
        'fault': 'maintenance'
    }
    
    gate.status = status_cycle.get(gate.status, 'online')
    gate.last_heartbeat = datetime.now()
    db.session.commit()
    
    status_names = {
        'online': '在线',
        'offline': '离线',
        'maintenance': '维护',
        'fault': '故障'
    }
    
    flash(f'闸机 {gate.gate_code} 状态已更新为：{status_names.get(gate.status)}', 'success')
    return redirect(url_for('gate.gates'))


@gate_bp.route('/statistics')
@gate_login_required
def statistics():
    """统计报表"""
    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    
    # 今日统计
    today_checks = GateCheck.query.filter(
        db.func.date(GateCheck.checked_at) == today_str
    ).all()
    
    today_total = len(today_checks)
    today_pass = len([c for c in today_checks if c.check_result == 'pass'])
    today_reject = today_total - today_pass
    today_pass_rate = (today_pass / today_total * 100) if today_total > 0 else 0
    
    # 本周统计
    week_start = today - timedelta(days=today.weekday())
    week_checks = GateCheck.query.filter(
        GateCheck.checked_at >= week_start
    ).all()
    
    week_total = len(week_checks)
    week_pass = len([c for c in week_checks if c.check_result == 'pass'])
    week_reject = week_total - week_pass
    
    # 按小时统计今日
    hourly_stats = []
    for hour in range(24):
        hour_checks = [c for c in today_checks 
                      if c.checked_at.hour == hour]
        hourly_stats.append({
            'hour': f'{hour:02d}:00',
            'total': len(hour_checks),
            'pass': len([c for c in hour_checks if c.check_result == 'pass']),
            'reject': len([c for c in hour_checks if c.check_result == 'reject'])
        })
    
    # 按车站统计
    station_stats = db.session.query(
        Station.station_name,
        db.func.count(GateCheck.id).label('total'),
        db.func.sum(db.case((GateCheck.check_result == 'pass', 1), else_=0)).label('pass_count')
    ).join(Gate, Gate.station_id == Station.id).join(
        GateCheck, GateCheck.gate_id == Gate.id
    ).filter(
        db.func.date(GateCheck.checked_at) == today_str
    ).group_by(Station.id, Station.station_name).all()
    
    # 拒绝原因统计
    reject_reasons = {}
    for check in today_checks:
        if check.check_result == 'reject' and check.reject_reason:
            reason = check.reject_reason
            reject_reasons[reason] = reject_reasons.get(reason, 0) + 1
    
    sorted_reasons = sorted(reject_reasons.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return render_template('gate/statistics.html',
                         today_total=today_total,
                         today_pass=today_pass,
                         today_reject=today_reject,
                         today_pass_rate=round(today_pass_rate, 1),
                         week_total=week_total,
                         week_pass=week_pass,
                         week_reject=week_reject,
                         hourly_stats=hourly_stats,
                         station_stats=station_stats,
                         reject_reasons=sorted_reasons)
