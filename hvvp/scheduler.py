import threading
import time
import json
import requests
from models import db, Request, Result
from datetime import datetime
from flask import current_app

def task_worker(app, request_obj):
    while True:
        try:
            headers = json.loads(request_obj.headers or '{}')
            body = request_obj.body or None
            method = request_obj.method.upper()

            if method in ['GET', 'DELETE']:
                resp = requests.request(method=method, url=request_obj.url, headers=headers)
            else:
                content_type = headers.get('Content-Type', '').lower()
                if 'application/json' in content_type and body:
                    try:
                        json_body = json.loads(body)
                        resp = requests.request(method=method, url=request_obj.url, headers=headers, json=json_body)
                    except json.JSONDecodeError:
                        resp = requests.request(method=method, url=request_obj.url, headers=headers, data=body)
                else:
                    resp = requests.request(method=method, url=request_obj.url, headers=headers, data=body)

            # 显式使用 app.app_context()
            with app.app_context():
                result = Result(
                    request_id=request_obj.id,
                    status_code=resp.status_code,
                    response_body=resp.text,
                    timestamp=datetime.utcnow()
                )
                db.session.add(result)
                db.session.commit()
                print(f"[{datetime.utcnow()}] 请求ID {request_obj.id} 执行成功，状态码 {resp.status_code}")

        except Exception as e:
            print(f"[{datetime.utcnow()}] 请求ID {request_obj.id} 执行失败: {e}")

        time.sleep(request_obj.interval * 60)


def start_scheduler(app):
    with app.app_context():
        requests_ = Request.query.all()
        for req in requests_:
            t = threading.Thread(target=task_worker, args=(app, req), daemon=True)
            t.start()
            print(f"启动请求ID {req.id} 的定时任务，间隔 {req.interval} 分钟")
