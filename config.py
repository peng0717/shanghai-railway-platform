import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'shanghai-railway-secret-key-2024'
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'railway.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 运营系统配置
    OPS_PREFIX = '/ops'
    OPS_TITLE = '上海局客票运营管理系统'
    
    # 客票系统配置
    CLIENT_TITLE = '上海局铁路客票系统'
    
    # 分页配置
    ITEMS_PER_PAGE = 20
    TRAIN_ITEMS_PER_PAGE = 15
