# 上海局铁路一体化集成平台 v1.1.0

铁路客票系统，参考12306设计，包含旅客端购票系统和运营管理系统。

## 系统架构

- **客票系统（旅客端）**：路径 `/` - 面向旅客的购票、查询、订单管理
- **运营管理系统（管理端）**：路径 `/ops/` - 面向铁路管理人员的票务、车次、站点管理
- **闸机检票系统（预留）**：路径 `/gate/` - 未来扩展

## 技术栈

- 后端：Python Flask
- 数据库：SQLite（文件型）
- 前端：Bootstrap 5 + Jinja2 模板
- 图表：Chart.js

## 快速启动

```bash
cd shanghai-railway-platform
pip install -r requirements.txt
python app.py
```

访问地址：
- 客票系统：http://localhost:5000/
- 运营管理系统：http://localhost:5000/ops/

## 演示账号

| 账号 | 密码 | 类型 | 说明 |
|------|------|------|------|
| admin | admin123 | 管理员 | 运营系统完整权限 |
| demo | demo123 | 旅客 | 旅客购票权限 |
| staff | staff123 | 职工 | 运营系统部分权限 |

## 功能模块

### 旅客端

- 车票查询（按出发站、到达站、日期查询）
- 车次时刻表
- 订单管理（预订、支付、退票）
- 个人中心（信息管理、密码修改）

### 运营管理系统

- 仪表盘（售票统计、营收分析）
- 车次管理（增删改查、停站设置、席别管理）
- 站点管理（增删改查）
- 票务管理（售票记录查询）
- 退票管理（退款审核）
- 用户管理（启用/禁用）
- 公告管理（发布/编辑公告）
- 列车调整（停运、晚点通知）
- 操作日志

## 数据库结构

系统包含12张核心数据表：
- users - 用户表
- stations - 站点表
- trains - 车次表
- train_stops - 停站表
- seat_types - 席别表
- train_seats - 车次席别表
- tickets - 订单表
- payments - 支付记录表
- refunds - 退票记录表
- announcements - 公告表
- train_schedule_changes - 列车调整表
- operation_logs - 操作日志表

## 种子数据

- 约100个管辖站点（上海、江苏、浙江、安徽）
- 约150趟车次（覆盖G/D/K/T/Z/C各类型）
- 8种席别（商务座、一等座、二等座等）
- 演示用户和公告数据

## 项目结构

```
shanghai-railway-platform/
├── app.py                    # 统一入口
├── config.py                 # 配置
├── models.py                 # 数据模型
├── seed_data.py              # 种子数据
├── requirements.txt          # 依赖
├── client/                   # 旅客端
│   ├── routes.py
│   ├── auth.py
│   └── templates/client/
├── ops/                      # 运营系统
│   ├── routes.py
│   ├── auth.py
│   └── templates/ops/
└── static/
    ├── css/
    └── js/
```

## Replit 部署

项目已配置 Replit 兼容：
- 单端口 5000
- 自动依赖安装
- 自动数据库初始化

在 Replit 中直接点击 Run 即可运行。

## 注意事项

1. 数据库文件 `railway.db` 会在首次运行时自动创建
2. 所有演示账号仅用于测试，不要用于生产环境
3. 支付功能为模拟实现，不涉及真实支付

## 版本历史

- v1.1.0 - 完善车次和站点数据，增加图表统计
- v1.0.0 - 初始版本，包含基础功能

## 许可证

内部使用项目
