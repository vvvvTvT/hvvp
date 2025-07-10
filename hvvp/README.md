# HVVP - HTTP请求定时监控平台

本项目是一个基于 Flask 的 HTTP 请求定时执行与监控平台，支持用户自定义请求（GET/POST等），定时执行请求，并将响应结果保存到数据库，方便查看历史和状态。

---

## 主要功能

- 提交自定义 HTTP 请求（支持方法、URL、请求头、请求体、执行间隔）
- 自动生成定时执行脚本，通过宝塔面板 API 添加定时任务（待完善）
- 定时执行请求，保存响应状态码、响应体及执行时间
- 提供接口查询所有请求及其最新状态
- 提供接口查询某个请求的全部历史响应记录
- 支持通过接口即时发送请求并返回响应，方便调试
- 时间统一以UTC时区存储

---

## 技术栈

- Python 3.x
- Flask
- SQLAlchemy + MySQL (数据库)
- requests
- pytz（时区处理）
- 宝塔面板 API（用于添加定时任务）
- 计划任务通过动态生成 Python 脚本执行

---

## 环境配置

1. 安装依赖

```bash
pip install flask sqlalchemy pymysql requests pytz
```

2. 配置数据库

创建 MySQL 数据库（建议9.0.1版本），导入项目目录中hvvp.sql，并修改 `app.py` 中的数据库连接 URI：

```
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username
:password@localhost/hvvp?charset=utf8mb4'
```

3. 配置宝塔面板相关参数（如果需要自动添加定时任务）

在 `config.py` 中配置：

```
BT_PANEL_URL = 'http://宝塔面板地址'
BT_API_KEY = '你的宝塔API密钥'
BT_API_USER = '你的宝塔用户名'
PYTHON_PATH = '/usr/bin/python3'  # Python解释器路径
SCRIPT_DIR = '/path/to/scripts'   # 脚本保存目录
LOG_DIR = '/path/to/logs'         # 日志保存目录
```

---

## 运行项目

```
python app.py
```

默认监听 `5001` 端口，访问：

* 首页：`http://localhost:5001/`
* 请求列表：`GET /api/requests`
* 新增请求：`POST /api/request`
* 获取请求历史结果：`GET /api/results/<request_id>`
* 立即发送请求接口：`POST /send_request`

---

## API示例

### 新增请求

```
POST /api/request
Content-Type: application/json

{
  "method": "POST",
  "url": "http://example.com/api",
  "headers": {"Content-Type": "application/json"},
  "body": "{\"key\":\"value\"}",
  "interval": 5
}
```

返回：

```
{
  "success": true,
  "id": 1
}
```

### 查询所有请求及最新响应

```
GET /api/requests
```

返回：

```
[
  {
    "id": 1,
    "method": "POST",
    "url": "http://example.com/api",
    "interval": 5,
    "last_status": 200,
    "last_response": "...",
    "last_time": "2024-06-01 15:30:00"
  },
  ...
]
```

### 查询某请求所有响应历史

```
GET /api/results/1
```

返回：

```
[
  {
    "status_code": 200,
    "response_body": "...",
    "timestamp": "2024-06-01 15:30:00"
  },
  ...
]
```

### 立即发送请求（调试用）

```
POST /send_request
Content-Type: application/json

{
  "method": "GET",
  "url": "http://example.com/api/test",
  "headers": {},
  "body": null
}
```

返回：

```
{
  "success": true,
  "status": 200,
  "headers": {...},
  "body": "响应内容"
}
```

---

## 注意事项

* 定时任务脚本会动态生成于 `SCRIPT_DIR` 目录，日志写入 `LOG_DIR`。请确保这两个目录存在且有写权限。
* 时间统一以UTC时区存储。
* 如果不使用宝塔面板自动添加定时任务功能，可以注释掉相关代码，手动添加定时任务（默认注释）。
* 数据库表结构请参考 `models.py`，确保字段支持时间存储。

---

## 目录结构示例

```
├── app.py
├── config.py
├── models.py
├── scheduler.py
├── scripts/           # 动态生成的定时任务脚本目录
├── logs/              # 执行日志目录
├── templates/
│   ├── index.html
│   └── set.html
└── README.md
```

---

## Todo

* 添加请求修改、删除功能；
* 添加时区修改功能；
* 添加批量导入请求功能；
* 添加历史请求清理功能；
* 优化前端组件展示；
* 优化定时请求算法，目前疑似有bug导致频繁发送请求；

## 许可证

MIT License

---

感谢使用，如有问题与优化建议欢迎提Issue！