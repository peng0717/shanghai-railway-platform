import sys
import os

def init_database(app, db):
    """初始化数据库"""
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("数据库表创建完成")
        
        # 检查是否需要加载种子数据
        from models import User, Station, SeatType
        if User.query.count() == 0:
            print("正在加载种子数据...")
            load_seed_data(db)
            print("种子数据加载完成")
        else:
            print("数据库已存在数据，跳过种子数据加载")


def load_seed_data(db):
    """加载种子数据"""
    from models import (
        User, Station, Train, TrainStop, SeatType, TrainSeat,
        Announcement
    )
    from datetime import datetime, timedelta
    import random
    
    # 创建席别数据
    seat_types = [
        SeatType(name='商务座', code='BS', base_price_rate=3.0, description='最高等级座位，空间宽敞'),
        SeatType(name='一等座', code='YS', base_price_rate=1.8, description='舒适座位，适合长途旅行'),
        SeatType(name='二等座', code='ES', base_price_rate=1.0, description='经济实惠，座椅舒适'),
        SeatType(name='特等座', code='TS', base_price_rate=2.0, description='独立包厢，尊贵体验'),
        SeatType(name='硬卧', code='YW', base_price_rate=0.6, description='硬质卧铺，适合过夜'),
        SeatType(name='软卧', code='RW', base_price_rate=0.8, description='软质卧铺，舒适休息'),
        SeatType(name='硬座', code='YZ', base_price_rate=0.4, description='基础座位，经济之选'),
        SeatType(name='无座', code='WZ', base_price_rate=0.35, description='无固定座位'),
    ]
    db.session.add_all(seat_types)
    db.session.commit()
    
    # 创建用户
    admin = User(
        username='admin',
        real_name='系统管理员',
        user_type='admin',
        status='active'
    )
    admin.set_password('admin123')
    
    demo = User(
        username='demo',
        real_name='演示用户',
        user_type='passenger',
        status='active'
    )
    demo.set_password('demo123')
    
    staff = User(
        username='staff',
        real_name='运营职工',
        user_type='staff',
        status='active'
    )
    staff.set_password('staff123')
    
    db.session.add_all([admin, demo, staff])
    db.session.commit()
    
    # 创建站点数据
    stations_data = [
        # 上海市
        ('SHA', '上海', 'Shanghai', '上海', '上海', '特等', 1),
        ('SHH', '上海虹桥', 'ShanghaiHongqiao', '上海', '上海', '特等', 1),
        ('SNH', '上海南', 'ShanghaiNan', '上海', '上海', '一等', 1),
        ('SHX', '上海西', 'ShanghaiXi', '上海', '上海', '一等', 1),
        ('SAJ', '松江', 'Songjiang', '上海', '上海', '二等', 1),
        ('NBE', '南翔北', 'Nanxiangbei', '上海', '上海', '二等', 0),
        ('ATB', '安亭北', 'Antingbei', '上海', '上海', '二等', 1),
        ('HQB', '花桥', 'Huaqiao', '苏州', '上海', '二等', 1),
        ('JTB', '金山北', 'Jinshanbei', '上海', '上海', '二等', 1),
        ('LCG', '芦潮港', 'LuchaoGang', '上海', '上海', '三等', 0),
        ('XNH', '新桥', 'Xinqiao', '上海', '上海', '三等', 0),
        ('CHZ', '春申', 'Chunshen', '上海', '上海', '三等', 0),
        ('QIB', '七宝', 'Qibao', '上海', '上海', '三等', 0),
        ('MIN', '闵行', 'Minhang', '上海', '上海', '三等', 0),
        ('XZB', '莘庄', 'Xinzhuang', '上海', '上海', '三等', 0),
        
        # 江苏省 - 南京无锡苏州
        ('NJH', '南京', 'Nanjing', '南京', '江苏', '特等', 1),
        ('NKH', '南京南', 'Nanjingnan', '南京', '江苏', '特等', 1),
        ('NJX', '南京西', 'Nanjingxi', '南京', '江苏', '一等', 0),
        ('SZH', '苏州', 'Suzhou', '苏州', '江苏', '一等', 1),
        ('SBN', '苏州北', 'Suzhoubei', '苏州', '江苏', '一等', 1),
        ('SZQ', '苏州园区', 'Suzhouyuanqu', '苏州', '江苏', '二等', 1),
        ('SXX', '苏州新区', 'Suzhouxinqu', '苏州', '江苏', '二等', 1),
        ('WXH', '无锡', 'Wuxi', '无锡', '江苏', '一等', 1),
        ('WXD', '无锡东', 'Wuxidong', '无锡', '江苏', '一等', 1),
        ('WXX', '无锡新区', 'Wuxixinqu', '无锡', '江苏', '二等', 1),
        ('HSH', '惠山', 'Huishan', '无锡', '江苏', '二等', 1),
        ('CZH', '常州', 'Changzhou', '常州', '江苏', '一等', 1),
        ('CZN', '常州北', 'Changzhoubei', '常州', '江苏', '二等', 1),
        ('QSY', '戚墅堰', 'Qishuyan', '常州', '江苏', '三等', 0),
        ('DYH', '丹阳', 'Danyang', '镇江', '江苏', '二等', 1),
        ('DYB', '丹阳北', 'Danyangbei', '镇江', '江苏', '二等', 1),
        ('ZJH', '镇江', 'Zhenjiang', '镇江', '江苏', '一等', 1),
        ('ZJN', '镇江南', 'Zhenjiangnan', '镇江', '江苏', '二等', 1),
        ('BHS', '宝华山', 'Baohuashan', '镇江', '江苏', '三等', 0),
        
        # 江苏省 - 昆山徐州连云港
        ('KSH', '昆山', 'Kunshan', '苏州', '江苏', '二等', 0),
        ('KSN', '昆山南', 'Kunshannan', '苏州', '江苏', '一等', 1),
        ('YCY', '阳澄湖', 'Yangchenghu', '苏州', '江苏', '三等', 1),
        ('XZH', '徐州', 'Xuzhou', '徐州', '江苏', '特等', 1),
        ('XZN', '徐州东', 'Xuzhoudong', '徐州', '江苏', '特等', 1),
        ('PZH', '邳州', 'Pizhou', '徐州', '江苏', '二等', 0),
        ('XYH', '新沂', 'Xinyi', '徐州', '江苏', '二等', 0),
        ('LGH', '连云港', 'Lianyungang', '连云港', '江苏', '一等', 1),
        ('LGD', '连云港东', 'Lianyungangdong', '连云港', '江苏', '二等', 0),
        ('DHX', '东海县', 'Donghaixian', '连云港', '江苏', '三等', 0),
        ('HAB', '淮安', 'Huaian', '淮安', '江苏', '二等', 1),
        ('HAN', '淮安南', 'Huaiannan', '淮安', '江苏', '三等', 0),
        
        # 江苏省 - 盐城南通泰州扬州
        ('YCH', '盐城', 'Yancheng', '盐城', '江苏', '二等', 1),
        ('DTZ', '东台', 'Dongtai', '盐城', '江苏', '三等', 0),
        ('NTH', '南通', 'Nantong', '南通', '江苏', '一等', 1),
        ('RGC', '如皋', 'Rugao', '南通', '江苏', '三等', 0),
        ('HAX', '海安县', 'Haianxian', '南通', '江苏', '三等', 0),
        ('TZH', '泰州', 'Taizhou', '泰州', '江苏', '二等', 1),
        ('JYZ', '姜堰', 'Jiangyan', '泰州', '江苏', '三等', 0),
        ('YZH', '扬州', 'Yangzhou', '扬州', '江苏', '二等', 1),
        ('JDH', '江都', 'Jiangdu', '扬州', '江苏', '三等', 0),
        ('YZG', '仪征', 'Yizheng', '扬州', '江苏', '三等', 0),
        ('JHZ', '建湖', 'Jianhu', '盐城', '江苏', '三等', 0),
        ('FNZ', '阜宁', 'Funing', '盐城', '江苏', '三等', 0),
        ('SYZ', '沭阳', 'Shuyang', '宿迁', '江苏', '三等', 0),
        
        # 浙江省 - 杭州宁波温州
        ('HZH', '杭州', 'Hangzhou', '杭州', '浙江', '特等', 1),
        ('HZN', '杭州东', 'Hangzhoudong', '杭州', '浙江', '特等', 1),
        ('HXB', '杭州南', 'Hangzhounan', '杭州', '浙江', '一等', 1),
        ('HZX', '杭州西', 'Hangzhouxi', '杭州', '浙江', '一等', 1),
        ('NBH', '宁波', 'Ningbo', '宁波', '浙江', '一等', 1),
        ('NBD', '宁波东', 'Ningbodong', '宁波', '浙江', '二等', 0),
        ('WZH', '温州', 'Wenzhou', '温州', '浙江', '一等', 1),
        ('WWN', '温州南', 'Wenzhounan', '温州', '浙江', '一等', 1),
        ('YQZ', '乐清', 'Yueqing', '温州', '浙江', '二等', 1),
        ('YJZ', '永嘉', 'Yongjia', '温州', '浙江', '二等', 1),
        ('YDS', '雁荡山', 'Yandangshan', '温州', '浙江', '三等', 1),
        
        # 浙江省 - 绍兴金华衢州
        ('SZX', '绍兴', 'Shaoxing', '绍兴', '浙江', '二等', 1),
        ('SYZ', '上虞', 'Shangyu', '绍兴', '浙江', '三等', 0),
        ('YWH', '义乌', 'Yiwu', '金华', '浙江', '一等', 1),
        ('ZJZ', '诸暨', 'Zhuji', '绍兴', '浙江', '二等', 0),
        ('JHW', '金华', 'Jinhua', '金华', '浙江', '一等', 1),
        ('JHN', '金华南', 'Jinhuanan', '金华', '浙江', '二等', 1),
        ('QZH', '衢州', 'Quzhou', '衢州', '浙江', '二等', 1),
        ('LYZ', '龙游', 'Longyou', '衢州', '浙江', '三等', 0),
        ('LXX', '兰溪', 'Lanxi', '金华', '浙江', '三等', 0),
        ('JSA', '江山', 'Jiangshan', '衢州', '浙江', '二等', 1),
        
        # 浙江省 - 嘉兴湖州台州丽水
        ('JXZ', '嘉兴', 'Jiaxing', '嘉兴', '浙江', '二等', 1),
        ('JXN', '嘉兴南', 'Jiaxingnan', '嘉兴', '浙江', '二等', 1),
        ('JSZ', '嘉善', 'Jiashan', '嘉兴', '浙江', '三等', 0),
        ('JSB', '嘉善南', 'Jiashannan', '嘉兴', '浙江', '二等', 1),
        ('HNZ', '海宁', 'Haining', '嘉兴', '浙江', '二等', 0),
        ('HNX', '海宁西', 'Hainingxi', '嘉兴', '浙江', '二等', 1),
        ('TXZ', '桐乡', 'Tongxiang', '嘉兴', '浙江', '二等', 1),
        ('DQZ', '德清', 'Deqing', '湖州', '浙江', '二等', 1),
        ('CYZ', '长兴', 'Changxing', '湖州', '浙江', '三等', 0),
        ('CNZ', '苍南', 'Cangnan', '温州', '浙江', '三等', 1),
        ('TZH', '台州', 'Taizhou', '台州', '浙江', '二等', 1),
        ('WLZ', '温岭', 'Wenling', '台州', '浙江', '二等', 1),
        ('LSH', '丽水', 'Lishui', '丽水', '浙江', '二等', 1),
        
        # 安徽省 - 合肥蚌埠阜阳
        ('HFH', '合肥', 'Hefei', '合肥', '安徽', '特等', 1),
        ('HFN', '合肥南', 'Hefeinan', '合肥', '安徽', '特等', 1),
        ('HFX', '合肥西', 'HefeiXi', '合肥', '安徽', '二等', 1),
        ('BBH', '蚌埠', 'Bengbu', '蚌埠', '安徽', '一等', 1),
        ('BBN', '蚌埠南', 'Bengbunan', '蚌埠', '安徽', '一等', 1),
        ('HNZ', '淮南', 'Huainan', '淮南', '安徽', '二等', 0),
        ('FYH', '阜阳', 'Fuyang', '阜阳', '安徽', '一等', 0),
        ('FYN', '阜阳北', 'Fuyangbei', '阜阳', '安徽', '一等', 0),
        ('BNZ', '亳州', 'Bozhou', '亳州', '安徽', '二等', 0),
        ('HBE', '淮北', 'Huaibei', '淮北', '安徽', '二等', 0),
        ('WYZ', '涡阳', 'Woyang', '亳州', '安徽', '三等', 0),
        
        # 安徽省 - 芜湖马鞍山宣城黄山
        ('WHH', '芜湖', 'Wuhu', '芜湖', '安徽', '一等', 1),
        ('MAZ', '马鞍山', 'Maanshan', '马鞍山', '安徽', '二等', 1),
        ('XCZ', '宣城', 'Xuancheng', '宣城', '安徽', '二等', 0),
        ('NGZ', '宁国', 'Ningguo', '宣城', '安徽', '三等', 0),
        ('HSZ', '黄山', 'Huangshan', '黄山', '安徽', '二等', 1),
        ('HBN', '黄山北', 'Huangshannan', '黄山', '安徽', '二等', 1),
        ('JXX', '绩溪县', 'Jixixian', '宣城', '安徽', '三等', 0),
        ('TLZ', '铜陵', 'Tongling', '铜陵', '安徽', '二等', 1),
        ('CHZ', '池州', 'Chizhou', '池州', '安徽', '二等', 0),
        ('AQH', '安庆', 'Anqing', '安庆', '安徽', '二等', 1),
        ('AQX', '安庆西', 'Anqingxi', '安庆', '安徽', '三等', 0),
        
        # 安徽省 - 六安滁州其他
        ('LAZ', '六安', 'LiuAn', '六安', '安徽', '二等', 1),
        ('JPZ', '金寨', 'Jinzhai', '六安', '安徽', '三等', 1),
        ('CHH', '巢湖', 'Chaohu', '合肥', '安徽', '三等', 0),
        ('LJZ', '庐江', 'Lujiang', '合肥', '安徽', '三等', 1),
        ('SCZ', '舒城', 'Shucheng', '合肥', '安徽', '三等', 0),
        ('TCZ', '桐城', 'Tongcheng', '安庆', '安徽', '三等', 0),
        ('QJZ', '全椒', 'Quanjiao', '滁州', '安徽', '三等', 1),
        ('DYH', '定远', 'Dingyuan', '滁州', '安徽', '三等', 1),
        ('SSZ', '宿松', 'Susong', '安庆', '安徽', '三等', 0),
        ('THZ', '太湖', 'Taihu', '安庆', '安徽', '三等', 0),
        ('TZS', '天柱山', 'Tianzhushan', '安庆', '安徽', '三等', 0),
    ]
    
    stations = []
    for data in stations_data:
        station = Station(
            station_code=data[0],
            station_name=data[1],
            pinyin=data[2],
            city=data[3],
            province=data[4],
            station_level=data[5],
            is_high_speed=data[6]
        )
        stations.append(station)
    
    db.session.add_all(stations)
    db.session.commit()
    
    # 创建车次数据
    train_data = []
    
    # 京沪高铁线
    train_data.extend([
        {'code': 'G1', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '07:00', 'arr': '11:30', 'dur': 270, 'dist': 1318},
        {'code': 'G3', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '09:00', 'arr': '13:28', 'dur': 268, 'dist': 1318},
        {'code': 'G5', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '11:00', 'arr': '15:28', 'dur': 268, 'dist': 1318},
        {'code': 'G7', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '13:00', 'arr': '17:28', 'dur': 268, 'dist': 1318},
        {'code': 'G9', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '15:00', 'arr': '19:28', 'dur': 268, 'dist': 1318},
        {'code': 'G101', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '08:00', 'arr': '13:05', 'dur': 305, 'dist': 1318},
        {'code': 'G103', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '10:00', 'arr': '15:05', 'dur': 305, 'dist': 1318},
        {'code': 'G105', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '14:00', 'arr': '19:05', 'dur': 305, 'dist': 1318},
    ])
    
    # 沪宁城际线
    train_data.extend([
        {'code': 'G7001', 'type': '高铁', 'start': 'SHA', 'end': 'NJH', 'dep': '06:00', 'arr': '07:30', 'dur': 90, 'dist': 301},
        {'code': 'G7003', 'type': '高铁', 'start': 'SHA', 'end': 'NJH', 'dep': '06:30', 'arr': '08:00', 'dur': 90, 'dist': 301},
        {'code': 'G7005', 'type': '高铁', 'start': 'SHA', 'end': 'NJH', 'dep': '07:00', 'arr': '08:30', 'dur': 90, 'dist': 301},
        {'code': 'G7007', 'type': '高铁', 'start': 'SHA', 'end': 'NJH', 'dep': '07:30', 'arr': '09:00', 'dur': 90, 'dist': 301},
        {'code': 'G7009', 'type': '高铁', 'start': 'SHA', 'end': 'NJH', 'dep': '08:00', 'arr': '09:30', 'dur': 90, 'dist': 301},
        {'code': 'C3001', 'type': '城际', 'start': 'SHA', 'end': 'NJH', 'dep': '06:15', 'arr': '07:50', 'dur': 95, 'dist': 301},
        {'code': 'C3003', 'type': '城际', 'start': 'SHA', 'end': 'NJH', 'dep': '07:15', 'arr': '08:50', 'dur': 95, 'dist': 301},
        {'code': 'C3005', 'type': '城际', 'start': 'SHA', 'end': 'NJH', 'dep': '08:15', 'arr': '09:50', 'dur': 95, 'dist': 301},
    ])
    
    # 沪昆高铁线
    train_data.extend([
        {'code': 'G1341', 'type': '高铁', 'start': 'SHH', 'end': 'CSQ', 'dep': '08:00', 'arr': '12:30', 'dur': 270, 'dist': 1150},
        {'code': 'G1343', 'type': '高铁', 'start': 'SHH', 'end': 'CSQ', 'dep': '09:30', 'arr': '14:00', 'dur': 270, 'dist': 1150},
        {'code': 'G1345', 'type': '高铁', 'start': 'SHH', 'end': 'CSQ', 'dep': '11:00', 'arr': '15:30', 'dur': 270, 'dist': 1150},
        {'code': 'G1347', 'type': '高铁', 'start': 'SHH', 'end': 'CSQ', 'dep': '14:00', 'arr': '18:30', 'dur': 270, 'dist': 1150},
        {'code': 'G1371', 'type': '高铁', 'start': 'SHH', 'end': 'KMG', 'dep': '07:00', 'arr': '19:00', 'dur': 720, 'dist': 2252},
    ])
    
    # 宁杭高铁线
    train_data.extend([
        {'code': 'G7601', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '07:00', 'arr': '08:30', 'dur': 90, 'dist': 256},
        {'code': 'G7603', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '08:00', 'arr': '09:30', 'dur': 90, 'dist': 256},
        {'code': 'G7605', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '09:00', 'arr': '10:30', 'dur': 90, 'dist': 256},
        {'code': 'G7611', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '10:00', 'arr': '11:30', 'dur': 90, 'dist': 256},
    ])
    
    # 合福高铁线
    train_data.extend([
        {'code': 'G1611', 'type': '高铁', 'start': 'HFN', 'end': 'FZS', 'dep': '08:00', 'arr': '12:30', 'dur': 270, 'dist': 780},
        {'code': 'G1613', 'type': '高铁', 'start': 'HFN', 'end': 'FZS', 'dep': '10:00', 'arr': '14:30', 'dur': 270, 'dist': 780},
        {'code': 'G1615', 'type': '高铁', 'start': 'HFN', 'end': 'FZS', 'dep': '14:00', 'arr': '18:30', 'dur': 270, 'dist': 780},
    ])
    
    # 杭深高铁线
    train_data.extend([
        {'code': 'G7501', 'type': '高铁', 'start': 'HZN', 'end': 'SZN', 'dep': '07:00', 'arr': '12:00', 'dur': 300, 'dist': 1100},
        {'code': 'G7503', 'type': '高铁', 'start': 'HZN', 'end': 'SZN', 'dep': '08:00', 'arr': '13:00', 'dur': 300, 'dist': 1100},
        {'code': 'G7505', 'type': '高铁', 'start': 'HZN', 'end': 'SZN', 'dep': '09:00', 'arr': '14:00', 'dur': 300, 'dist': 1100},
        {'code': 'G7511', 'type': '高铁', 'start': 'HZN', 'end': 'SZN', 'dep': '10:00', 'arr': '15:00', 'dur': 300, 'dist': 1100},
    ])
    
    # 京沪普速线
    train_data.extend([
        {'code': 'T110', 'type': '普速', 'start': 'SHA', 'end': 'BJP', 'dep': '18:00', 'arr': '09:00', 'dur': 900, 'dist': 1463},
        {'code': 'T132', 'type': '普速', 'start': 'SHA', 'end': 'BJP', 'dep': '19:00', 'arr': '10:00', 'dur': 900, 'dist': 1463},
        {'code': 'Z166', 'type': '普速', 'start': 'SHA', 'end': 'BJP', 'dep': '20:00', 'arr': '11:00', 'dur': 900, 'dist': 1463},
        {'code': 'K101', 'type': '普速', 'start': 'SHA', 'end': 'BJP', 'dep': '12:00', 'arr': '08:00', 'dur': 1200, 'dist': 1463},
    ])
    
    # 沪昆普速线
    train_data.extend([
        {'code': 'K71', 'type': '普速', 'start': 'SNH', 'end': 'KMG', 'dep': '14:00', 'arr': '21:00', 'dur': 2100, 'dist': 2252},
        {'code': 'K79', 'type': '普速', 'start': 'SNH', 'end': 'KMG', 'dep': '16:00', 'arr': '23:00', 'dur': 2100, 'dist': 2252},
        {'code': 'T77', 'type': '普速', 'start': 'SNH', 'end': 'KMG', 'dep': '18:00', 'arr': '18:00', 'dur': 1440, 'dist': 2252},
    ])
    
    # 宁铜线
    train_data.extend([
        {'code': 'K8421', 'type': '普速', 'start': 'NJH', 'end': 'TLZ', 'dep': '07:00', 'arr': '11:30', 'dur': 270, 'dist': 250},
        {'code': 'T7777', 'type': '普速', 'start': 'NJH', 'end': 'TLZ', 'dep': '13:00', 'arr': '17:30', 'dur': 270, 'dist': 250},
        {'code': 'K1551', 'type': '普速', 'start': 'NJH', 'end': 'TLZ', 'dep': '08:00', 'arr': '12:00', 'dur': 240, 'dist': 250},
    ])
    
    # 沪苏通线
    train_data.extend([
        {'code': 'C3811', 'type': '城际', 'start': 'SHA', 'end': 'NTH', 'dep': '07:00', 'arr': '08:30', 'dur': 90, 'dist': 120},
        {'code': 'C3813', 'type': '城际', 'start': 'SHA', 'end': 'NTH', 'dep': '09:00', 'arr': '10:30', 'dur': 90, 'dist': 120},
        {'code': 'C3815', 'type': '城际', 'start': 'SHA', 'end': 'NTH', 'dep': '11:00', 'arr': '12:30', 'dur': 90, 'dist': 120},
        {'code': 'C3817', 'type': '城际', 'start': 'SHA', 'end': 'NTH', 'dep': '14:00', 'arr': '15:30', 'dur': 90, 'dist': 120},
    ])
    
    # 徐兰高铁安徽段
    train_data.extend([
        {'code': 'G1920', 'type': '高铁', 'start': 'XZN', 'end': 'XAF', 'dep': '08:00', 'arr': '14:00', 'dur': 360, 'dist': 600},
        {'code': 'G1922', 'type': '高铁', 'start': 'XZN', 'end': 'XAF', 'dep': '10:00', 'arr': '16:00', 'dur': 360, 'dist': 600},
    ])
    
    # 合安高铁线
    train_data.extend([
        {'code': 'G9501', 'type': '高铁', 'start': 'HFN', 'end': 'AQH', 'dep': '07:00', 'arr': '08:00', 'dur': 60, 'dist': 180},
        {'code': 'G9503', 'type': '高铁', 'start': 'HFN', 'end': 'AQH', 'dep': '09:00', 'arr': '10:00', 'dur': 60, 'dist': 180},
        {'code': 'G9505', 'type': '高铁', 'start': 'HFN', 'end': 'AQH', 'dep': '11:00', 'arr': '12:00', 'dur': 60, 'dist': 180},
    ])
    
    # 宁安城际线
    train_data.extend([
        {'code': 'D9501', 'type': '动车', 'start': 'NKH', 'end': 'AQH', 'dep': '07:30', 'arr': '10:00', 'dur': 150, 'dist': 280},
        {'code': 'D9503', 'type': '动车', 'start': 'NKH', 'end': 'AQH', 'dep': '09:30', 'arr': '12:00', 'dur': 150, 'dist': 280},
        {'code': 'D9505', 'type': '动车', 'start': 'NKH', 'end': 'AQH', 'dep': '14:00', 'arr': '16:30', 'dur': 150, 'dist': 280},
    ])
    
    # 盐通高铁线
    train_data.extend([
        {'code': 'G9505', 'type': '高铁', 'start': 'YCH', 'end': 'NTH', 'dep': '08:00', 'arr': '09:00', 'dur': 60, 'dist': 100},
        {'code': 'G9507', 'type': '高铁', 'start': 'YCH', 'end': 'NTH', 'dep': '10:00', 'arr': '11:00', 'dur': 60, 'dist': 100},
    ])
    
    # 连镇高铁线
    train_data.extend([
        {'code': 'G9509', 'type': '高铁', 'start': 'LGH', 'end': 'ZJN', 'dep': '08:00', 'arr': '10:30', 'dur': 150, 'dist': 200},
        {'code': 'G9511', 'type': '高铁', 'start': 'LGH', 'end': 'ZJN', 'dep': '11:00', 'arr': '13:30', 'dur': 150, 'dist': 200},
    ])
    
    # 更多京沪高铁车次
    train_data.extend([
        {'code': 'G107', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '06:30', 'arr': '11:30', 'dur': 300, 'dist': 1318},
        {'code': 'G109', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '07:30', 'arr': '12:30', 'dur': 300, 'dist': 1318},
        {'code': 'G111', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '08:30', 'arr': '13:30', 'dur': 300, 'dist': 1318},
        {'code': 'G113', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '09:30', 'arr': '14:30', 'dur': 300, 'dist': 1318},
        {'code': 'G115', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '10:30', 'arr': '15:30', 'dur': 300, 'dist': 1318},
        {'code': 'G117', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '11:30', 'arr': '16:30', 'dur': 300, 'dist': 1318},
        {'code': 'G119', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '12:30', 'arr': '17:30', 'dur': 300, 'dist': 1318},
    ])
    
    # 更多沪宁城际车次
    train_data.extend([
        {'code': 'G7011', 'type': '高铁', 'start': 'SHA', 'end': 'NJH', 'dep': '09:00', 'arr': '10:30', 'dur': 90, 'dist': 301},
        {'code': 'G7013', 'type': '高铁', 'start': 'SHA', 'end': 'NJH', 'dep': '10:00', 'arr': '11:30', 'dur': 90, 'dist': 301},
        {'code': 'G7015', 'type': '高铁', 'start': 'SHA', 'end': 'NJH', 'dep': '11:00', 'arr': '12:30', 'dur': 90, 'dist': 301},
        {'code': 'G7017', 'type': '高铁', 'start': 'SHA', 'end': 'NJH', 'dep': '12:00', 'arr': '13:30', 'dur': 90, 'dist': 301},
        {'code': 'G7019', 'type': '高铁', 'start': 'SHA', 'end': 'NJH', 'dep': '13:00', 'arr': '14:30', 'dur': 90, 'dist': 301},
        {'code': 'C3007', 'type': '城际', 'start': 'SHA', 'end': 'NJH', 'dep': '09:15', 'arr': '10:50', 'dur': 95, 'dist': 301},
        {'code': 'C3009', 'type': '城际', 'start': 'SHA', 'end': 'NJH', 'dep': '10:15', 'arr': '11:50', 'dur': 95, 'dist': 301},
    ])
    
    # 更多沪昆高铁车次
    train_data.extend([
        {'code': 'G1373', 'type': '高铁', 'start': 'SHH', 'end': 'KMG', 'dep': '09:00', 'arr': '21:00', 'dur': 720, 'dist': 2252},
        {'code': 'G1375', 'type': '高铁', 'start': 'SHH', 'end': 'KMG', 'dep': '11:00', 'arr': '23:00', 'dur': 720, 'dist': 2252},
        {'code': 'G1321', 'type': '高铁', 'start': 'SHH', 'end': 'CSQ', 'dep': '06:00', 'arr': '10:30', 'dur': 270, 'dist': 1150},
        {'code': 'G1323', 'type': '高铁', 'start': 'SHH', 'end': 'CSQ', 'dep': '07:00', 'arr': '11:30', 'dur': 270, 'dist': 1150},
        {'code': 'G1325', 'type': '高铁', 'start': 'SHH', 'end': 'CSQ', 'dep': '08:00', 'arr': '12:30', 'dur': 270, 'dist': 1150},
        {'code': 'G1327', 'type': '高铁', 'start': 'SHH', 'end': 'CSQ', 'dep': '10:00', 'arr': '14:30', 'dur': 270, 'dist': 1150},
        {'code': 'G1329', 'type': '高铁', 'start': 'SHH', 'end': 'CSQ', 'dep': '12:00', 'arr': '16:30', 'dur': 270, 'dist': 1150},
    ])
    
    # 更多宁杭高铁车次
    train_data.extend([
        {'code': 'G7613', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '11:00', 'arr': '12:30', 'dur': 90, 'dist': 256},
        {'code': 'G7615', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '12:00', 'arr': '13:30', 'dur': 90, 'dist': 256},
        {'code': 'G7617', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '13:00', 'arr': '14:30', 'dur': 90, 'dist': 256},
        {'code': 'G7619', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '14:00', 'arr': '15:30', 'dur': 90, 'dist': 256},
        {'code': 'G7621', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '15:00', 'arr': '16:30', 'dur': 90, 'dist': 256},
    ])
    
    # 更多杭深高铁车次
    train_data.extend([
        {'code': 'G7513', 'type': '高铁', 'start': 'HZN', 'end': 'SZN', 'dep': '11:00', 'arr': '16:00', 'dur': 300, 'dist': 1100},
        {'code': 'G7515', 'type': '高铁', 'start': 'HZN', 'end': 'SZN', 'dep': '12:00', 'arr': '17:00', 'dur': 300, 'dist': 1100},
        {'code': 'G7517', 'type': '高铁', 'start': 'HZN', 'end': 'SZN', 'dep': '13:00', 'arr': '18:00', 'dur': 300, 'dist': 1100},
        {'code': 'G7519', 'type': '高铁', 'start': 'HZN', 'end': 'SZN', 'dep': '14:00', 'arr': '19:00', 'dur': 300, 'dist': 1100},
        {'code': 'G7521', 'type': '高铁', 'start': 'HZN', 'end': 'SZN', 'dep': '15:00', 'arr': '20:00', 'dur': 300, 'dist': 1100},
    ])
    
    # 更多合福高铁车次
    train_data.extend([
        {'code': 'G1617', 'type': '高铁', 'start': 'HFN', 'end': 'FZS', 'dep': '07:00', 'arr': '11:30', 'dur': 270, 'dist': 780},
        {'code': 'G1619', 'type': '高铁', 'start': 'HFN', 'end': 'FZS', 'dep': '11:00', 'arr': '15:30', 'dur': 270, 'dist': 780},
        {'code': 'G1621', 'type': '高铁', 'start': 'HFN', 'end': 'FZS', 'dep': '13:00', 'arr': '17:30', 'dur': 270, 'dist': 780},
        {'code': 'G1623', 'type': '高铁', 'start': 'HFN', 'end': 'FZS', 'dep': '15:00', 'arr': '19:30', 'dur': 270, 'dist': 780},
    ])
    
    # 更多京沪普速车次
    train_data.extend([
        {'code': 'Z268', 'type': '普速', 'start': 'SHA', 'end': 'BJP', 'dep': '14:00', 'arr': '07:00', 'dur': 1020, 'dist': 1463},
        {'code': 'K47', 'type': '普速', 'start': 'SHA', 'end': 'BJP', 'dep': '15:00', 'arr': '12:00', 'dur': 1260, 'dist': 1463},
        {'code': 'K145', 'type': '普速', 'start': 'SHA', 'end': 'BJP', 'dep': '16:00', 'arr': '14:00', 'dur': 1320, 'dist': 1463},
    ])
    
    # 更多沪昆普速车次
    train_data.extend([
        {'code': 'K111', 'type': '普速', 'start': 'SNH', 'end': 'KMG', 'dep': '12:00', 'arr': '18:00', 'dur': 2160, 'dist': 2252},
        {'code': 'K495', 'type': '普速', 'start': 'SNH', 'end': 'KMG', 'dep': '14:00', 'arr': '20:00', 'dur': 2160, 'dist': 2252},
        {'code': 'K739', 'type': '普速', 'start': 'SNH', 'end': 'KMG', 'dep': '16:00', 'arr': '22:00', 'dur': 2160, 'dist': 2252},
    ])
    
    # 杭州-温州方向
    train_data.extend([
        {'code': 'G7623', 'type': '高铁', 'start': 'HZN', 'end': 'WZH', 'dep': '08:00', 'arr': '10:00', 'dur': 120, 'dist': 350},
        {'code': 'G7625', 'type': '高铁', 'start': 'HZN', 'end': 'WZH', 'dep': '10:00', 'arr': '12:00', 'dur': 120, 'dist': 350},
        {'code': 'G7627', 'type': '高铁', 'start': 'HZN', 'end': 'WZH', 'dep': '13:00', 'arr': '15:00', 'dur': 120, 'dist': 350},
        {'code': 'D3231', 'type': '动车', 'start': 'HZN', 'end': 'WZH', 'dep': '09:00', 'arr': '11:30', 'dur': 150, 'dist': 350},
        {'code': 'D3233', 'type': '动车', 'start': 'HZN', 'end': 'WZH', 'dep': '14:00', 'arr': '16:30', 'dur': 150, 'dist': 350},
    ])
    
    # 宁波-温州方向
    train_data.extend([
        {'code': 'G7651', 'type': '高铁', 'start': 'NBH', 'end': 'WZH', 'dep': '08:00', 'arr': '09:30', 'dur': 90, 'dist': 280},
        {'code': 'G7653', 'type': '高铁', 'start': 'NBH', 'end': 'WZH', 'dep': '10:00', 'arr': '11:30', 'dur': 90, 'dist': 280},
        {'code': 'G7655', 'type': '高铁', 'start': 'NBH', 'end': 'WZH', 'dep': '13:00', 'arr': '14:30', 'dur': 90, 'dist': 280},
    ])
    
    # 上海-杭州方向
    train_data.extend([
        {'code': 'G9301', 'type': '高铁', 'start': 'SHA', 'end': 'HZH', 'dep': '07:00', 'arr': '08:30', 'dur': 90, 'dist': 202},
        {'code': 'G9303', 'type': '高铁', 'start': 'SHA', 'end': 'HZH', 'dep': '08:00', 'arr': '09:30', 'dur': 90, 'dist': 202},
        {'code': 'G9305', 'type': '高铁', 'start': 'SHA', 'end': 'HZH', 'dep': '09:00', 'arr': '10:30', 'dur': 90, 'dist': 202},
        {'code': 'G9307', 'type': '高铁', 'start': 'SHA', 'end': 'HZH', 'dep': '10:00', 'arr': '11:30', 'dur': 90, 'dist': 202},
        {'code': 'G9309', 'type': '高铁', 'start': 'SHA', 'end': 'HZH', 'dep': '11:00', 'arr': '12:30', 'dur': 90, 'dist': 202},
        {'code': 'C5601', 'type': '城际', 'start': 'SHA', 'end': 'HZH', 'dep': '07:30', 'arr': '09:10', 'dur': 100, 'dist': 202},
        {'code': 'C5603', 'type': '城际', 'start': 'SHA', 'end': 'HZH', 'dep': '08:30', 'arr': '10:10', 'dur': 100, 'dist': 202},
        {'code': 'C5605', 'type': '城际', 'start': 'SHA', 'end': 'HZH', 'dep': '09:30', 'arr': '11:10', 'dur': 100, 'dist': 202},
    ])
    
    # 上海虹桥-杭州东
    train_data.extend([
        {'code': 'G9311', 'type': '高铁', 'start': 'SHH', 'end': 'HZN', 'dep': '07:30', 'arr': '08:50', 'dur': 80, 'dist': 202},
        {'code': 'G9313', 'type': '高铁', 'start': 'SHH', 'end': 'HZN', 'dep': '08:30', 'arr': '09:50', 'dur': 80, 'dist': 202},
        {'code': 'G9315', 'type': '高铁', 'start': 'SHH', 'end': 'HZN', 'dep': '09:30', 'arr': '10:50', 'dur': 80, 'dist': 202},
        {'code': 'G9317', 'type': '高铁', 'start': 'SHH', 'end': 'HZN', 'dep': '10:30', 'arr': '11:50', 'dur': 80, 'dist': 202},
        {'code': 'G9319', 'type': '高铁', 'start': 'SHH', 'end': 'HZN', 'dep': '11:30', 'arr': '12:50', 'dur': 80, 'dist': 202},
        {'code': 'G9321', 'type': '高铁', 'start': 'SHH', 'end': 'HZN', 'dep': '13:30', 'arr': '14:50', 'dur': 80, 'dist': 202},
        {'code': 'G9323', 'type': '高铁', 'start': 'SHH', 'end': 'HZN', 'dep': '14:30', 'arr': '15:50', 'dur': 80, 'dist': 202},
        {'code': 'G9325', 'type': '高铁', 'start': 'SHH', 'end': 'HZN', 'dep': '15:30', 'arr': '16:50', 'dur': 80, 'dist': 202},
    ])
    
    # 合肥-杭州方向
    train_data.extend([
        {'code': 'G7657', 'type': '高铁', 'start': 'HFN', 'end': 'HZN', 'dep': '08:00', 'arr': '11:00', 'dur': 180, 'dist': 450},
        {'code': 'G7659', 'type': '高铁', 'start': 'HFN', 'end': 'HZN', 'dep': '10:00', 'arr': '13:00', 'dur': 180, 'dist': 450},
        {'code': 'G7661', 'type': '高铁', 'start': 'HFN', 'end': 'HZN', 'dep': '13:00', 'arr': '16:00', 'dur': 180, 'dist': 450},
        {'code': 'G7663', 'type': '高铁', 'start': 'HFN', 'end': 'HZN', 'dep': '15:00', 'arr': '18:00', 'dur': 180, 'dist': 450},
    ])
    
    # 南京-杭州方向
    train_data.extend([
        {'code': 'G7665', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '08:00', 'arr': '10:30', 'dur': 150, 'dist': 350},
        {'code': 'G7667', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '10:00', 'arr': '12:30', 'dur': 150, 'dist': 350},
        {'code': 'G7669', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '12:00', 'arr': '14:30', 'dur': 150, 'dist': 350},
        {'code': 'G7671', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '14:00', 'arr': '16:30', 'dur': 150, 'dist': 350},
        {'code': 'G7673', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '16:00', 'arr': '18:30', 'dur': 150, 'dist': 350},
    ])
    
    # 上海-宁波方向
    train_data.extend([
        {'code': 'G7521', 'type': '高铁', 'start': 'SHA', 'end': 'NBH', 'dep': '08:00', 'arr': '10:00', 'dur': 120, 'dist': 320},
        {'code': 'G7523', 'type': '高铁', 'start': 'SHA', 'end': 'NBH', 'dep': '10:00', 'arr': '12:00', 'dur': 120, 'dist': 320},
        {'code': 'G7525', 'type': '高铁', 'start': 'SHA', 'end': 'NBH', 'dep': '13:00', 'arr': '15:00', 'dur': 120, 'dist': 320},
        {'code': 'G7527', 'type': '高铁', 'start': 'SHA', 'end': 'NBH', 'dep': '15:00', 'arr': '17:00', 'dur': 120, 'dist': 320},
        {'code': 'G7529', 'type': '高铁', 'start': 'SHA', 'end': 'NBH', 'dep': '17:00', 'arr': '19:00', 'dur': 120, 'dist': 320},
    ])
    
    # 上海-温州方向
    train_data.extend([
        {'code': 'G7531', 'type': '高铁', 'start': 'SHA', 'end': 'WZH', 'dep': '08:00', 'arr': '12:00', 'dur': 240, 'dist': 650},
        {'code': 'G7533', 'type': '高铁', 'start': 'SHA', 'end': 'WZH', 'dep': '10:00', 'arr': '14:00', 'dur': 240, 'dist': 650},
        {'code': 'G7535', 'type': '高铁', 'start': 'SHA', 'end': 'WZH', 'dep': '13:00', 'arr': '17:00', 'dur': 240, 'dist': 650},
    ])
    
    # 更多合肥相关车次
    train_data.extend([
        {'code': 'G7675', 'type': '高铁', 'start': 'HFN', 'end': 'SHA', 'dep': '08:00', 'arr': '11:00', 'dur': 180, 'dist': 450},
        {'code': 'G7677', 'type': '高铁', 'start': 'HFN', 'end': 'SHA', 'dep': '10:00', 'arr': '13:00', 'dur': 180, 'dist': 450},
        {'code': 'G7679', 'type': '高铁', 'start': 'HFN', 'end': 'SHA', 'dep': '13:00', 'arr': '16:00', 'dur': 180, 'dist': 450},
        {'code': 'G7681', 'type': '高铁', 'start': 'HFN', 'end': 'SHA', 'dep': '15:00', 'arr': '18:00', 'dur': 180, 'dist': 450},
    ])
    
    # 更多南京相关车次
    train_data.extend([
        {'code': 'G7101', 'type': '高铁', 'start': 'NJH', 'end': 'SHA', 'dep': '07:00', 'arr': '08:30', 'dur': 90, 'dist': 301},
        {'code': 'G7103', 'type': '高铁', 'start': 'NJH', 'end': 'SHA', 'dep': '08:00', 'arr': '09:30', 'dur': 90, 'dist': 301},
        {'code': 'G7105', 'type': '高铁', 'start': 'NJH', 'end': 'SHA', 'dep': '09:00', 'arr': '10:30', 'dur': 90, 'dist': 301},
        {'code': 'G7107', 'type': '高铁', 'start': 'NJH', 'end': 'SHA', 'dep': '10:00', 'arr': '11:30', 'dur': 90, 'dist': 301},
        {'code': 'G7109', 'type': '高铁', 'start': 'NJH', 'end': 'SHA', 'dep': '11:00', 'arr': '12:30', 'dur': 90, 'dist': 301},
        {'code': 'G7111', 'type': '高铁', 'start': 'NJH', 'end': 'SHA', 'dep': '12:00', 'arr': '13:30', 'dur': 90, 'dist': 301},
        {'code': 'G7113', 'type': '高铁', 'start': 'NJH', 'end': 'SHA', 'dep': '13:00', 'arr': '14:30', 'dur': 90, 'dist': 301},
        {'code': 'G7115', 'type': '高铁', 'start': 'NJH', 'end': 'SHA', 'dep': '14:00', 'arr': '15:30', 'dur': 90, 'dist': 301},
    ])
    
    # 徐州-南京方向
    train_data.extend([
        {'code': 'G7121', 'type': '高铁', 'start': 'XZH', 'end': 'NJH', 'dep': '08:00', 'arr': '10:00', 'dur': 120, 'dist': 330},
        {'code': 'G7123', 'type': '高铁', 'start': 'XZH', 'end': 'NJH', 'dep': '10:00', 'arr': '12:00', 'dur': 120, 'dist': 330},
        {'code': 'G7125', 'type': '高铁', 'start': 'XZH', 'end': 'NJH', 'dep': '13:00', 'arr': '15:00', 'dur': 120, 'dist': 330},
        {'code': 'G7127', 'type': '高铁', 'start': 'XZH', 'end': 'NJH', 'dep': '15:00', 'arr': '17:00', 'dur': 120, 'dist': 330},
    ])
    
    # 徐州东相关车次
    train_data.extend([
        {'code': 'G7131', 'type': '高铁', 'start': 'XZN', 'end': 'SHA', 'dep': '08:00', 'arr': '11:30', 'dur': 210, 'dist': 650},
        {'code': 'G7133', 'type': '高铁', 'start': 'XZN', 'end': 'SHA', 'dep': '10:00', 'arr': '13:30', 'dur': 210, 'dist': 650},
        {'code': 'G7135', 'type': '高铁', 'start': 'XZN', 'end': 'SHA', 'dep': '13:00', 'arr': '16:30', 'dur': 210, 'dist': 650},
        {'code': 'G7137', 'type': '高铁', 'start': 'XZN', 'end': 'SHA', 'dep': '15:00', 'arr': '18:30', 'dur': 210, 'dist': 650},
        {'code': 'G7141', 'type': '高铁', 'start': 'SHA', 'end': 'XZN', 'dep': '08:00', 'arr': '11:00', 'dur': 180, 'dist': 650},
        {'code': 'G7143', 'type': '高铁', 'start': 'SHA', 'end': 'XZN', 'dep': '10:00', 'arr': '13:00', 'dur': 180, 'dist': 650},
        {'code': 'G7145', 'type': '高铁', 'start': 'SHA', 'end': 'XZN', 'dep': '13:00', 'arr': '16:00', 'dur': 180, 'dist': 650},
        {'code': 'G7147', 'type': '高铁', 'start': 'SHA', 'end': 'XZN', 'dep': '15:00', 'arr': '18:00', 'dur': 180, 'dist': 650},
    ])
    
    # 创建车次和停站
    station_map = {s.station_code: s.id for s in Station.query.all()}
    
    trains_created = []
    for td in train_data:
        start_id = station_map.get(td['start'])
        end_id = station_map.get(td['end'])
        
        if not start_id or not end_id:
            continue
        
        train = Train(
            train_code=td['code'],
            train_type=td['type'],
            start_station_id=start_id,
            end_station_id=end_id,
            departure_time=td['dep'],
            arrival_time=td['arr'],
            duration=td['dur'],
            total_distance=td['dist'],
            is_active=1
        )
        db.session.add(train)
        trains_created.append(train)
    
    db.session.commit()
    
    # 为车次创建停站和席别
    for train in trains_created:
        base_price = train.total_distance * 0.45  # 基础票价率
        
        # 创建席别
        if train.train_type in ['高铁', '动车', '城际']:
            seat_configs = [
                ('BS', 3.0, 10, 8),
                ('YS', 1.8, 50, 45),
                ('ES', 1.0, 500, 480),
            ]
        else:
            seat_configs = [
                ('RW', 1.5, 80, 75),
                ('YW', 1.0, 200, 190),
                ('YZ', 0.5, 500, 480),
            ]
        
        for code, rate, total, available in seat_configs:
            seat_type = SeatType.query.filter_by(code=code).first()
            if seat_type:
                train_seat = TrainSeat(
                    train_id=train.id,
                    seat_type_id=seat_type.id,
                    total_count=total,
                    available_count=available,
                    price=round(base_price * rate, 2)
                )
                db.session.add(train_seat)
        
        # 创建停站信息（简化：只有起始站和终到站）
        stop1 = TrainStop(
            train_id=train.id,
            station_id=train.start_station_id,
            stop_order=1,
            arrival_time=None,
            departure_time=train.departure_time,
            stop_duration=0,
            distance_from_start=0
        )
        stop2 = TrainStop(
            train_id=train.id,
            station_id=train.end_station_id,
            stop_order=2,
            arrival_time=train.arrival_time,
            departure_time=None,
            stop_duration=0,
            distance_from_start=train.total_distance
        )
        db.session.add_all([stop1, stop2])
    
    db.session.commit()
    
    # 创建公告
    announcements = [
        Announcement(
            title='关于2024年春运期间增开列车的公告',
            content='为满足2024年春运期间旅客出行需求，我局将在春节期间增开多趟临时旅客列车，具体车次及开行时间请关注车站公告。',
            type='announcement',
            created_by=admin.id
        ),
        Announcement(
            title='系统维护通知',
            content='系统将于本周日凌晨2:00-6:00进行例行维护，届时可能影响部分功能的正常使用，给您带来不便敬请谅解。',
            type='notice',
            created_by=admin.id
        ),
        Announcement(
            title='关于调整预售期的公告',
            content='即日起，互联网售票预售期调整为15天（含当日），请广大旅客提前做好出行安排。',
            type='notice',
            created_by=admin.id
        ),
    ]
    db.session.add_all(announcements)
    db.session.commit()
    
    print(f"创建了 {len(SeatType.query.all())} 种席别")
    print(f"创建了 {len(stations)} 个站点")
    print(f"创建了 {len(trains_created)} 趟车次")
    print(f"创建了 {len(Announcement.query.all())} 条公告")
