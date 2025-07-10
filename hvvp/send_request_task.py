import sys
import json
import requests
from datetime import datetime
from app import create_app, db, Request, Result

app = create_app()
app.app_context().push()

def send_and_save(request_id):
    req = Request.query.get(request_id)
    if not req:
        print(f"Request ID {request_id} 不存在")
        return

    try:
        headers = json.loads(req.headers) if req.headers else {}
    except Exception:
        headers = {}

    try:
        if req.method.upper() == 'GET':
            resp = requests.get(req.url, headers=headers, timeout=10)
        elif req.method.upper() == 'POST':
            resp = requests.post(req.url, headers=headers, data=req.body, timeout=10)
        elif req.method.upper() == 'PUT':
            resp = requests.put(req.url, headers=headers, data=req.body, timeout=10)
        elif req.method.upper() == 'DELETE':
            resp = requests.delete(req.url, headers=headers, data=req.body, timeout=10)
        elif req.method.upper() == 'PATCH':
            resp = requests.patch(req.url, headers=headers, data=req.body, timeout=10)
        else:
            print(f"不支持的请求方法: {req.method}")
            return
    except Exception as e:
        # 请求异常，写入错误状态
        result = Result(
            request_id=request_id,
            status_code=0,
            response_body=str(e),
            timestamp=datetime.utcnow()
        )
        db.session.add(result)
        db.session.commit()
        print(f"请求异常: {e}")
        return

    # 保存结果
    result = Result(
        request_id=request_id,
        status_code=resp.status_code,
        response_body=resp.text,
        timestamp=datetime.utcnow()
    )
    db.session.add(result)
    db.session.commit()
    print(f"请求 {request_id} 执行完成，状态码: {resp.status_code}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("请传入Request ID参数")
        sys.exit(1)
    send_and_save(int(sys.argv[1]))
