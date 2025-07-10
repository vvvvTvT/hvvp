import json
import random
from datetime import datetime, timedelta
from app import app, db, Request, Result

def generate_requests(n=5):
    methods = ['GET', 'POST', 'PUT', 'DELETE']
    urls = [
        'https://jsonplaceholder.typicode.com/posts',
        'https://jsonplaceholder.typicode.com/comments',
        'https://jsonplaceholder.typicode.com/albums',
        'https://jsonplaceholder.typicode.com/photos',
        'https://jsonplaceholder.typicode.com/todos'
    ]
    for i in range(n):
        req = Request(
            method=methods[i % len(methods)],
            url=urls[i % len(urls)],
            headers=json.dumps({"Content-Type": "application/json"}),
            body='{"test": "data"}' if methods[i % len(methods)] in ['POST', 'PUT'] else None,
            interval=60*(i+1)  # 1分钟, 2分钟, 3分钟...
        )
        db.session.add(req)
    db.session.commit()
    print(f"Inserted {n} requests.")

def generate_results():
    requests_ = Request.query.all()
    now = datetime.utcnow()
    error_statuses = [404, 500, 502]
    for req in requests_:
        # 每个请求插入3条结果，时间递减
        for j in range(3):
            # 30% 几率异常
            if random.random() < 0.3:
                status_code = random.choice(error_statuses)
                response_body = f"Error {status_code} for request {req.id}"
            else:
                status_code = 200
                response_body = f"Response body {j+1} for request {req.id}"
            res = Result(
                request_id=req.id,
                status_code=status_code,
                response_body=response_body,
                timestamp=now - timedelta(minutes=j*5)
            )
            db.session.add(res)
    db.session.commit()
    print(f"Inserted {len(requests_)*3} results.")

if __name__ == '__main__':
    with app.app_context():
        generate_requests()
        generate_results()
