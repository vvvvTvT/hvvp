from flask import Flask, render_template, request, jsonify
from models import db, Request, Result
import json
from scheduler import start_scheduler
import requests as req
from config import BT_PANEL_URL, BT_API_KEY, BT_API_USER, PYTHON_PATH, SCRIPT_DIR, LOG_DIR
import os
import requests as http_requests
import urllib.parse
import pytz
from datetime import datetime

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/hvvp?charset=utf8mb4'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

app = create_app()

@app.before_request
def init_app():
    db.create_all()
    # 启动定时任务线程
    start_scheduler(app)

@app.route('/')
def index():
    return render_template('index.html', active_page='index')

@app.route('/set')
def set_page():
    return render_template('set.html', active_page='set')

# API: 新增请求
@app.route('/api/request', methods=['POST'])
def create_request():
    data = request.json
    if not data:
        return jsonify(success=False, error='请求数据为空'), 400

    method = data.get('method')
    url_ = data.get('url')
    headers = data.get('headers', {})
    body = data.get('body', None)
    interval = data.get('interval')

    if not all([method, url_, interval]):
        return jsonify(success=False, error='缺少必要字段'), 400

    try:
        interval = int(interval)
        if interval < 1:
            raise ValueError()
    except Exception:
        return jsonify(success=False, error='间隔时间必须是正整数'), 400

    # 保存请求
    new_req = Request(
        method=method.upper(),
        url=url_,
        headers=json.dumps(headers),
        body=body,
        interval=interval
    )
    db.session.add(new_req)
    db.session.commit()

    # 生成执行脚本路径和日志路径
    script_path = os.path.join(SCRIPT_DIR, f'run_request_{new_req.id}.py')
    log_path = os.path.join(LOG_DIR, f'hvvp_request_{new_req.id}.log')

    # 生成执行脚本内容，动态获取上海时区时间写入数据库
    script_content = f'''\
import json
import requests
from datetime import datetime
from app import create_app, db
from models import Request, Result

def main():
    app = create_app()
    with app.app_context():
        req = Request.query.get({new_req.id})
        if not req:
            print("请求ID {new_req.id} 不存在")
            return

        try:
            headers = json.loads(req.headers) if req.headers else {{}}
        except Exception:
            headers = {{}}

        body = req.body if req.body else None

        try:
            response = requests.request(
                method=req.method,
                url=req.url,
                headers=headers,
                data=body,
                timeout=30
            )
            status_code = response.status_code
            response_body = response.text
        except Exception as e:
            status_code = 0
            response_body = str(e)

        # 写入结果
        result = Result(
            request_id={new_req.id},
            status_code=status_code,
            response_body=response_body,
            timestamp=datetime.utcnow()
        )
        db.session.add(result)

        # 更新请求最新状态和时间
        req.last_status = status_code
        req.last_time = datetime.utcnow()

        db.session.commit()
        print(f"请求 {new_req.id} 执行完成，状态码 {{status_code}}")

if __name__ == '__main__':
    main()
'''

    # 保存脚本文件
    os.makedirs(SCRIPT_DIR, exist_ok=True)
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    os.chmod(script_path, 0o755)

    # 确保日志目录存在
    os.makedirs(LOG_DIR, exist_ok=True)

    # 生成cron表达式，支持每 interval 分钟执行一次
    cron_schedule = f"*/{interval} * * * *"
    cron_cmd = f"{PYTHON_PATH} {script_path} >> {log_path} 2>&1"

    # 调用宝塔API添加定时任务（如果需要取消注释）
    # try:
    #     result = add_cron_task(
    #         name=f'HVVP Request {new_req.id}',
    #         shell_cmd=cron_cmd,
    #         schedule=cron_schedule,
    #         user=''  # 宝塔API里传空字符串即可
    #     )
    #     if not (result.get('status') is True or str(result.get('status')).lower() == 'true'):
    #         return jsonify(success=False, error='添加宝塔定时任务失败: ' + result.get('msg', '未知错误')), 500
    # except Exception as e:
    #     return jsonify(success=False, error='调用宝塔API异常: ' + str(e)), 500

    return jsonify(success=True, id=new_req.id)


