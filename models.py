from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    real_name = db.Column(db.String(100))
    id_card = db.Column(db.String(18))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    user_type = db.Column(db.String(20), default='passenger')  # admin/staff/passenger
    status = db.Column(db.String(20), default='active')  # active/disabled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Station(db.Model):
    __tablename__ = 'stations'
    
    id = db.Column(db.Integer, primary_key=True)
    station_code = db.Column(db.String(10), unique=True, nullable=False)
    station_name = db.Column(db.String(50), nullable=False)
    pinyin = db.Column(db.String(100))
    city = db.Column(db.String(50))
    province = db.Column(db.String(50))
    station_level = db.Column(db.String(20))  # 特等/一等/二等/三等
    is_high_speed = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Train(db.Model):
    __tablename__ = 'trains'
    
    id = db.Column(db.Integer, primary_key=True)
    train_code = db.Column(db.String(20), unique=True, nullable=False)
    train_type = db.Column(db.String(20), nullable=False)  # 高铁/动车/普速/城际
    start_station_id = db.Column(db.Integer, db.ForeignKey('stations.id'))
    end_station_id = db.Column(db.Integer, db.ForeignKey('stations.id'))
    departure_time = db.Column(db.String(10))  # HH:MM
    arrival_time = db.Column(db.String(10))  # HH:MM
    duration = db.Column(db.Integer)  # 分钟
    total_distance = db.Column(db.Integer)  # 公里
    is_active = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    start_station = db.relationship('Station', foreign_keys=[start_station_id])
    end_station = db.relationship('Station', foreign_keys=[end_station_id])
    stops = db.relationship('TrainStop', backref='train', lazy='dynamic', order_by='TrainStop.stop_order')
    seats = db.relationship('TrainSeat', backref='train', lazy='dynamic')


class TrainStop(db.Model):
    __tablename__ = 'train_stops'
    
    id = db.Column(db.Integer, primary_key=True)
    train_id = db.Column(db.Integer, db.ForeignKey('trains.id'))
    station_id = db.Column(db.Integer, db.ForeignKey('stations.id'))
    stop_order = db.Column(db.Integer)
    arrival_time = db.Column(db.String(10))
    departure_time = db.Column(db.String(10))
    stop_duration = db.Column(db.Integer)  # 分钟
    distance_from_start = db.Column(db.Integer)  # 公里
    
    station = db.relationship('Station')


class SeatType(db.Model):
    __tablename__ = 'seat_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    code = db.Column(db.String(10), unique=True)
    base_price_rate = db.Column(db.Float, default=1.0)
    description = db.Column(db.String(100))


class TrainSeat(db.Model):
    __tablename__ = 'train_seats'
    
    id = db.Column(db.Integer, primary_key=True)
    train_id = db.Column(db.Integer, db.ForeignKey('trains.id'))
    seat_type_id = db.Column(db.Integer, db.ForeignKey('seat_types.id'))
    total_count = db.Column(db.Integer, default=100)
    available_count = db.Column(db.Integer, default=100)
    price = db.Column(db.Float)
    
    seat_type = db.relationship('SeatType')


class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    train_id = db.Column(db.Integer, db.ForeignKey('trains.id'))
    from_station_id = db.Column(db.Integer, db.ForeignKey('stations.id'))
    to_station_id = db.Column(db.Integer, db.ForeignKey('stations.id'))
    seat_type_id = db.Column(db.Integer, db.ForeignKey('seat_types.id'))
    departure_date = db.Column(db.String(20))  # YYYY-MM-DD
    departure_time = db.Column(db.String(10))
    arrival_time = db.Column(db.String(10))
    car_number = db.Column(db.String(10))
    seat_number = db.Column(db.String(10))
    price = db.Column(db.Float)
    status = db.Column(db.String(20), default='paid')  # unpaid/paid/cancelled/refunded/used
    passenger_name = db.Column(db.String(100))
    passenger_id_card = db.Column(db.String(18))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)
    
    user = db.relationship('User', backref='tickets')
    train = db.relationship('Train')
    from_station = db.relationship('Station', foreign_keys=[from_station_id])
    to_station = db.relationship('Station', foreign_keys=[to_station_id])
    seat_type = db.relationship('SeatType')
    payment = db.relationship('Payment', backref='ticket', uselist=False)
    refund = db.relationship('Refund', backref='ticket', uselist=False)


class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'))
    amount = db.Column(db.Float)
    pay_method = db.Column(db.String(20))  # 支付宝/微信/银行卡
    pay_status = db.Column(db.String(20), default='success')  # pending/success/failed
    transaction_no = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Refund(db.Model):
    __tablename__ = 'refunds'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'))
    refund_amount = db.Column(db.Float)
    refund_fee = db.Column(db.Float, default=0)
    reason = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')  # pending/approved/rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Announcement(db.Model):
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    type = db.Column(db.String(20), default='notice')  # notice/announcement/cancel
    is_active = db.Column(db.Integer, default=1)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    creator = db.relationship('User')


class TrainScheduleChange(db.Model):
    __tablename__ = 'train_schedule_changes'
    
    id = db.Column(db.Integer, primary_key=True)
    train_id = db.Column(db.Integer, db.ForeignKey('trains.id'))
    change_type = db.Column(db.String(20))  # cancel/delay/change
    reason = db.Column(db.String(200))
    effective_date = db.Column(db.String(20))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    train = db.relationship('Train')


class OperationLog(db.Model):
    __tablename__ = 'operation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(50))
    module = db.Column(db.String(50))
    detail = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User')
