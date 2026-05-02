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
    
    # 创建站点数据 - 上海局管辖上海、江苏、浙江、安徽四省市
    # 修复重复代码：HNZ(淮南/海宁)->淮南HNS,海宁HNZ2; CHZ(春申/池州)->春申CSH,池州CHZ2
    # DYH(丹阳/定远)->丹阳保留DYH,定远DYG; TZH(泰州/台州)->泰州TZC,台州TZU
    stations_data = [
        # ========== 上海市（19个）==========
        ('SHA', '上海', 'Shanghai', '上海', '上海', '特等', 1),
        ('SHH', '上海虹桥', 'ShanghaiHongqiao', '上海', '上海', '特等', 1),
        ('SNH', '上海南', 'ShanghaiNan', '上海', '上海', '一等', 1),
        ('SHX', '上海西', 'ShanghaiXi', '上海', '上海', '一等', 1),
        ('SJN', '松江南', 'Songjiangnan', '上海', '上海', '二等', 1),
        ('SAJ', '松江', 'Songjiang', '上海', '上海', '二等', 1),
        ('NBE', '南翔北', 'Nanxiangbei', '上海', '上海', '二等', 0),
        ('ATB', '安亭北', 'Antingbei', '上海', '上海', '二等', 1),
        ('HQB', '花桥', 'Huaqiao', '苏州', '上海', '二等', 1),
        ('JTB', '金山北', 'Jinshanbei', '上海', '上海', '二等', 1),
        ('LCG', '芦潮港', 'LuchaoGang', '上海', '上海', '三等', 0),
        ('XQH', '新桥', 'Xinqiao', '上海', '上海', '三等', 0),
        ('CSH', '春申', 'Chunshen', '上海', '上海', '三等', 0),
        ('QIB', '七宝', 'Qibao', '上海', '上海', '三等', 0),
        ('MIN', '闵行', 'Minhang', '上海', '上海', '三等', 0),
        ('XZB', '莘庄', 'Xinzhuang', '上海', '上海', '三等', 0),
        ('LTH', '练塘', 'Liantang', '上海', '上海', '三等', 0),
        ('JSW', '金山卫', 'Jinshanwei', '上海', '上海', '二等', 1),
        ('SHU', '上海东', 'ShanghaiDong', '上海', '上海', '特等', 1),
        
        # ========== 江苏省 - 南京（8个）==========
        ('NJH', '南京', 'Nanjing', '南京', '江苏', '特等', 1),
        ('NKH', '南京南', 'Nanjingnan', '南京', '江苏', '特等', 1),
        ('NJX', '南京西', 'Nanjingxi', '南京', '江苏', '一等', 0),
        ('XLI', '仙林', 'Xianlin', '南京', '江苏', '二等', 1),
        ('JNC', '江宁', 'Jiangning', '南京', '江苏', '二等', 1),
        ('LHZ', '六合', 'Liuhe', '南京', '江苏', '二等', 1),
        ('NJG', '南京北', 'Nanjingbei', '南京', '江苏', '三等', 0),
        ('CJQ', '长芦', 'Changlu', '南京', '江苏', '三等', 0),
        
        # ========== 江苏省 - 苏州（10个）==========
        ('SZH', '苏州', 'Suzhou', '苏州', '江苏', '一等', 1),
        ('SBN', '苏州北', 'Suzhoubei', '苏州', '江苏', '一等', 1),
        ('SZQ', '苏州园区', 'Suzhouyuanqu', '苏州', '江苏', '二等', 1),
        ('SXX', '苏州新区', 'Suzhouxinqu', '苏州', '江苏', '二等', 1),
        ('KSH', '昆山', 'Kunshan', '苏州', '江苏', '二等', 0),
        ('KSN', '昆山南', 'Kunshannan', '苏州', '江苏', '一等', 1),
        ('YCY', '阳澄湖', 'Yangchenghu', '苏州', '江苏', '三等', 1),
        ('TCZ', '太仓', 'Taicang', '苏州', '江苏', '二等', 1),
        ('CSZ', '常熟', 'Changshu', '苏州', '江苏', '二等', 1),
        ('ZJG', '张家港', 'Zhangjiagang', '苏州', '江苏', '二等', 1),
        
        # ========== 江苏省 - 无锡（5个）==========
        ('WXH', '无锡', 'Wuxi', '无锡', '江苏', '一等', 1),
        ('WXD', '无锡东', 'Wuxidong', '无锡', '江苏', '一等', 1),
        ('WXX', '无锡新区', 'Wuxixinqu', '无锡', '江苏', '二等', 1),
        ('HSH', '惠山', 'Huishan', '无锡', '江苏', '二等', 1),
        ('YXH', '宜兴', 'Yixing', '无锡', '江苏', '二等', 1),
        
        # ========== 江苏省 - 常州（4个）==========
        ('CZH', '常州', 'Changzhou', '常州', '江苏', '一等', 1),
        ('CZN', '常州北', 'Changzhoubei', '常州', '江苏', '二等', 1),
        ('QSY', '戚墅堰', 'Qishuyan', '常州', '江苏', '三等', 0),
        ('WJN', '武进', 'Wujin', '常州', '江苏', '二等', 1),
        
        # ========== 江苏省 - 镇江（6个）==========
        ('ZJH', '镇江', 'Zhenjiang', '镇江', '江苏', '一等', 1),
        ('ZJN', '镇江南', 'Zhenjiangnan', '镇江', '江苏', '二等', 1),
        ('DYH', '丹阳', 'Danyang', '镇江', '江苏', '二等', 1),
        ('DYB', '丹阳北', 'Danyangbei', '镇江', '江苏', '二等', 1),
        ('BHS', '宝华山', 'Baohuashan', '镇江', '江苏', '三等', 0),
        ('JRH', '句容', 'Jurong', '镇江', '江苏', '二等', 1),
        
        # ========== 江苏省 - 徐州（5个）==========
        ('XZH', '徐州', 'Xuzhou', '徐州', '江苏', '特等', 1),
        ('XZN', '徐州东', 'Xuzhoudong', '徐州', '江苏', '特等', 1),
        ('PZH', '邳州', 'Pizhou', '徐州', '江苏', '二等', 0),
        ('XYH', '新沂', 'Xinyi', '徐州', '江苏', '二等', 0),
        ('SUN', '睢宁', 'Suining', '徐州', '江苏', '二等', 1),
        
        # ========== 江苏省 - 连云港（4个）==========
        ('LGH', '连云港', 'Lianyungang', '连云港', '江苏', '一等', 1),
        ('LGD', '连云港东', 'Lianyungangdong', '连云港', '江苏', '二等', 0),
        ('DHX', '东海县', 'Donghaixian', '连云港', '江苏', '三等', 0),
        ('GYN', '灌云', 'Guanyun', '连云港', '江苏', '三等', 1),
        
        # ========== 江苏省 - 淮安（4个）==========
        ('HAB', '淮安', 'Huaian', '淮安', '江苏', '二等', 1),
        ('HAD', '淮安东', 'Huaiandong', '淮安', '江苏', '一等', 1),
        ('HAN', '淮安南', 'Huaiannan', '淮安', '江苏', '三等', 0),
        ('LIS', '涟水', 'Lianshui', '淮安', '江苏', '二等', 1),
        
        # ========== 江苏省 - 盐城（7个）==========
        ('YCH', '盐城', 'Yancheng', '盐城', '江苏', '二等', 1),
        ('DFZ', '盐城大丰', 'YanchengDafeng', '盐城', '江苏', '二等', 1),
        ('DTZ', '东台', 'Dongtai', '盐城', '江苏', '三等', 0),
        ('JHZ', '建湖', 'Jianhu', '盐城', '江苏', '三等', 0),
        ('FNZ', '阜宁', 'Funing', '盐城', '江苏', '三等', 0),
        ('BJX', '滨海', 'Binhai', '盐城', '江苏', '三等', 1),
        ('XSS', '响水', 'Xiangshui', '盐城', '江苏', '三等', 1),
        
        # ========== 江苏省 - 南通（7个）==========
        ('NTH', '南通', 'Nantong', '南通', '江苏', '一等', 1),
        ('NTX', '南通西', 'Nantongxi', '南通', '江苏', '二等', 1),
        ('RGC', '如皋', 'Rugao', '南通', '江苏', '三等', 0),
        ('HAX', '海安', 'Haian', '南通', '江苏', '二等', 1),
        ('RDZ', '如东', 'Rudong', '南通', '江苏', '三等', 1),
        ('QDZ', '启东', 'Qidong', '南通', '江苏', '三等', 1),
        ('HMN', '海门', 'Haimen', '南通', '江苏', '二等', 1),
        
        # ========== 江苏省 - 扬州（5个）==========
        ('YZH', '扬州', 'Yangzhou', '扬州', '江苏', '二等', 1),
        ('YZD', '扬州东', 'Yangzhoudong', '扬州', '江苏', '一等', 1),
        ('JDH', '江都', 'Jiangdu', '扬州', '江苏', '三等', 0),
        ('YZG', '仪征', 'Yizheng', '扬州', '江苏', '三等', 0),
        ('GYH', '高邮', 'Gaoyou', '扬州', '江苏', '三等', 1),
        
        # ========== 江苏省 - 泰州（3个）==========
        ('TZC', '泰州', 'Taizhou', '泰州', '江苏', '二等', 1),
        ('JYZ', '姜堰', 'Jiangyan', '泰州', '江苏', '三等', 0),
        ('TXZ', '泰兴', 'Taixing', '泰州', '江苏', '三等', 1),
        
        # ========== 江苏省 - 宿迁（3个）==========
        ('SUQ', '宿迁', 'Suqian', '宿迁', '江苏', '二等', 1),
        ('SYZ', '沭阳', 'Shuyang', '宿迁', '江苏', '三等', 0),
        ('SIY', '泗阳', 'Siyang', '宿迁', '江苏', '三等', 1),
        
        # ========== 江苏省 - 扬州泰州共用/其他（1个）==========
        ('BGY', '宝应', 'Baoying', '扬州', '江苏', '三等', 1),
        
        # ========== 浙江省 - 杭州（9个）==========
        ('HZH', '杭州', 'Hangzhou', '杭州', '浙江', '特等', 1),
        ('HZN', '杭州东', 'Hangzhoudong', '杭州', '浙江', '特等', 1),
        ('HXB', '杭州南', 'Hangzhounan', '杭州', '浙江', '一等', 1),
        ('HZX', '杭州西', 'Hangzhouxi', '杭州', '浙江', '一等', 1),
        ('YHH', '余杭', 'Yuhang', '杭州', '浙江', '二等', 1),
        ('LPN', '临平南', 'Linpingnan', '杭州', '浙江', '二等', 1),
        ('FYH', '富阳', 'Fuyang', '杭州', '浙江', '二等', 1),
        ('TLZ', '桐庐', 'Tonglu', '杭州', '浙江', '二等', 1),
        ('JDX', '建德', 'Jiande', '杭州', '浙江', '二等', 1),
        
        # ========== 浙江省 - 宁波（6个）==========
        ('NBH', '宁波', 'Ningbo', '宁波', '浙江', '一等', 1),
        ('NBD', '宁波东', 'Ningbodong', '宁波', '浙江', '二等', 0),
        ('YYZ', '余姚', 'Yuyao', '宁波', '浙江', '二等', 1),
        ('CXX', '慈溪', 'Cixi', '宁波', '浙江', '二等', 1),
        ('NHZ', '宁海', 'Ninghai', '宁波', '浙江', '二等', 1),
        ('FHZ', '奉化', 'Fenghua', '宁波', '浙江', '二等', 1),
        
        # ========== 浙江省 - 温州（8个）==========
        ('WZH', '温州', 'Wenzhou', '温州', '浙江', '一等', 1),
        ('WWN', '温州南', 'Wenzhounan', '温州', '浙江', '一等', 1),
        ('YQZ', '乐清', 'Yueqing', '温州', '浙江', '二等', 1),
        ('YJZ', '永嘉', 'Yongjia', '温州', '浙江', '二等', 1),
        ('YDS', '雁荡山', 'Yandangshan', '温州', '浙江', '三等', 1),
        ('CNZ', '苍南', 'Cangnan', '温州', '浙江', '三等', 1),
        ('RAZ', '瑞安', 'Rui\'an', '温州', '浙江', '二等', 1),
        ('PYZ', '平阳', 'Pingyang', '温州', '浙江', '二等', 1),
        
        # ========== 浙江省 - 绍兴（4个）==========
        ('SZX', '绍兴', 'Shaoxing', '绍兴', '浙江', '二等', 1),
        ('SYZ', '上虞', 'Shangyu', '绍兴', '浙江', '三等', 0),
        ('ZJZ', '诸暨', 'Zhuji', '绍兴', '浙江', '二等', 0),
        ('SHZ', '嵊州', 'Shengzhou', '绍兴', '浙江', '二等', 1),
        
        # ========== 浙江省 - 金华（8个）==========
        ('JHW', '金华', 'Jinhua', '金华', '浙江', '一等', 1),
        ('JHN', '金华南', 'Jinhuanan', '金华', '浙江', '二等', 1),
        ('YWH', '义乌', 'Yiwu', '金华', '浙江', '一等', 1),
        ('DNZ', '东阳', 'Dongyang', '金华', '浙江', '二等', 1),
        ('LXX', '兰溪', 'Lanxi', '金华', '浙江', '三等', 0),
        ('YKZ', '永康', 'Yongkang', '金华', '浙江', '二等', 1),
        ('WYZ', '武义', 'Wuyi', '金华', '浙江', '三等', 0),
        
        # ========== 浙江省 - 衢州（5个）==========
        ('QZH', '衢州', 'Quzhou', '衢州', '浙江', '二等', 1),
        ('LYZ', '龙游', 'Longyou', '衢州', '浙江', '三等', 0),
        ('JSA', '江山', 'Jiangshan', '衢州', '浙江', '二等', 1),
        ('CSX', '常山', 'Changshan', '衢州', '浙江', '三等', 1),
        ('KHZ', '开化', 'Kaihua', '衢州', '浙江', '三等', 1),
        
        # ========== 浙江省 - 嘉兴（8个）==========
        ('JXZ', '嘉兴', 'Jiaxing', '嘉兴', '浙江', '二等', 1),
        ('JXN', '嘉兴南', 'Jiaxingnan', '嘉兴', '浙江', '二等', 1),
        ('JSZ', '嘉善', 'Jiashan', '嘉兴', '浙江', '三等', 0),
        ('JSB', '嘉善南', 'Jiashannan', '嘉兴', '浙江', '二等', 1),
        ('HNZ', '海宁', 'Haining', '嘉兴', '浙江', '二等', 0),
        ('HNX', '海宁西', 'Hainingxi', '嘉兴', '浙江', '二等', 1),
        ('TXZ', '桐乡', 'Tongxiang', '嘉兴', '浙江', '二等', 1),
        ('PHZ', '平湖', 'Pinghu', '嘉兴', '浙江', '二等', 1),
        ('HYZ', '海盐', 'Haiyan', '嘉兴', '浙江', '二等', 1),
        
        # ========== 浙江省 - 湖州（6个）==========
        ('HZU', '湖州', 'Huzhou', '湖州', '浙江', '二等', 1),
        ('DQZ', '德清', 'Deqing', '湖州', '浙江', '二等', 1),
        ('CXZ', '长兴', 'Changxing', '湖州', '浙江', '三等', 0),
        ('AJZ', '安吉', 'Anji', '湖州', '浙江', '三等', 1),
        ('NXZ', '南浔', 'Nanxun', '湖州', '浙江', '三等', 1),
        
        # ========== 浙江省 - 台州（5个）==========
        ('TZU', '台州', 'Taizhou', '台州', '浙江', '二等', 1),
        ('WLZ', '温岭', 'Wenling', '台州', '浙江', '二等', 1),
        ('LHZ', '临海', 'Linhai', '台州', '浙江', '二等', 1),
        ('YUZ', '玉环', 'Yuhuan', '台州', '浙江', '三等', 1),
        ('SMZ', '三门', 'Sanmen', '台州', '浙江', '二等', 1),
        
        # ========== 浙江省 - 丽水（4个）==========
        ('LSH', '丽水', 'Lishui', '丽水', '浙江', '二等', 1),
        ('QTZ', '青田', 'Qingtian', '丽水', '浙江', '三等', 0),
        ('JYZ', '缙云', 'Jinyun', '丽水', '浙江', '三等', 1),
        ('LQZ', '龙泉', 'Longquan', '丽水', '浙江', '三等', 1),
        
        # ========== 安徽省 - 合肥（8个）==========
        ('HFH', '合肥', 'Hefei', '合肥', '安徽', '特等', 1),
        ('HFN', '合肥南', 'Hefeinan', '合肥', '安徽', '特等', 1),
        ('HFX', '合肥西', 'HefeiXi', '合肥', '安徽', '二等', 1),
        ('HBC', '合肥北城', 'Hefeibeicheng', '合肥', '安徽', '二等', 1),
        ('CFZ', '长丰', 'Changfeng', '合肥', '安徽', '三等', 0),
        ('CHH', '巢湖', 'Chaohu', '合肥', '安徽', '三等', 0),
        ('LJZ', '庐江', 'Lujiang', '合肥', '安徽', '三等', 1),
        ('SCZ', '舒城', 'Shucheng', '合肥', '安徽', '三等', 0),
        
        # ========== 安徽省 - 蚌埠（3个）==========
        ('BBH', '蚌埠', 'Bengbu', '蚌埠', '安徽', '一等', 1),
        ('BBN', '蚌埠南', 'Bengbunan', '蚌埠', '安徽', '一等', 1),
        ('GUZ', '固镇', 'Guzhen', '蚌埠', '安徽', '三等', 0),
        
        # ========== 安徽省 - 阜阳（5个）==========
        ('FYH', '阜阳', 'Fuyang', '阜阳', '安徽', '一等', 0),
        ('FYN', '阜阳北', 'Fuyangbei', '阜阳', '安徽', '一等', 0),
        ('THZ', '太和', 'Taihe', '阜阳', '安徽', '三等', 0),
        ('JSZ', '界首', 'Jieshou', '阜阳', '安徽', '三等', 1),
        ('LQZ', '临泉', 'Linquan', '阜阳', '安徽', '三等', 1),
        
        # ========== 安徽省 - 亳州（4个）==========
        ('BZZ', '亳州', 'Bozhou', '亳州', '安徽', '二等', 0),
        ('WYZ', '涡阳', 'Woyang', '亳州', '安徽', '三等', 0),
        ('MCZ', '蒙城', 'Mengcheng', '亳州', '安徽', '三等', 1),
        ('LXZ', '利辛', 'Lixin', '亳州', '安徽', '三等', 1),
        
        # ========== 安徽省 - 淮北（2个）==========
        ('HBE', '淮北', 'Huaibei', '淮北', '安徽', '二等', 0),
        ('SXI', '濉溪', 'Suixi', '淮北', '安徽', '三等', 1),
        
        # ========== 安徽省 - 淮南（3个）==========
        ('HNS', '淮南', 'Huainan', '淮南', '安徽', '二等', 0),
        ('SHX', '寿县', 'Shouxian', '淮南', '安徽', '三等', 1),
        ('FTZ', '凤台', 'Fengtai', '淮南', '安徽', '三等', 1),
        
        # ========== 安徽省 - 芜湖（4个）==========
        ('WHH', '芜湖', 'Wuhu', '芜湖', '安徽', '一等', 1),
        ('WHD', '芜湖东', 'Wuhudong', '芜湖', '安徽', '二等', 1),
        ('FCZ', '繁昌', 'Fanchang', '芜湖', '安徽', '三等', 0),
        ('WWE', '无为', 'Wuwei', '芜湖', '安徽', '三等', 1),
        
        # ========== 安徽省 - 马鞍山（3个）==========
        ('MAZ', '马鞍山', 'Maanshan', '马鞍山', '安徽', '二等', 1),
        ('DTZ', '当涂', 'Dangtu', '马鞍山', '安徽', '三等', 0),
        ('HSZ', '含山', 'Hanshan', '马鞍山', '安徽', '三等', 1),
        
        # ========== 安徽省 - 铜陵（3个）==========
        ('TLZ', '铜陵', 'Tongling', '铜陵', '安徽', '二等', 1),
        ('TLB', '铜陵北', 'Tonglingbei', '铜陵', '安徽', '二等', 1),
        ('CZY', '枞阳', 'Zongyang', '铜陵', '安徽', '三等', 1),
        
        # ========== 安徽省 - 安庆（9个）==========
        ('AQH', '安庆', 'Anqing', '安庆', '安徽', '二等', 1),
        ('AQX', '安庆西', 'Anqingxi', '安庆', '安徽', '三等', 0),
        ('TCZ', '桐城', 'Tongcheng', '安庆', '安徽', '三等', 0),
        ('HNZ', '怀宁', 'Huaining', '安庆', '安徽', '三等', 0),
        ('QSZ', '潜山', 'Qianshan', '安庆', '安徽', '三等', 1),
        ('THZ', '太湖', 'Taihu', '安庆', '安徽', '三等', 0),
        ('SSZ', '宿松', 'Susong', '安庆', '安徽', '三等', 0),
        ('WJZ', '望江', 'Wangjiang', '安庆', '安徽', '三等', 1),
        ('TZS', '天柱山', 'Tianzhushan', '安庆', '安徽', '三等', 0),
        ('YXZ', '岳西', 'Yuexi', '安庆', '安徽', '三等', 1),
        
        # ========== 安徽省 - 黄山（6个）==========
        ('HSZ', '黄山', 'Huangshan', '黄山', '安徽', '二等', 1),
        ('HBN', '黄山北', 'Huangshannan', '黄山', '安徽', '二等', 1),
        ('SXX', '歙县', 'Shexian', '黄山', '安徽', '三等', 0),
        ('QMN', '祁门', 'Qimen', '黄山', '安徽', '三等', 1),
        ('YXX', '黟县', 'Yixian', '黄山', '安徽', '三等', 1),
        ('JXX', '绩溪县', 'Jixixian', '黄山', '安徽', '三等', 0),
        
        # ========== 安徽省 - 宣城（5个）==========
        ('XCZ', '宣城', 'Xuancheng', '宣城', '安徽', '二等', 0),
        ('NGZ', '宁国', 'Ningguo', '宣城', '安徽', '三等', 0),
        ('GDZ', '广德', 'Guangde', '宣城', '安徽', '三等', 1),
        ('LXZ', '郎溪', 'Langxi', '宣城', '安徽', '三等', 1),
        ('JXZ', '泾县', 'Jingxian', '宣城', '安徽', '三等', 1),
        
        # ========== 安徽省 - 滁州（6个）==========
        ('CHZ', '滁州', 'Chuzhou', '滁州', '安徽', '二等', 1),
        ('CHB', '滁州北', 'Chuzhoubei', '滁州', '安徽', '三等', 0),
        ('QJZ', '全椒', 'Quanjiao', '滁州', '安徽', '三等', 1),
        ('DYG', '定远', 'Dingyuan', '滁州', '安徽', '三等', 1),
        ('MGZ', '明光', 'Mingguang', '滁州', '安徽', '三等', 0),
        ('TCZ', '天长', 'Tianchang', '滁州', '安徽', '三等', 1),
        
        # ========== 安徽省 - 六安（4个）==========
        ('LAZ', '六安', 'LiuAn', '六安', '安徽', '二等', 1),
        ('JPZ', '金寨', 'Jinzhai', '六安', '安徽', '三等', 1),
        ('HSZ', '霍山', 'Huoshan', '六安', '安徽', '三等', 1),
        ('SCZ', '舒城', 'Shucheng', '六安', '安徽', '三等', 0),
        
        # ========== 安徽省 - 池州（1个）==========
        ('CHZ', '池州', 'Chizhou', '池州', '安徽', '二等', 0),
        
        # ========== 外局站点（15个）==========
        ('BJP', '北京南', 'BeijingNan', '北京', '北京', '特等', 1),
        ('TJP', '天津南', 'TianjinNan', '天津', '天津', '特等', 1),
        ('SJP', '石家庄', 'Shijiazhuang', '石家庄', '河北', '特等', 1),
        ('TYN', '太原南', 'TaiyuanNan', '太原', '山西', '特等', 1),
        ('ZZD', '郑州东', 'Zhengzhoudong', '郑州', '河南', '特等', 1),
        ('WHN', '武汉', 'Wuhan', '武汉', '湖北', '特等', 1),
        ('CWQ', '重庆西', 'ChongqingXi', '重庆', '重庆', '特等', 1),
        ('CSQ', '长沙南', 'ChangshaNan', '长沙', '湖南', '特等', 1),
        ('FZS', '福州南', 'FuzhouNan', '福州', '福建', '一等', 1),
        ('SZN', '深圳北', 'ShenzhenBei', '深圳', '广东', '特等', 1),
        ('KMG', '昆明南', 'KunmingNan', '昆明', '云南', '特等', 1),
        ('XAF', '西安北', 'XianBei', '西安', '陕西', '特等', 1),
        ('WHD', '武汉东', 'Wuhandong', '武汉', '湖北', '一等', 1),
        ('CZQ', '常州北', 'Changzhou', '常州', '江苏', '二等', 1),
        ('SZD', '苏州东', 'Suzhoudong', '苏州', '江苏', '二等', 1),
    ]
    
    # 去除重复的站点代码（保留第一个）
    seen_codes = set()
    unique_stations = []
    for s in stations_data:
        if s[0] not in seen_codes:
            seen_codes.add(s[0])
            unique_stations.append(s)
    
    stations = []
    for data in unique_stations:
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
    
    # ========== 1. 京沪高铁：上海虹桥-北京南（经南京南、徐州东等）==========
    train_data.extend([
        {'code': 'G1', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '07:00', 'arr': '11:30', 'dur': 270, 'dist': 1318, 'stops': ['SHH', 'NKH', 'XZN', 'TJP', 'BJP']},
        {'code': 'G3', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '09:00', 'arr': '13:28', 'dur': 268, 'dist': 1318, 'stops': ['SHH', 'NJH', 'XZN', 'BJP']},
        {'code': 'G5', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '11:00', 'arr': '15:28', 'dur': 268, 'dist': 1318, 'stops': ['SHH', 'NKH', 'XZN', 'BJP']},
        {'code': 'G7', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '13:00', 'arr': '17:28', 'dur': 268, 'dist': 1318, 'stops': ['SHH', 'NJH', 'XZN', 'BJP']},
        {'code': 'G9', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '15:00', 'arr': '19:28', 'dur': 268, 'dist': 1318, 'stops': ['SHH', 'NKH', 'XZN', 'BJP']},
        {'code': 'G101', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '08:00', 'arr': '13:05', 'dur': 305, 'dist': 1318, 'stops': ['SHH', 'NJH', 'XZN', 'BJP']},
        {'code': 'G103', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '10:00', 'arr': '15:05', 'dur': 305, 'dist': 1318, 'stops': ['SHH', 'NJH', 'XZN', 'BJP']},
        {'code': 'G105', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '14:00', 'arr': '19:05', 'dur': 305, 'dist': 1318, 'stops': ['SHH', 'NJH', 'XZN', 'BJP']},
        {'code': 'G107', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '06:30', 'arr': '11:30', 'dur': 300, 'dist': 1318, 'stops': ['SHH', 'NKH', 'XZN', 'TJP', 'BJP']},
        {'code': 'G109', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '07:30', 'arr': '12:30', 'dur': 300, 'dist': 1318, 'stops': ['SHH', 'NKH', 'XZN', 'TJP', 'BJP']},
        {'code': 'G111', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '08:30', 'arr': '13:30', 'dur': 300, 'dist': 1318, 'stops': ['SHH', 'NKH', 'XZN', 'BJP']},
        {'code': 'G113', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '09:30', 'arr': '14:30', 'dur': 300, 'dist': 1318, 'stops': ['SHH', 'NKH', 'XZN', 'BJP']},
        {'code': 'G115', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '10:30', 'arr': '15:30', 'dur': 300, 'dist': 1318, 'stops': ['SHH', 'NKH', 'XZN', 'BJP']},
        {'code': 'G117', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '11:30', 'arr': '16:30', 'dur': 300, 'dist': 1318, 'stops': ['SHH', 'NKH', 'XZN', 'BJP']},
        {'code': 'G119', 'type': '高铁', 'start': 'SHH', 'end': 'BJP', 'dep': '12:30', 'arr': '17:30', 'dur': 300, 'dist': 1318, 'stops': ['SHH', 'NKH', 'XZN', 'BJP']},
    ])
    
    # ========== 2. 沪宁城际：上海-南京==========
    train_data.extend([
        {'code': 'G7001', 'type': '高铁', 'start': 'SHA', 'end': 'NJH', 'dep': '06:00', 'arr': '07:30', 'dur': 90, 'dist': 301, 'stops': ['SHA', 'SZH', 'WXH', 'CZH', 'ZJH', 'NJH']},
        {'code': 'G7003', 'type': '高铁', 'start': 'SHA', 'end': 'NJH', 'dep': '06:30', 'arr': '08:00', 'dur': 90, 'dist': 301, 'stops': ['SHA', 'SZH', 'WXH', 'CZH', 'ZJH', 'NJH']},
        {'code': 'G7005', 'type': '高铁', 'start': 'SHA', 'end': 'NJH', 'dep': '07:00', 'arr': '08:30', 'dur': 90, 'dist': 301, 'stops': ['SHA', 'SZH', 'WXH', 'CZH', 'ZJH', 'NJH']},
        {'code': 'G7007', 'type': '高铁', 'start': 'SHA', 'end': 'NJH', 'dep': '07:30', 'arr': '09:00', 'dur': 90, 'dist': 301, 'stops': ['SHA', 'SZH', 'WXH', 'CZH', 'ZJH', 'NJH']},
        {'code': 'G7009', 'type': '高铁', 'start': 'SHA', 'end': 'NJH', 'dep': '08:00', 'arr': '09:30', 'dur': 90, 'dist': 301, 'stops': ['SHA', 'SZH', 'WXH', 'CZH', 'ZJH', 'NJH']},
        {'code': 'G7011', 'type': '高铁', 'start': 'SHA', 'end': 'NJH', 'dep': '09:00', 'arr': '10:30', 'dur': 90, 'dist': 301, 'stops': ['SHA', 'SZH', 'WXH', 'CZH', 'ZJH', 'NJH']},
        {'code': 'G7013', 'type': '高铁', 'start': 'SHA', 'end': 'NJH', 'dep': '10:00', 'arr': '11:30', 'dur': 90, 'dist': 301, 'stops': ['SHA', 'SZH', 'WXH', 'CZH', 'ZJH', 'NJH']},
        {'code': 'G7015', 'type': '高铁', 'start': 'SHA', 'end': 'NJH', 'dep': '11:00', 'arr': '12:30', 'dur': 90, 'dist': 301, 'stops': ['SHA', 'SZH', 'WXH', 'CZH', 'ZJH', 'NJH']},
        {'code': 'G7017', 'type': '高铁', 'start': 'SHA', 'end': 'NJH', 'dep': '12:00', 'arr': '13:30', 'dur': 90, 'dist': 301, 'stops': ['SHA', 'SZH', 'WXH', 'CZH', 'ZJH', 'NJH']},
        {'code': 'G7019', 'type': '高铁', 'start': 'SHA', 'end': 'NJH', 'dep': '13:00', 'arr': '14:30', 'dur': 90, 'dist': 301, 'stops': ['SHA', 'SZH', 'WXH', 'CZH', 'ZJH', 'NJH']},
        {'code': 'C3001', 'type': '城际', 'start': 'SHA', 'end': 'NJH', 'dep': '06:15', 'arr': '07:50', 'dur': 95, 'dist': 301, 'stops': ['SHA', 'SZH', 'WXH', 'CZH', 'ZJH', 'NJH']},
        {'code': 'C3003', 'type': '城际', 'start': 'SHA', 'end': 'NJH', 'dep': '07:15', 'arr': '08:50', 'dur': 95, 'dist': 301, 'stops': ['SHA', 'SZH', 'WXH', 'CZH', 'ZJH', 'NJH']},
        {'code': 'C3005', 'type': '城际', 'start': 'SHA', 'end': 'NJH', 'dep': '08:15', 'arr': '09:50', 'dur': 95, 'dist': 301, 'stops': ['SHA', 'SZH', 'WXH', 'CZH', 'ZJH', 'NJH']},
        {'code': 'C3007', 'type': '城际', 'start': 'SHA', 'end': 'NJH', 'dep': '09:15', 'arr': '10:50', 'dur': 95, 'dist': 301, 'stops': ['SHA', 'SZH', 'WXH', 'CZH', 'ZJH', 'NJH']},
        {'code': 'C3009', 'type': '城际', 'start': 'SHA', 'end': 'NJH', 'dep': '10:15', 'arr': '11:50', 'dur': 95, 'dist': 301, 'stops': ['SHA', 'SZH', 'WXH', 'CZH', 'ZJH', 'NJH']},
    ])
    
    # ========== 3. 宁杭高铁：南京南-杭州东==========
    train_data.extend([
        {'code': 'G7601', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '07:00', 'arr': '08:30', 'dur': 90, 'dist': 256, 'stops': ['NKH', 'YXH', 'HZN']},
        {'code': 'G7603', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '08:00', 'arr': '09:30', 'dur': 90, 'dist': 256, 'stops': ['NKH', 'YXH', 'HZN']},
        {'code': 'G7605', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '09:00', 'arr': '10:30', 'dur': 90, 'dist': 256, 'stops': ['NKH', 'YXH', 'HZN']},
        {'code': 'G7611', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '10:00', 'arr': '11:30', 'dur': 90, 'dist': 256, 'stops': ['NKH', 'YXH', 'HZN']},
        {'code': 'G7613', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '11:00', 'arr': '12:30', 'dur': 90, 'dist': 256, 'stops': ['NKH', 'YXH', 'HZN']},
        {'code': 'G7615', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '12:00', 'arr': '13:30', 'dur': 90, 'dist': 256, 'stops': ['NKH', 'YXH', 'HZN']},
        {'code': 'G7617', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '13:00', 'arr': '14:30', 'dur': 90, 'dist': 256, 'stops': ['NKH', 'YXH', 'HZN']},
        {'code': 'G7619', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '14:00', 'arr': '15:30', 'dur': 90, 'dist': 256, 'stops': ['NKH', 'YXH', 'HZN']},
        {'code': 'G7621', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '15:00', 'arr': '16:30', 'dur': 90, 'dist': 256, 'stops': ['NKH', 'YXH', 'HZN']},
        {'code': 'G7665', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '08:00', 'arr': '10:30', 'dur': 150, 'dist': 350, 'stops': ['NKH', 'YXH', 'HZN']},
        {'code': 'G7667', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '10:00', 'arr': '12:30', 'dur': 150, 'dist': 350, 'stops': ['NKH', 'YXH', 'HZN']},
        {'code': 'G7669', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '12:00', 'arr': '14:30', 'dur': 150, 'dist': 350, 'stops': ['NKH', 'YXH', 'HZN']},
        {'code': 'G7671', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '14:00', 'arr': '16:30', 'dur': 150, 'dist': 350, 'stops': ['NKH', 'YXH', 'HZN']},
        {'code': 'G7673', 'type': '高铁', 'start': 'NKH', 'end': 'HZN', 'dep': '16:00', 'arr': '18:30', 'dur': 150, 'dist': 350, 'stops': ['NKH', 'YXH', 'HZN']},
    ])
    
    # ========== 4. 沪昆高铁：上海虹桥-长沙南/昆明南==========
    train_data.extend([
        {'code': 'G1341', 'type': '高铁', 'start': 'SHH', 'end': 'CSQ', 'dep': '08:00', 'arr': '12:30', 'dur': 270, 'dist': 1150, 'stops': ['SHH', 'HZN', 'YWH', 'JHW', 'CSQ']},
        {'code': 'G1343', 'type': '高铁', 'start': 'SHH', 'end': 'CSQ', 'dep': '09:30', 'arr': '14:00', 'dur': 270, 'dist': 1150, 'stops': ['SHH', 'HZN', 'YWH', 'JHW', 'CSQ']},
        {'code': 'G1345', 'type': '高铁', 'start': 'SHH', 'end': 'CSQ', 'dep': '11:00', 'arr': '15:30', 'dur': 270, 'dist': 1150, 'stops': ['SHH', 'HZN', 'YWH', 'JHW', 'CSQ']},
        {'code': 'G1347', 'type': '高铁', 'start': 'SHH', 'end': 'CSQ', 'dep': '14:00', 'arr': '18:30', 'dur': 270, 'dist': 1150, 'stops': ['SHH', 'HZN', 'YWH', 'JHW', 'CSQ']},
        {'code': 'G1321', 'type': '高铁', 'start': 'SHH', 'end': 'CSQ', 'dep': '06:00', 'arr': '10:30', 'dur': 270, 'dist': 1150, 'stops': ['SHH', 'HZN', 'YWH', 'JHW', 'CSQ']},
        {'code': 'G1323', 'type': '高铁', 'start': 'SHH', 'end': 'CSQ', 'dep': '07:00', 'arr': '11:30', 'dur': 270, 'dist': 1150, 'stops': ['SHH', 'HZN', 'YWH', 'JHW', 'CSQ']},
        {'code': 'G1325', 'type': '高铁', 'start': 'SHH', 'end': 'CSQ', 'dep': '08:00', 'arr': '12:30', 'dur': 270, 'dist': 1150, 'stops': ['SHH', 'HZN', 'YWH', 'JHW', 'CSQ']},
        {'code': 'G1327', 'type': '高铁', 'start': 'SHH', 'end': 'CSQ', 'dep': '10:00', 'arr': '14:30', 'dur': 270, 'dist': 1150, 'stops': ['SHH', 'HZN', 'YWH', 'JHW', 'CSQ']},
        {'code': 'G1329', 'type': '高铁', 'start': 'SHH', 'end': 'CSQ', 'dep': '12:00', 'arr': '16:30', 'dur': 270, 'dist': 1150, 'stops': ['SHH', 'HZN', 'YWH', 'JHW', 'CSQ']},
        {'code': 'G1371', 'type': '高铁', 'start': 'SHH', 'end': 'KMG', 'dep': '07:00', 'arr': '19:00', 'dur': 720, 'dist': 2252, 'stops': ['SHH', 'HZN', 'YWH', 'JHW', 'QZH', 'FZS', 'KMG']},
        {'code': 'G1373', 'type': '高铁', 'start': 'SHH', 'end': 'KMG', 'dep': '09:00', 'arr': '21:00', 'dur': 720, 'dist': 2252, 'stops': ['SHH', 'HZN', 'YWH', 'JHW', 'QZH', 'FZS', 'KMG']},
        {'code': 'G1375', 'type': '高铁', 'start': 'SHH', 'end': 'KMG', 'dep': '11:00', 'arr': '23:00', 'dur': 720, 'dist': 2252, 'stops': ['SHH', 'HZN', 'YWH', 'JHW', 'QZH', 'FZS', 'KMG']},
    ])
    
    # ========== 5. 合福高铁：合肥南-福州南==========
    train_data.extend([
        {'code': 'G1611', 'type': '高铁', 'start': 'HFN', 'end': 'FZS', 'dep': '08:00', 'arr': '12:30', 'dur': 270, 'dist': 780, 'stops': ['HFN', 'JXX', 'HSZ', 'FZS']},
        {'code': 'G1613', 'type': '高铁', 'start': 'HFN', 'end': 'FZS', 'dep': '10:00', 'arr': '14:30', 'dur': 270, 'dist': 780, 'stops': ['HFN', 'JXX', 'HSZ', 'FZS']},
        {'code': 'G1615', 'type': '高铁', 'start': 'HFN', 'end': 'FZS', 'dep': '14:00', 'arr': '18:30', 'dur': 270, 'dist': 780, 'stops': ['HFN', 'JXX', 'HSZ', 'FZS']},
        {'code': 'G1617', 'type': '高铁', 'start': 'HFN', 'end': 'FZS', 'dep': '07:00', 'arr': '11:30', 'dur': 270, 'dist': 780, 'stops': ['HFN', 'JXX', 'HSZ', 'FZS']},
        {'code': 'G1619', 'type': '高铁', 'start': 'HFN', 'end': 'FZS', 'dep': '11:00', 'arr': '15:30', 'dur': 270, 'dist': 780, 'stops': ['HFN', 'JXX', 'HSZ', 'FZS']},
        {'code': 'G1621', 'type': '高铁', 'start': 'HFN', 'end': 'FZS', 'dep': '13:00', 'arr': '17:30', 'dur': 270, 'dist': 780, 'stops': ['HFN', 'JXX', 'HSZ', 'FZS']},
        {'code': 'G1623', 'type': '高铁', 'start': 'HFN', 'end': 'FZS', 'dep': '15:00', 'arr': '19:30', 'dur': 270, 'dist': 780, 'stops': ['HFN', 'JXX', 'HSZ', 'FZS']},
    ])
    
    # ========== 6. 杭深高铁：杭州东-深圳北==========
    train_data.extend([
        {'code': 'G7501', 'type': '高铁', 'start': 'HZN', 'end': 'SZN', 'dep': '07:00', 'arr': '12:00', 'dur': 300, 'dist': 1100, 'stops': ['HZN', 'NBH', 'WZH', 'SZN']},
        {'code': 'G7503', 'type': '高铁', 'start': 'HZN', 'end': 'SZN', 'dep': '08:00', 'arr': '13:00', 'dur': 300, 'dist': 1100, 'stops': ['HZN', 'NBH', 'WZH', 'SZN']},
        {'code': 'G7505', 'type': '高铁', 'start': 'HZN', 'end': 'SZN', 'dep': '09:00', 'arr': '14:00', 'dur': 300, 'dist': 1100, 'stops': ['HZN', 'NBH', 'WZH', 'SZN']},
        {'code': 'G7511', 'type': '高铁', 'start': 'HZN', 'end': 'SZN', 'dep': '10:00', 'arr': '15:00', 'dur': 300, 'dist': 1100, 'stops': ['HZN', 'NBH', 'WZH', 'SZN']},
        {'code': 'G7513', 'type': '高铁', 'start': 'HZN', 'end': 'SZN', 'dep': '11:00', 'arr': '16:00', 'dur': 300, 'dist': 1100, 'stops': ['HZN', 'NBH', 'WZH', 'SZN']},
        {'code': 'G7515', 'type': '高铁', 'start': 'HZN', 'end': 'SZN', 'dep': '12:00', 'arr': '17:00', 'dur': 300, 'dist': 1100, 'stops': ['HZN', 'NBH', 'WZH', 'SZN']},
        {'code': 'G7517', 'type': '高铁', 'start': 'HZN', 'end': 'SZN', 'dep': '13:00', 'arr': '18:00', 'dur': 300, 'dist': 1100, 'stops': ['HZN', 'NBH', 'WZH', 'SZN']},
        {'code': 'G7519', 'type': '高铁', 'start': 'HZN', 'end': 'SZN', 'dep': '14:00', 'arr': '19:00', 'dur': 300, 'dist': 1100, 'stops': ['HZN', 'NBH', 'WZH', 'SZN']},
        {'code': 'G7521', 'type': '高铁', 'start': 'HZN', 'end': 'SZN', 'dep': '15:00', 'arr': '20:00', 'dur': 300, 'dist': 1100, 'stops': ['HZN', 'NBH', 'WZH', 'SZN']},
    ])
    
    # ========== 7. 商合杭高铁：合肥南-杭州东==========
    train_data.extend([
        {'code': 'G7657', 'type': '高铁', 'start': 'HFN', 'end': 'HZN', 'dep': '08:00', 'arr': '11:00', 'dur': 180, 'dist': 450, 'stops': ['HFN', 'HNS', 'YXH', 'HZN']},
        {'code': 'G7659', 'type': '高铁', 'start': 'HFN', 'end': 'HZN', 'dep': '10:00', 'arr': '13:00', 'dur': 180, 'dist': 450, 'stops': ['HFN', 'HNS', 'YXH', 'HZN']},
        {'code': 'G7661', 'type': '高铁', 'start': 'HFN', 'end': 'HZN', 'dep': '13:00', 'arr': '16:00', 'dur': 180, 'dist': 450, 'stops': ['HFN', 'HNS', 'YXH', 'HZN']},
        {'code': 'G7663', 'type': '高铁', 'start': 'HFN', 'end': 'HZN', 'dep': '15:00', 'arr': '18:00', 'dur': 180, 'dist': 450, 'stops': ['HFN', 'HNS', 'YXH', 'HZN']},
        {'code': 'G7675', 'type': '高铁', 'start': 'HFN', 'end': 'HZN', 'dep': '08:00', 'arr': '11:00', 'dur': 180, 'dist': 450, 'stops': ['HFN', 'HNS', 'YXH', 'HZN']},
        {'code': 'G7677', 'type': '高铁', 'start': 'HFN', 'end': 'HZN', 'dep': '10:00', 'arr': '13:00', 'dur': 180, 'dist': 450, 'stops': ['HFN', 'HNS', 'YXH', 'HZN']},
        {'code': 'G7679', 'type': '高铁', 'start': 'HFN', 'end': 'HZN', 'dep': '13:00', 'arr': '16:00', 'dur': 180, 'dist': 450, 'stops': ['HFN', 'HNS', 'YXH', 'HZN']},
        {'code': 'G7681', 'type': '高铁', 'start': 'HFN', 'end': 'HZN', 'dep': '15:00', 'arr': '18:00', 'dur': 180, 'dist': 450, 'stops': ['HFN', 'HNS', 'YXH', 'HZN']},
    ])
    
    # ========== 8. 盐通高铁：盐城-南通（修复G9505重复，改用G9515）==========
    train_data.extend([
        {'code': 'G9515', 'type': '高铁', 'start': 'YCH', 'end': 'NTH', 'dep': '08:00', 'arr': '09:00', 'dur': 60, 'dist': 100, 'stops': ['YCH', 'DTZ', 'HAX', 'NTH']},
        {'code': 'G9517', 'type': '高铁', 'start': 'YCH', 'end': 'NTH', 'dep': '10:00', 'arr': '11:00', 'dur': 60, 'dist': 100, 'stops': ['YCH', 'DTZ', 'HAX', 'NTH']},
        {'code': 'G9519', 'type': '高铁', 'start': 'YCH', 'end': 'NTH', 'dep': '12:00', 'arr': '13:00', 'dur': 60, 'dist': 100, 'stops': ['YCH', 'DTZ', 'HAX', 'NTH']},
        {'code': 'G9521', 'type': '高铁', 'start': 'YCH', 'end': 'NTH', 'dep': '14:00', 'arr': '15:00', 'dur': 60, 'dist': 100, 'stops': ['YCH', 'DTZ', 'HAX', 'NTH']},
        {'code': 'G9523', 'type': '高铁', 'start': 'YCH', 'end': 'NTH', 'dep': '16:00', 'arr': '17:00', 'dur': 60, 'dist': 100, 'stops': ['YCH', 'DTZ', 'HAX', 'NTH']},
        {'code': 'G9525', 'type': '高铁', 'start': 'NTH', 'end': 'YCH', 'dep': '09:00', 'arr': '10:00', 'dur': 60, 'dist': 100, 'stops': ['NTH', 'HAX', 'DTZ', 'YCH']},
        {'code': 'G9527', 'type': '高铁', 'start': 'NTH', 'end': 'YCH', 'dep': '11:00', 'arr': '12:00', 'dur': 60, 'dist': 100, 'stops': ['NTH', 'HAX', 'DTZ', 'YCH']},
        {'code': 'G9529', 'type': '高铁', 'start': 'NTH', 'end': 'YCH', 'dep': '13:00', 'arr': '14:00', 'dur': 60, 'dist': 100, 'stops': ['NTH', 'HAX', 'DTZ', 'YCH']},
    ])
    
    # ========== 9. 连镇高铁：连云港-镇江==========
    train_data.extend([
        {'code': 'G9509', 'type': '高铁', 'start': 'LGH', 'end': 'ZJN', 'dep': '08:00', 'arr': '10:30', 'dur': 150, 'dist': 200, 'stops': ['LGH', 'HAD', 'GYH', 'ZJN']},
        {'code': 'G9511', 'type': '高铁', 'start': 'LGH', 'end': 'ZJN', 'dep': '11:00', 'arr': '13:30', 'dur': 150, 'dist': 200, 'stops': ['LGH', 'HAD', 'GYH', 'ZJN']},
        {'code': 'G9513', 'type': '高铁', 'start': 'LGH', 'end': 'ZJN', 'dep': '14:00', 'arr': '16:30', 'dur': 150, 'dist': 200, 'stops': ['LGH', 'HAD', 'GYH', 'ZJN']},
        {'code': 'G9509A', 'type': '高铁', 'start': 'ZJN', 'end': 'LGH', 'dep': '09:00', 'arr': '11:30', 'dur': 150, 'dist': 200, 'stops': ['ZJN', 'GYH', 'HAD', 'LGH']},
        {'code': 'G9511A', 'type': '高铁', 'start': 'ZJN', 'end': 'LGH', 'dep': '12:00', 'arr': '14:30', 'dur': 150, 'dist': 200, 'stops': ['ZJN', 'GYH', 'HAD', 'LGH']},
        {'code': 'G9513A', 'type': '高铁', 'start': 'ZJN', 'end': 'LGH', 'dep': '15:00', 'arr': '17:30', 'dur': 150, 'dist': 200, 'stops': ['ZJN', 'GYH', 'HAD', 'LGH']},
    ])
    
    # ========== 10. 合安高铁：合肥南-安庆（修复G9505重复，改用G9502）==========
    train_data.extend([
        {'code': 'G9501', 'type': '高铁', 'start': 'HFN', 'end': 'AQH', 'dep': '07:00', 'arr': '08:00', 'dur': 60, 'dist': 180, 'stops': ['HFN', 'CHH', 'TCZ', 'AQH']},
        {'code': 'G9502', 'type': '高铁', 'start': 'HFN', 'end': 'AQH', 'dep': '09:00', 'arr': '10:00', 'dur': 60, 'dist': 180, 'stops': ['HFN', 'CHH', 'TCZ', 'AQH']},
        {'code': 'G9503', 'type': '高铁', 'start': 'HFN', 'end': 'AQH', 'dep': '11:00', 'arr': '12:00', 'dur': 60, 'dist': 180, 'stops': ['HFN', 'CHH', 'TCZ', 'AQH']},
        {'code': 'G9504', 'type': '高铁', 'start': 'AQH', 'end': 'HFN', 'dep': '08:00', 'arr': '09:00', 'dur': 60, 'dist': 180, 'stops': ['AQH', 'TCZ', 'CHH', 'HFN']},
        {'code': 'G9506', 'type': '高铁', 'start': 'AQH', 'end': 'HFN', 'dep': '10:00', 'arr': '11:00', 'dur': 60, 'dist': 180, 'stops': ['AQH', 'TCZ', 'CHH', 'HFN']},
        {'code': 'G9508', 'type': '高铁', 'start': 'AQH', 'end': 'HFN', 'dep': '13:00', 'arr': '14:00', 'dur': 60, 'dist': 180, 'stops': ['AQH', 'TCZ', 'CHH', 'HFN']},
    ])
    
    # ========== 11. 宁安城际：南京南-安庆==========
    train_data.extend([
        {'code': 'D9501', 'type': '动车', 'start': 'NKH', 'end': 'AQH', 'dep': '07:30', 'arr': '10:00', 'dur': 150, 'dist': 280, 'stops': ['NKH', 'WHH', 'FCZ', 'AQH']},
        {'code': 'D9503', 'type': '动车', 'start': 'NKH', 'end': 'AQH', 'dep': '09:30', 'arr': '12:00', 'dur': 150, 'dist': 280, 'stops': ['NKH', 'WHH', 'FCZ', 'AQH']},
        {'code': 'D9505', 'type': '动车', 'start': 'NKH', 'end': 'AQH', 'dep': '14:00', 'arr': '16:30', 'dur': 150, 'dist': 280, 'stops': ['NKH', 'WHH', 'FCZ', 'AQH']},
        {'code': 'D9507', 'type': '动车', 'start': 'NKH', 'end': 'AQH', 'dep': '16:30', 'arr': '19:00', 'dur': 150, 'dist': 280, 'stops': ['NKH', 'WHH', 'FCZ', 'AQH']},
        {'code': 'D9502', 'type': '动车', 'start': 'AQH', 'end': 'NKH', 'dep': '08:00', 'arr': '10:30', 'dur': 150, 'dist': 280, 'stops': ['AQH', 'FCZ', 'WHH', 'NKH']},
        {'code': 'D9504', 'type': '动车', 'start': 'AQH', 'end': 'NKH', 'dep': '11:00', 'arr': '13:30', 'dur': 150, 'dist': 280, 'stops': ['AQH', 'FCZ', 'WHH', 'NKH']},
        {'code': 'D9506', 'type': '动车', 'start': 'AQH', 'end': 'NKH', 'dep': '15:00', 'arr': '17:30', 'dur': 150, 'dist': 280, 'stops': ['AQH', 'FCZ', 'WHH', 'NKH']},
    ])
    
    # ========== 12. 京港高铁合肥段：合肥南-深圳北==========
    train_data.extend([
        {'code': 'G2791', 'type': '高铁', 'start': 'HFN', 'end': 'SZN', 'dep': '08:00', 'arr': '15:00', 'dur': 420, 'dist': 1400, 'stops': ['HFN', 'HNS', 'HZN', 'NBH', 'WZH', 'SZN']},
        {'code': 'G2793', 'type': '高铁', 'start': 'HFN', 'end': 'SZN', 'dep': '10:00', 'arr': '17:00', 'dur': 420, 'dist': 1400, 'stops': ['HFN', 'HNS', 'HZN', 'NBH', 'WZH', 'SZN']},
        {'code': 'G2795', 'type': '高铁', 'start': 'SZN', 'end': 'HFN', 'dep': '08:00', 'arr': '15:00', 'dur': 420, 'dist': 1400, 'stops': ['SZN', 'WZH', 'NBH', 'HZN', 'HNS', 'HFN']},
        {'code': 'G2797', 'type': '高铁', 'start': 'SZN', 'end': 'HFN', 'dep': '10:00', 'arr': '17:00', 'dur': 420, 'dist': 1400, 'stops': ['SZN', 'WZH', 'NBH', 'HZN', 'HNS', 'HFN']},
    ])
    
    # ========== 13. 徐兰高铁安徽段：徐州东-西安北==========
    train_data.extend([
        {'code': 'G1920', 'type': '高铁', 'start': 'XZN', 'end': 'XAF', 'dep': '08:00', 'arr': '14:00', 'dur': 360, 'dist': 600, 'stops': ['XZN', 'SJP', 'TYN', 'XAF']},
        {'code': 'G1922', 'type': '高铁', 'start': 'XZN', 'end': 'XAF', 'dep': '10:00', 'arr': '16:00', 'dur': 360, 'dist': 600, 'stops': ['XZN', 'SJP', 'TYN', 'XAF']},
        {'code': 'G1924', 'type': '高铁', 'start': 'XZN', 'end': 'XAF', 'dep': '13:00', 'arr': '19:00', 'dur': 360, 'dist': 600, 'stops': ['XZN', 'SJP', 'TYN', 'XAF']},
        {'code': 'G1921', 'type': '高铁', 'start': 'XAF', 'end': 'XZN', 'dep': '08:00', 'arr': '14:00', 'dur': 360, 'dist': 600, 'stops': ['XAF', 'TYN', 'SJP', 'XZN']},
        {'code': 'G1923', 'type': '高铁', 'start': 'XAF', 'end': 'XZN', 'dep': '11:00', 'arr': '17:00', 'dur': 360, 'dist': 600, 'stops': ['XAF', 'TYN', 'SJP', 'XZN']},
    ])
    
    # ========== 14. 上海-宁波==========
    train_data.extend([
        {'code': 'G7531', 'type': '高铁', 'start': 'SHA', 'end': 'NBH', 'dep': '08:00', 'arr': '10:00', 'dur': 120, 'dist': 320, 'stops': ['SHA', 'HZH', 'NBH']},
        {'code': 'G7533', 'type': '高铁', 'start': 'SHA', 'end': 'NBH', 'dep': '10:00', 'arr': '12:00', 'dur': 120, 'dist': 320, 'stops': ['SHA', 'HZH', 'NBH']},
        {'code': 'G7535', 'type': '高铁', 'start': 'SHA', 'end': 'NBH', 'dep': '13:00', 'arr': '15:00', 'dur': 120, 'dist': 320, 'stops': ['SHA', 'HZH', 'NBH']},
        {'code': 'G7537', 'type': '高铁', 'start': 'SHA', 'end': 'NBH', 'dep': '15:00', 'arr': '17:00', 'dur': 120, 'dist': 320, 'stops': ['SHA', 'HZH', 'NBH']},
        {'code': 'G7539', 'type': '高铁', 'start': 'SHA', 'end': 'NBH', 'dep': '17:00', 'arr': '19:00', 'dur': 120, 'dist': 320, 'stops': ['SHA', 'HZH', 'NBH']},
        {'code': 'G7532', 'type': '高铁', 'start': 'NBH', 'end': 'SHA', 'dep': '08:00', 'arr': '10:00', 'dur': 120, 'dist': 320, 'stops': ['NBH', 'HZH', 'SHA']},
        {'code': 'G7534', 'type': '高铁', 'start': 'NBH', 'end': 'SHA', 'dep': '10:00', 'arr': '12:00', 'dur': 120, 'dist': 320, 'stops': ['NBH', 'HZH', 'SHA']},
        {'code': 'G7536', 'type': '高铁', 'start': 'NBH', 'end': 'SHA', 'dep': '13:00', 'arr': '15:00', 'dur': 120, 'dist': 320, 'stops': ['NBH', 'HZH', 'SHA']},
        {'code': 'G7538', 'type': '高铁', 'start': 'NBH', 'end': 'SHA', 'dep': '15:00', 'arr': '17:00', 'dur': 120, 'dist': 320, 'stops': ['NBH', 'HZH', 'SHA']},
    ])
    
    # ========== 15. 杭州-温州：D3231系列==========
    train_data.extend([
        {'code': 'D3231', 'type': '动车', 'start': 'HZN', 'end': 'WZH', 'dep': '09:00', 'arr': '11:30', 'dur': 150, 'dist': 350, 'stops': ['HZN', 'YQZ', 'WZH']},
        {'code': 'D3233', 'type': '动车', 'start': 'HZN', 'end': 'WZH', 'dep': '14:00', 'arr': '16:30', 'dur': 150, 'dist': 350, 'stops': ['HZN', 'YQZ', 'WZH']},
        {'code': 'D3235', 'type': '动车', 'start': 'HZN', 'end': 'WZH', 'dep': '08:00', 'arr': '10:30', 'dur': 150, 'dist': 350, 'stops': ['HZN', 'YQZ', 'WZH']},
        {'code': 'D3237', 'type': '动车', 'start': 'HZN', 'end': 'WZH', 'dep': '11:00', 'arr': '13:30', 'dur': 150, 'dist': 350, 'stops': ['HZN', 'YQZ', 'WZH']},
        {'code': 'D3232', 'type': '动车', 'start': 'WZH', 'end': 'HZN', 'dep': '09:00', 'arr': '11:30', 'dur': 150, 'dist': 350, 'stops': ['WZH', 'YQZ', 'HZN']},
        {'code': 'D3234', 'type': '动车', 'start': 'WZH', 'end': 'HZN', 'dep': '14:00', 'arr': '16:30', 'dur': 150, 'dist': 350, 'stops': ['WZH', 'YQZ', 'HZN']},
        {'code': 'G7623', 'type': '高铁', 'start': 'HZN', 'end': 'WZH', 'dep': '08:00', 'arr': '10:00', 'dur': 120, 'dist': 350, 'stops': ['HZN', 'YQZ', 'WZH']},
        {'code': 'G7625', 'type': '高铁', 'start': 'HZN', 'end': 'WZH', 'dep': '10:00', 'arr': '12:00', 'dur': 120, 'dist': 350, 'stops': ['HZN', 'YQZ', 'WZH']},
        {'code': 'G7627', 'type': '高铁', 'start': 'HZN', 'end': 'WZH', 'dep': '13:00', 'arr': '15:00', 'dur': 120, 'dist': 350, 'stops': ['HZN', 'YQZ', 'WZH']},
        {'code': 'G7624', 'type': '高铁', 'start': 'WZH', 'end': 'HZN', 'dep': '09:00', 'arr': '11:00', 'dur': 120, 'dist': 350, 'stops': ['WZH', 'YQZ', 'HZN']},
        {'code': 'G7626', 'type': '高铁', 'start': 'WZH', 'end': 'HZN', 'dep': '11:00', 'arr': '13:00', 'dur': 120, 'dist': 350, 'stops': ['WZH', 'YQZ', 'HZN']},
    ])
    
    # ========== 16. 合肥-黄山==========
    train_data.extend([
        {'code': 'D5591', 'type': '动车', 'start': 'HFN', 'end': 'HSZ', 'dep': '08:00', 'arr': '11:00', 'dur': 180, 'dist': 350, 'stops': ['HFN', 'JXX', 'HSZ']},
        {'code': 'D5593', 'type': '动车', 'start': 'HFN', 'end': 'HSZ', 'dep': '12:00', 'arr': '15:00', 'dur': 180, 'dist': 350, 'stops': ['HFN', 'JXX', 'HSZ']},
        {'code': 'D5595', 'type': '动车', 'start': 'HFN', 'end': 'HSZ', 'dep': '16:00', 'arr': '19:00', 'dur': 180, 'dist': 350, 'stops': ['HFN', 'JXX', 'HSZ']},
        {'code': 'D5592', 'type': '动车', 'start': 'HSZ', 'end': 'HFN', 'dep': '08:00', 'arr': '11:00', 'dur': 180, 'dist': 350, 'stops': ['HSZ', 'JXX', 'HFN']},
        {'code': 'D5594', 'type': '动车', 'start': 'HSZ', 'end': 'HFN', 'dep': '12:00', 'arr': '15:00', 'dur': 180, 'dist': 350, 'stops': ['HSZ', 'JXX', 'HFN']},
    ])
    
    # ========== 17. 沪苏通：上海-南通==========
    train_data.extend([
        {'code': 'C3811', 'type': '城际', 'start': 'SHA', 'end': 'NTH', 'dep': '07:00', 'arr': '08:30', 'dur': 90, 'dist': 120, 'stops': ['SHA', 'JSW', 'NTH']},
        {'code': 'C3813', 'type': '城际', 'start': 'SHA', 'end': 'NTH', 'dep': '09:00', 'arr': '10:30', 'dur': 90, 'dist': 120, 'stops': ['SHA', 'JSW', 'NTH']},
        {'code': 'C3815', 'type': '城际', 'start': 'SHA', 'end': 'NTH', 'dep': '11:00', 'arr': '12:30', 'dur': 90, 'dist': 120, 'stops': ['SHA', 'JSW', 'NTH']},
        {'code': 'C3817', 'type': '城际', 'start': 'SHA', 'end': 'NTH', 'dep': '14:00', 'arr': '15:30', 'dur': 90, 'dist': 120, 'stops': ['SHA', 'JSW', 'NTH']},
        {'code': 'C3819', 'type': '城际', 'start': 'SHA', 'end': 'NTH', 'dep': '16:00', 'arr': '17:30', 'dur': 90, 'dist': 120, 'stops': ['SHA', 'JSW', 'NTH']},
        {'code': 'C3821', 'type': '城际', 'start': 'SHA', 'end': 'NTH', 'dep': '18:00', 'arr': '19:30', 'dur': 90, 'dist': 120, 'stops': ['SHA', 'JSW', 'NTH']},
        {'code': 'C3812', 'type': '城际', 'start': 'NTH', 'end': 'SHA', 'dep': '07:30', 'arr': '09:00', 'dur': 90, 'dist': 120, 'stops': ['NTH', 'JSW', 'SHA']},
        {'code': 'C3814', 'type': '城际', 'start': 'NTH', 'end': 'SHA', 'dep': '09:30', 'arr': '11:00', 'dur': 90, 'dist': 120, 'stops': ['NTH', 'JSW', 'SHA']},
        {'code': 'C3816', 'type': '城际', 'start': 'NTH', 'end': 'SHA', 'dep': '11:30', 'arr': '13:00', 'dur': 90, 'dist': 120, 'stops': ['NTH', 'JSW', 'SHA']},
        {'code': 'C3818', 'type': '城际', 'start': 'NTH', 'end': 'SHA', 'dep': '14:30', 'arr': '16:00', 'dur': 90, 'dist': 120, 'stops': ['NTH', 'JSW', 'SHA']},
    ])
    
    # ========== 18. 宁启线：南京-南通/扬州==========
    train_data.extend([
        {'code': 'C3751', 'type': '城际', 'start': 'NJH', 'end': 'NTH', 'dep': '08:00', 'arr': '10:30', 'dur': 150, 'dist': 260, 'stops': ['NJH', 'YZH', 'NTH']},
        {'code': 'C3753', 'type': '城际', 'start': 'NJH', 'end': 'NTH', 'dep': '10:00', 'arr': '12:30', 'dur': 150, 'dist': 260, 'stops': ['NJH', 'YZH', 'NTH']},
        {'code': 'C3755', 'type': '城际', 'start': 'NJH', 'end': 'NTH', 'dep': '14:00', 'arr': '16:30', 'dur': 150, 'dist': 260, 'stops': ['NJH', 'YZH', 'NTH']},
        {'code': 'C3757', 'type': '城际', 'start': 'NJH', 'end': 'NTH', 'dep': '16:00', 'arr': '18:30', 'dur': 150, 'dist': 260, 'stops': ['NJH', 'YZH', 'NTH']},
        {'code': 'C3752', 'type': '城际', 'start': 'NTH', 'end': 'NJH', 'dep': '08:30', 'arr': '11:00', 'dur': 150, 'dist': 260, 'stops': ['NTH', 'YZH', 'NJH']},
        {'code': 'C3754', 'type': '城际', 'start': 'NTH', 'end': 'NJH', 'dep': '11:00', 'arr': '13:30', 'dur': 150, 'dist': 260, 'stops': ['NTH', 'YZH', 'NJH']},
        {'code': 'C3756', 'type': '城际', 'start': 'NTH', 'end': 'NJH', 'dep': '15:00', 'arr': '17:30', 'dur': 150, 'dist': 260, 'stops': ['NTH', 'YZH', 'NJH']},
        {'code': 'C3758', 'type': '城际', 'start': 'NTH', 'end': 'NJH', 'dep': '17:00', 'arr': '19:30', 'dur': 150, 'dist': 260, 'stops': ['NTH', 'YZH', 'NJH']},
    ])
    
    # ========== 19. 金山线：上海南-金山卫==========
    train_data.extend([
        {'code': 'C3001', 'type': '城际', 'start': 'SNH', 'end': 'JSW', 'dep': '06:00', 'arr': '06:40', 'dur': 40, 'dist': 56, 'stops': ['SNH', 'JTB', 'JSW']},
        {'code': 'C3003', 'type': '城际', 'start': 'SNH', 'end': 'JSW', 'dep': '07:00', 'arr': '07:40', 'dur': 40, 'dist': 56, 'stops': ['SNH', 'JTB', 'JSW']},
        {'code': 'C3005', 'type': '城际', 'start': 'SNH', 'end': 'JSW', 'dep': '08:00', 'arr': '08:40', 'dur': 40, 'dist': 56, 'stops': ['SNH', 'JTB', 'JSW']},
        {'code': 'C3007', 'type': '城际', 'start': 'SNH', 'end': 'JSW', 'dep': '09:00', 'arr': '09:40', 'dur': 40, 'dist': 56, 'stops': ['SNH', 'JTB', 'JSW']},
        {'code': 'C3009', 'type': '城际', 'start': 'SNH', 'end': 'JSW', 'dep': '10:00', 'arr': '10:40', 'dur': 40, 'dist': 56, 'stops': ['SNH', 'JTB', 'JSW']},
        {'code': 'C3011', 'type': '城际', 'start': 'SNH', 'end': 'JSW', 'dep': '11:00', 'arr': '11:40', 'dur': 40, 'dist': 56, 'stops': ['SNH', 'JTB', 'JSW']},
        {'code': 'C3013', 'type': '城际', 'start': 'SNH', 'end': 'JSW', 'dep': '12:00', 'arr': '12:40', 'dur': 40, 'dist': 56, 'stops': ['SNH', 'JTB', 'JSW']},
        {'code': 'C3015', 'type': '城际', 'start': 'SNH', 'end': 'JSW', 'dep': '13:00', 'arr': '13:40', 'dur': 40, 'dist': 56, 'stops': ['SNH', 'JTB', 'JSW']},
        {'code': 'C3002', 'type': '城际', 'start': 'JSW', 'end': 'SNH', 'dep': '06:30', 'arr': '07:10', 'dur': 40, 'dist': 56, 'stops': ['JSW', 'JTB', 'SNH']},
        {'code': 'C3004', 'type': '城际', 'start': 'JSW', 'end': 'SNH', 'dep': '07:30', 'arr': '08:10', 'dur': 40, 'dist': 56, 'stops': ['JSW', 'JTB', 'SNH']},
        {'code': 'C3006', 'type': '城际', 'start': 'JSW', 'end': 'SNH', 'dep': '08:30', 'arr': '09:10', 'dur': 40, 'dist': 56, 'stops': ['JSW', 'JTB', 'SNH']},
        {'code': 'C3008', 'type': '城际', 'start': 'JSW', 'end': 'SNH', 'dep': '09:30', 'arr': '10:10', 'dur': 40, 'dist': 56, 'stops': ['JSW', 'JTB', 'SNH']},
    ])
    
    # ========== 20. 京沪线普速：T110/Z166/K101等==========
    train_data.extend([
        {'code': 'T110', 'type': '普速', 'start': 'SHA', 'end': 'BJP', 'dep': '18:00', 'arr': '09:00', 'dur': 900, 'dist': 1463, 'stops': ['SHA', 'NJH', 'XZH', 'BJP']},
        {'code': 'T132', 'type': '普速', 'start': 'SHA', 'end': 'BJP', 'dep': '19:00', 'arr': '10:00', 'dur': 900, 'dist': 1463, 'stops': ['SHA', 'NJH', 'XZH', 'BJP']},
        {'code': 'Z166', 'type': '普速', 'start': 'SHA', 'end': 'BJP', 'dep': '20:00', 'arr': '11:00', 'dur': 900, 'dist': 1463, 'stops': ['SHA', 'NJH', 'XZH', 'BJP']},
        {'code': 'K101', 'type': '普速', 'start': 'SHA', 'end': 'BJP', 'dep': '12:00', 'arr': '08:00', 'dur': 1200, 'dist': 1463, 'stops': ['SHA', 'NJH', 'XZH', 'BJP']},
        {'code': 'Z268', 'type': '普速', 'start': 'SHA', 'end': 'BJP', 'dep': '14:00', 'arr': '07:00', 'dur': 1020, 'dist': 1463, 'stops': ['SHA', 'NJH', 'XZH', 'BJP']},
        {'code': 'K47', 'type': '普速', 'start': 'SHA', 'end': 'BJP', 'dep': '15:00', 'arr': '12:00', 'dur': 1260, 'dist': 1463, 'stops': ['SHA', 'NJH', 'XZH', 'BJP']},
        {'code': 'K145', 'type': '普速', 'start': 'SHA', 'end': 'BJP', 'dep': '16:00', 'arr': '14:00', 'dur': 1320, 'dist': 1463, 'stops': ['SHA', 'NJH', 'XZH', 'BJP']},
    ])
    
    # ========== 21. 沪昆线普速：K71/T77等==========
    train_data.extend([
        {'code': 'K71', 'type': '普速', 'start': 'SNH', 'end': 'KMG', 'dep': '14:00', 'arr': '21:00', 'dur': 2100, 'dist': 2252, 'stops': ['SNH', 'HZH', 'JHW', 'KMG']},
        {'code': 'K79', 'type': '普速', 'start': 'SNH', 'end': 'KMG', 'dep': '16:00', 'arr': '23:00', 'dur': 2100, 'dist': 2252, 'stops': ['SNH', 'HZH', 'JHW', 'KMG']},
        {'code': 'T77', 'type': '普速', 'start': 'SNH', 'end': 'KMG', 'dep': '18:00', 'arr': '18:00', 'dur': 1440, 'dist': 2252, 'stops': ['SNH', 'HZH', 'JHW', 'KMG']},
        {'code': 'K111', 'type': '普速', 'start': 'SNH', 'end': 'KMG', 'dep': '12:00', 'arr': '18:00', 'dur': 2160, 'dist': 2252, 'stops': ['SNH', 'HZH', 'JHW', 'KMG']},
        {'code': 'K495', 'type': '普速', 'start': 'SNH', 'end': 'KMG', 'dep': '14:00', 'arr': '20:00', 'dur': 2160, 'dist': 2252, 'stops': ['SNH', 'HZH', 'JHW', 'KMG']},
        {'code': 'K739', 'type': '普速', 'start': 'SNH', 'end': 'KMG', 'dep': '16:00', 'arr': '22:00', 'dur': 2160, 'dist': 2252, 'stops': ['SNH', 'HZH', 'JHW', 'KMG']},
    ])
    
    # ========== 22. 宁铜线：南京-铜陵==========
    train_data.extend([
        {'code': 'K8421', 'type': '普速', 'start': 'NJH', 'end': 'TLZ', 'dep': '07:00', 'arr': '11:30', 'dur': 270, 'dist': 250, 'stops': ['NJH', 'WHH', 'TLZ']},
        {'code': 'T7777', 'type': '普速', 'start': 'NJH', 'end': 'TLZ', 'dep': '13:00', 'arr': '17:30', 'dur': 270, 'dist': 250, 'stops': ['NJH', 'WHH', 'TLZ']},
        {'code': 'K1551', 'type': '普速', 'start': 'NJH', 'end': 'TLZ', 'dep': '08:00', 'arr': '12:00', 'dur': 240, 'dist': 250, 'stops': ['NJH', 'WHH', 'TLZ']},
        {'code': 'K5901', 'type': '普速', 'start': 'NJH', 'end': 'TLZ', 'dep': '15:00', 'arr': '19:00', 'dur': 240, 'dist': 250, 'stops': ['NJH', 'WHH', 'TLZ']},
        {'code': 'K8422', 'type': '普速', 'start': 'TLZ', 'end': 'NJH', 'dep': '07:30', 'arr': '12:00', 'dur': 270, 'dist': 250, 'stops': ['TLZ', 'WHH', 'NJH']},
        {'code': 'T7778', 'type': '普速', 'start': 'TLZ', 'end': 'NJH', 'dep': '13:30', 'arr': '18:00', 'dur': 270, 'dist': 250, 'stops': ['TLZ', 'WHH', 'NJH']},
    ])
    
    # ========== 23. 皖赣线：南京-黄山==========
    train_data.extend([
        {'code': 'K45', 'type': '普速', 'start': 'NJH', 'end': 'HSZ', 'dep': '08:00', 'arr': '15:00', 'dur': 420, 'dist': 400, 'stops': ['NJH', 'XCZ', 'HSZ']},
        {'code': 'K155', 'type': '普速', 'start': 'NJH', 'end': 'HSZ', 'dep': '10:00', 'arr': '17:00', 'dur': 420, 'dist': 400, 'stops': ['NJH', 'XCZ', 'HSZ']},
        {'code': 'K783', 'type': '普速', 'start': 'NJH', 'end': 'HSZ', 'dep': '14:00', 'arr': '21:00', 'dur': 420, 'dist': 400, 'stops': ['NJH', 'XCZ', 'HSZ']},
        {'code': 'K46', 'type': '普速', 'start': 'HSZ', 'end': 'NJH', 'dep': '08:00', 'arr': '15:00', 'dur': 420, 'dist': 400, 'stops': ['HSZ', 'XCZ', 'NJH']},
        {'code': 'K156', 'type': '普速', 'start': 'HSZ', 'end': 'NJH', 'dep': '11:00', 'arr': '18:00', 'dur': 420, 'dist': 400, 'stops': ['HSZ', 'XCZ', 'NJH']},
    ])
    
    # ========== 更多重要车次 ==========
    
    # 上海-杭州方向
    train_data.extend([
        {'code': 'G9301', 'type': '高铁', 'start': 'SHA', 'end': 'HZH', 'dep': '07:00', 'arr': '08:30', 'dur': 90, 'dist': 202, 'stops': ['SHA', 'HZH']},
        {'code': 'G9303', 'type': '高铁', 'start': 'SHA', 'end': 'HZH', 'dep': '08:00', 'arr': '09:30', 'dur': 90, 'dist': 202, 'stops': ['SHA', 'HZH']},
        {'code': 'G9305', 'type': '高铁', 'start': 'SHA', 'end': 'HZH', 'dep': '09:00', 'arr': '10:30', 'dur': 90, 'dist': 202, 'stops': ['SHA', 'HZH']},
        {'code': 'G9307', 'type': '高铁', 'start': 'SHA', 'end': 'HZH', 'dep': '10:00', 'arr': '11:30', 'dur': 90, 'dist': 202, 'stops': ['SHA', 'HZH']},
        {'code': 'G9309', 'type': '高铁', 'start': 'SHA', 'end': 'HZH', 'dep': '11:00', 'arr': '12:30', 'dur': 90, 'dist': 202, 'stops': ['SHA', 'HZH']},
    ])
    
    # 上海虹桥-杭州东
    train_data.extend([
        {'code': 'G9311', 'type': '高铁', 'start': 'SHH', 'end': 'HZN', 'dep': '07:30', 'arr': '08:50', 'dur': 80, 'dist': 202, 'stops': ['SHH', 'HZN']},
        {'code': 'G9313', 'type': '高铁', 'start': 'SHH', 'end': 'HZN', 'dep': '08:30', 'arr': '09:50', 'dur': 80, 'dist': 202, 'stops': ['SHH', 'HZN']},
        {'code': 'G9315', 'type': '高铁', 'start': 'SHH', 'end': 'HZN', 'dep': '09:30', 'arr': '10:50', 'dur': 80, 'dist': 202, 'stops': ['SHH', 'HZN']},
        {'code': 'G9317', 'type': '高铁', 'start': 'SHH', 'end': 'HZN', 'dep': '10:30', 'arr': '11:50', 'dur': 80, 'dist': 202, 'stops': ['SHH', 'HZN']},
        {'code': 'G9319', 'type': '高铁', 'start': 'SHH', 'end': 'HZN', 'dep': '11:30', 'arr': '12:50', 'dur': 80, 'dist': 202, 'stops': ['SHH', 'HZN']},
        {'code': 'G9321', 'type': '高铁', 'start': 'SHH', 'end': 'HZN', 'dep': '13:30', 'arr': '14:50', 'dur': 80, 'dist': 202, 'stops': ['SHH', 'HZN']},
        {'code': 'G9323', 'type': '高铁', 'start': 'SHH', 'end': 'HZN', 'dep': '14:30', 'arr': '15:50', 'dur': 80, 'dist': 202, 'stops': ['SHH', 'HZN']},
        {'code': 'G9325', 'type': '高铁', 'start': 'SHH', 'end': 'HZN', 'dep': '15:30', 'arr': '16:50', 'dur': 80, 'dist': 202, 'stops': ['SHH', 'HZN']},
    ])
    
    # 南京-上海
    train_data.extend([
        {'code': 'G7101', 'type': '高铁', 'start': 'NJH', 'end': 'SHA', 'dep': '07:00', 'arr': '08:30', 'dur': 90, 'dist': 301, 'stops': ['NJH', 'ZJH', 'CZH', 'WXH', 'SZH', 'SHA']},
        {'code': 'G7103', 'type': '高铁', 'start': 'NJH', 'end': 'SHA', 'dep': '08:00', 'arr': '09:30', 'dur': 90, 'dist': 301, 'stops': ['NJH', 'ZJH', 'CZH', 'WXH', 'SZH', 'SHA']},
        {'code': 'G7105', 'type': '高铁', 'start': 'NJH', 'end': 'SHA', 'dep': '09:00', 'arr': '10:30', 'dur': 90, 'dist': 301, 'stops': ['NJH', 'ZJH', 'CZH', 'WXH', 'SZH', 'SHA']},
        {'code': 'G7107', 'type': '高铁', 'start': 'NJH', 'end': 'SHA', 'dep': '10:00', 'arr': '11:30', 'dur': 90, 'dist': 301, 'stops': ['NJH', 'ZJH', 'CZH', 'WXH', 'SZH', 'SHA']},
        {'code': 'G7109', 'type': '高铁', 'start': 'NJH', 'end': 'SHA', 'dep': '11:00', 'arr': '12:30', 'dur': 90, 'dist': 301, 'stops': ['NJH', 'ZJH', 'CZH', 'WXH', 'SZH', 'SHA']},
        {'code': 'G7111', 'type': '高铁', 'start': 'NJH', 'end': 'SHA', 'dep': '12:00', 'arr': '13:30', 'dur': 90, 'dist': 301, 'stops': ['NJH', 'ZJH', 'CZH', 'WXH', 'SZH', 'SHA']},
        {'code': 'G7113', 'type': '高铁', 'start': 'NJH', 'end': 'SHA', 'dep': '13:00', 'arr': '14:30', 'dur': 90, 'dist': 301, 'stops': ['NJH', 'ZJH', 'CZH', 'WXH', 'SZH', 'SHA']},
        {'code': 'G7115', 'type': '高铁', 'start': 'NJH', 'end': 'SHA', 'dep': '14:00', 'arr': '15:30', 'dur': 90, 'dist': 301, 'stops': ['NJH', 'ZJH', 'CZH', 'WXH', 'SZH', 'SHA']},
    ])
    
    # 徐州-南京
    train_data.extend([
        {'code': 'G7121', 'type': '高铁', 'start': 'XZH', 'end': 'NJH', 'dep': '08:00', 'arr': '10:00', 'dur': 120, 'dist': 330, 'stops': ['XZH', 'NJH']},
        {'code': 'G7123', 'type': '高铁', 'start': 'XZH', 'end': 'NJH', 'dep': '10:00', 'arr': '12:00', 'dur': 120, 'dist': 330, 'stops': ['XZH', 'NJH']},
        {'code': 'G7125', 'type': '高铁', 'start': 'XZH', 'end': 'NJH', 'dep': '13:00', 'arr': '15:00', 'dur': 120, 'dist': 330, 'stops': ['XZH', 'NJH']},
        {'code': 'G7127', 'type': '高铁', 'start': 'XZH', 'end': 'NJH', 'dep': '15:00', 'arr': '17:00', 'dur': 120, 'dist': 330, 'stops': ['XZH', 'NJH']},
        {'code': 'G7122', 'type': '高铁', 'start': 'NJH', 'end': 'XZH', 'dep': '08:30', 'arr': '10:30', 'dur': 120, 'dist': 330, 'stops': ['NJH', 'XZH']},
        {'code': 'G7124', 'type': '高铁', 'start': 'NJH', 'end': 'XZH', 'dep': '11:00', 'arr': '13:00', 'dur': 120, 'dist': 330, 'stops': ['NJH', 'XZH']},
    ])
    
    # 徐州东相关
    train_data.extend([
        {'code': 'G7131', 'type': '高铁', 'start': 'XZN', 'end': 'SHA', 'dep': '08:00', 'arr': '11:30', 'dur': 210, 'dist': 650, 'stops': ['XZN', 'NJH', 'SHA']},
        {'code': 'G7133', 'type': '高铁', 'start': 'XZN', 'end': 'SHA', 'dep': '10:00', 'arr': '13:30', 'dur': 210, 'dist': 650, 'stops': ['XZN', 'NJH', 'SHA']},
        {'code': 'G7135', 'type': '高铁', 'start': 'XZN', 'end': 'SHA', 'dep': '13:00', 'arr': '16:30', 'dur': 210, 'dist': 650, 'stops': ['XZN', 'NJH', 'SHA']},
        {'code': 'G7137', 'type': '高铁', 'start': 'XZN', 'end': 'SHA', 'dep': '15:00', 'arr': '18:30', 'dur': 210, 'dist': 650, 'stops': ['XZN', 'NJH', 'SHA']},
        {'code': 'G7141', 'type': '高铁', 'start': 'SHA', 'end': 'XZN', 'dep': '08:00', 'arr': '11:00', 'dur': 180, 'dist': 650, 'stops': ['SHA', 'NJH', 'XZN']},
        {'code': 'G7143', 'type': '高铁', 'start': 'SHA', 'end': 'XZN', 'dep': '10:00', 'arr': '13:00', 'dur': 180, 'dist': 650, 'stops': ['SHA', 'NJH', 'XZN']},
        {'code': 'G7145', 'type': '高铁', 'start': 'SHA', 'end': 'XZN', 'dep': '13:00', 'arr': '16:00', 'dur': 180, 'dist': 650, 'stops': ['SHA', 'NJH', 'XZN']},
        {'code': 'G7147', 'type': '高铁', 'start': 'SHA', 'end': 'XZN', 'dep': '15:00', 'arr': '18:00', 'dur': 180, 'dist': 650, 'stops': ['SHA', 'NJH', 'XZN']},
    ])
    
    # 宁波-温州
    train_data.extend([
        {'code': 'G7651', 'type': '高铁', 'start': 'NBH', 'end': 'WZH', 'dep': '08:00', 'arr': '09:30', 'dur': 90, 'dist': 280, 'stops': ['NBH', 'WZH']},
        {'code': 'G7653', 'type': '高铁', 'start': 'NBH', 'end': 'WZH', 'dep': '10:00', 'arr': '11:30', 'dur': 90, 'dist': 280, 'stops': ['NBH', 'WZH']},
        {'code': 'G7655', 'type': '高铁', 'start': 'NBH', 'end': 'WZH', 'dep': '13:00', 'arr': '14:30', 'dur': 90, 'dist': 280, 'stops': ['NBH', 'WZH']},
        {'code': 'G7652', 'type': '高铁', 'start': 'WZH', 'end': 'NBH', 'dep': '09:00', 'arr': '10:30', 'dur': 90, 'dist': 280, 'stops': ['WZH', 'NBH']},
        {'code': 'G7654', 'type': '高铁', 'start': 'WZH', 'end': 'NBH', 'dep': '11:00', 'arr': '12:30', 'dur': 90, 'dist': 280, 'stops': ['WZH', 'NBH']},
    ])
    
    # 上海-温州
    train_data.extend([
        {'code': 'G7541', 'type': '高铁', 'start': 'SHA', 'end': 'WZH', 'dep': '08:00', 'arr': '12:00', 'dur': 240, 'dist': 650, 'stops': ['SHA', 'HZN', 'WZH']},
        {'code': 'G7543', 'type': '高铁', 'start': 'SHA', 'end': 'WZH', 'dep': '10:00', 'arr': '14:00', 'dur': 240, 'dist': 650, 'stops': ['SHA', 'HZN', 'WZH']},
        {'code': 'G7545', 'type': '高铁', 'start': 'SHA', 'end': 'WZH', 'dep': '13:00', 'arr': '17:00', 'dur': 240, 'dist': 650, 'stops': ['SHA', 'HZN', 'WZH']},
        {'code': 'G7542', 'type': '高铁', 'start': 'WZH', 'end': 'SHA', 'dep': '08:30', 'arr': '12:30', 'dur': 240, 'dist': 650, 'stops': ['WZH', 'HZN', 'SHA']},
        {'code': 'G7544', 'type': '高铁', 'start': 'WZH', 'end': 'SHA', 'dep': '11:00', 'arr': '15:00', 'dur': 240, 'dist': 650, 'stops': ['WZH', 'HZN', 'SHA']},
    ])
    
    # 合肥-上海
    train_data.extend([
        {'code': 'G7171', 'type': '高铁', 'start': 'HFN', 'end': 'SHA', 'dep': '08:00', 'arr': '11:00', 'dur': 180, 'dist': 450, 'stops': ['HFN', 'NJH', 'SHA']},
        {'code': 'G7173', 'type': '高铁', 'start': 'HFN', 'end': 'SHA', 'dep': '10:00', 'arr': '13:00', 'dur': 180, 'dist': 450, 'stops': ['HFN', 'NJH', 'SHA']},
        {'code': 'G7175', 'type': '高铁', 'start': 'HFN', 'end': 'SHA', 'dep': '13:00', 'arr': '16:00', 'dur': 180, 'dist': 450, 'stops': ['HFN', 'NJH', 'SHA']},
        {'code': 'G7177', 'type': '高铁', 'start': 'HFN', 'end': 'SHA', 'dep': '15:00', 'arr': '18:00', 'dur': 180, 'dist': 450, 'stops': ['HFN', 'NJH', 'SHA']},
        {'code': 'G7172', 'type': '高铁', 'start': 'SHA', 'end': 'HFN', 'dep': '08:30', 'arr': '11:30', 'dur': 180, 'dist': 450, 'stops': ['SHA', 'NJH', 'HFN']},
        {'code': 'G7174', 'type': '高铁', 'start': 'SHA', 'end': 'HFN', 'dep': '11:00', 'arr': '14:00', 'dur': 180, 'dist': 450, 'stops': ['SHA', 'NJH', 'HFN']},
    ])
    
    # 武汉方向
    train_data.extend([
        {'code': 'G1711', 'type': '高铁', 'start': 'SHH', 'end': 'WHN', 'dep': '08:00', 'arr': '12:30', 'dur': 270, 'dist': 800, 'stops': ['SHH', 'NJH', 'WHN']},
        {'code': 'G1713', 'type': '高铁', 'start': 'SHH', 'end': 'WHN', 'dep': '10:00', 'arr': '14:30', 'dur': 270, 'dist': 800, 'stops': ['SHH', 'NJH', 'WHN']},
        {'code': 'G1715', 'type': '高铁', 'start': 'SHH', 'end': 'WHN', 'dep': '13:00', 'arr': '17:30', 'dur': 270, 'dist': 800, 'stops': ['SHH', 'NJH', 'WHN']},
        {'code': 'G1712', 'type': '高铁', 'start': 'WHN', 'end': 'SHH', 'dep': '08:30', 'arr': '13:00', 'dur': 270, 'dist': 800, 'stops': ['WHN', 'NJH', 'SHH']},
        {'code': 'G1714', 'type': '高铁', 'start': 'WHN', 'end': 'SHH', 'dep': '12:00', 'arr': '16:30', 'dur': 270, 'dist': 800, 'stops': ['WHN', 'NJH', 'SHH']},
    ])
    
    # 郑州方向
    train_data.extend([
        {'code': 'G1801', 'type': '高铁', 'start': 'SHH', 'end': 'ZZD', 'dep': '08:00', 'arr': '13:30', 'dur': 330, 'dist': 1000, 'stops': ['SHH', 'NJH', 'XZN', 'ZZD']},
        {'code': 'G1803', 'type': '高铁', 'start': 'SHH', 'end': 'ZZD', 'dep': '10:00', 'arr': '15:30', 'dur': 330, 'dist': 1000, 'stops': ['SHH', 'NJH', 'XZN', 'ZZD']},
        {'code': 'G1805', 'type': '高铁', 'start': 'SHH', 'end': 'ZZD', 'dep': '13:00', 'arr': '18:30', 'dur': 330, 'dist': 1000, 'stops': ['SHH', 'NJH', 'XZN', 'ZZD']},
        {'code': 'G1802', 'type': '高铁', 'start': 'ZZD', 'end': 'SHH', 'dep': '08:00', 'arr': '13:30', 'dur': 330, 'dist': 1000, 'stops': ['ZZD', 'XZN', 'NJH', 'SHH']},
        {'code': 'G1804', 'type': '高铁', 'start': 'ZZD', 'end': 'SHH', 'dep': '11:00', 'arr': '16:30', 'dur': 330, 'dist': 1000, 'stops': ['ZZD', 'XZN', 'NJH', 'SHH']},
    ])
    
    # 台州方向
    train_data.extend([
        {'code': 'G7541', 'type': '高铁', 'start': 'SHA', 'end': 'TZU', 'dep': '09:00', 'arr': '13:00', 'dur': 240, 'dist': 450, 'stops': ['SHA', 'HZN', 'TZU']},
        {'code': 'G7543', 'type': '高铁', 'start': 'SHA', 'end': 'TZU', 'dep': '11:00', 'arr': '15:00', 'dur': 240, 'dist': 450, 'stops': ['SHA', 'HZN', 'TZU']},
        {'code': 'G7545', 'type': '高铁', 'start': 'SHA', 'end': 'TZU', 'dep': '14:00', 'arr': '18:00', 'dur': 240, 'dist': 450, 'stops': ['SHA', 'HZN', 'TZU']},
        {'code': 'G7542', 'type': '高铁', 'start': 'TZU', 'end': 'SHA', 'dep': '09:30', 'arr': '13:30', 'dur': 240, 'dist': 450, 'stops': ['TZU', 'HZN', 'SHA']},
        {'code': 'G7544', 'type': '高铁', 'start': 'TZU', 'end': 'SHA', 'dep': '12:00', 'arr': '16:00', 'dur': 240, 'dist': 450, 'stops': ['TZU', 'HZN', 'SHA']},
    ])
    
    # 创建车次和停站
    station_map = {s.station_code: s.id for s in Station.query.all()}
    
    trains_created = []
    train_codes_seen = set()  # 用于检测重复车次代码
    
    for td in train_data:
        # 检查车次代码是否重复
        if td['code'] in train_codes_seen:
            print(f"跳过重复车次代码: {td['code']}")
            continue
        train_codes_seen.add(td['code'])
        
        start_id = station_map.get(td['start'])
        end_id = station_map.get(td['end'])
        
        if not start_id or not end_id:
            print(f"跳过站点不存在: {td['start']} -> {td['end']}")
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
    stop_count = 0
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
        
        # 获取中间停站信息
        stops = td.get('stops', [train.train_code])  # 使用td中存储的stops
        # 重新查找td信息
        td_info = next((x for x in train_data if x['code'] == train.train_code), None)
        if td_info:
            stops = td_info.get('stops', [train.train_code])
        
        # 计算每个区间的距离
        num_stops = len(stops)
        distance_per_stop = train.total_distance / (num_stops - 1) if num_stops > 1 else train.total_distance
        
        # 解析时间（简化处理：按平均速度分配时间）
        dep_parts = train.departure_time.split(':')
        dep_minutes = int(dep_parts[0]) * 60 + int(dep_parts[1])
        arr_parts = train.arrival_time.split(':')
        arr_minutes = int(arr_parts[0]) * 60 + int(arr_parts[1])
        if arr_minutes < dep_minutes:
            arr_minutes += 24 * 60
        total_minutes = arr_minutes - dep_minutes
        minutes_per_stop = total_minutes / (num_stops - 1) if num_stops > 1 else total_minutes
        
        for i, stop_code in enumerate(stops):
            stop_station_id = station_map.get(stop_code)
            if not stop_station_id:
                continue  # 跳过不存在的站点
            
            current_time = int(dep_minutes + i * minutes_per_stop)
            current_hour = current_time // 60
            current_min = current_time % 60
            current_time_str = f"{current_hour:02d}:{current_min:02d}"
            
            distance = int(i * distance_per_stop)
            
            stop = TrainStop(
                train_id=train.id,
                station_id=stop_station_id,
                stop_order=i + 1,
                arrival_time=current_time_str if i > 0 else None,
                departure_time=current_time_str if i == 0 else None,
                stop_duration=2 if 0 < i < num_stops - 1 else 0,
                distance_from_start=distance
            )
            db.session.add(stop)
            stop_count += 1
    
    db.session.commit()
    
    # 创建公告
    announcements = [
        Announcement(
            title='关于2026年春运期间增开列车的公告',
            content='为满足2026年春运期间旅客出行需求，我局将在春节期间增开多趟临时旅客列车，具体车次及开行时间请关注车站公告。',
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
    
    # 打印统计信息
    print(f"\n========== 数据库初始化统计 ==========")
    print(f"席别种类: {len(SeatType.query.all())}")
    print(f"站点总数: {len(stations)}")
    print(f"车次总数: {len(trains_created)}")
    print(f"停站总数: {stop_count}")
    print(f"公告总数: {len(Announcement.query.all())}")
    print(f"========================================\n")