def add_cron_task(name, shell_cmd, schedule, user=''):
    """
    通过宝塔面板API添加定时任务
    :param name: 任务名称
    :param shell_cmd: 执行的shell命令
    :param schedule: cron表达式，如 */5 * * * *
    :param user: 运行用户，浏览器请求中为空字符串即可
    :return: 返回API响应json
    """
    url = f'{BT_PANEL_URL}/crontab?action=AddCrontab'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'x-http-token': BT_API_KEY,
        'Accept': 'application/json, text/plain, */*',
        'Origin': BT_PANEL_URL,
        'Referer': f'{BT_PANEL_URL}/crontab/task',
        'User-Agent': 'Mozilla/5.0',
    }

    cron_parts = schedule.strip().split()
    if len(cron_parts) == 5:
        minute, hour, day, month, week = cron_parts
        type_ = 'day'
        week_ = '1'
        hour_ = '1'
        minute_ = '30'

        if minute.startswith('*/'):
            minute_ = minute[2:]
        else:
            minute_ = minute

        if hour != '*':
            hour_ = hour
    else:
        type_ = 'day'
        week_ = '1'
        hour_ = '1'
        minute_ = '30'

    data = {
        'name': name,
        'sType': 'toShell',
        'sBody': shell_cmd,
        'sName': '',
        'backupTo': '',
        'save': '',
        'urladdress': '',
        'save_local': '0',
        'notice': '0',
        'notice_channel': '',
        'datab_name': '',
        'tables_name': '',
        'keyword': '',
        'flock': '1',
        'version': '',
        'user': user,
        'stop_site': '0',
        'type': type_,
        'week': week_,
        'hour': hour_,
        'minute': minute_,
        'where1': '1',
        'timeSet': '1',
        'timeType': 'sday',
    }

    encoded_data = urllib.parse.urlencode(data)
    print('请求URL:', url)
    print('请求头:', headers)
    print('请求数据:', encoded_data)

    resp = http_requests.post(url, headers=headers, data=encoded_data, timeout=10, verify=False)
    print('返回状态码:', resp.status_code)
    print('返回内容:', resp.text)
    resp.raise_for_status()
    return resp.json()


# API: 获取所有请求及最新响应
@app.route('/api/requests', methods=['GET'])
def get_requests():
    requests_ = Request.query.all()
    result_list = []
    for req_ in requests_:
        last_result = Result.query.filter_by(request_id=req_.id).order_by(Result.timestamp.desc()).first()
        result_list.append({
            'id': req_.id,
            'method': req_.method,
            'url': req_.url,
            'interval': req_.interval,
            'last_status': last_result.status_code if last_result else None,
            'last_response': last_result.response_body if last_result else '',
            'last_time': last_result.timestamp.strftime('%Y-%m-%d %H:%M:%S') if last_result else ''
        })
    return jsonify(result_list)


# API: 获取某请求所有响应历史
@app.route('/api/results/<int:request_id>', methods=['GET'])
def get_results(request_id):
    results = Result.query.filter_by(request_id=request_id).order_by(Result.timestamp.desc()).all()
    result_list = [{
        'status_code': r.status_code,
        'response_body': r.response_body,
        'timestamp': r.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    } for r in results]
    return jsonify(result_list)


@app.route('/send_request', methods=['POST'])
def send_request():
    data = request.json
    method = data.get('method', 'GET').upper()
    url_ = data.get('url', '')
    headers = data.get('headers', {})
    body = data.get('body', None)

    try:
        if method in ['GET', 'DELETE']:
            response = req.request(method, url_, headers=headers)
        else:
            content_type = headers.get('Content-Type', '').lower()
            if 'application/json' in content_type and body:
                try:
                    json_body = json.loads(body) if isinstance(body, str) else body
                    response = req.request(method, url_, headers=headers, json=json_body)
                except Exception:
                    response = req.request(method, url_, headers=headers, data=body)
            else:
                response = req.request(method, url_, headers=headers, data=body)

        try:
            response_body = response.json()
        except Exception:
            response_body = response.text

        return jsonify({
            'success': True,
            'status': response.status_code,
            'headers': dict(response.headers),
            'body': response_body
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    start_scheduler(app)
    app.run(port=5001, debug=True)
