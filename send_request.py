# sendreq.py
import argparse
import requests
import sys


def main():
    parser = argparse.ArgumentParser(description='发送HTTP请求')
    parser.add_argument('-u', '--url', required=True, help='请求的URL')
    parser.add_argument('-H', '--header', action='append', help='请求头，格式为"Key: Value"', default=[])
    parser.add_argument('-d', '--data', help='请求体', default=None)

    args = parser.parse_args()

    # 将header列表转换为字典
    headers = {}
    for h in args.header:
        key, value = h.split(':', 1)
        headers[key.strip()] = value.strip()

    try:
        # 发送GET请求（即使有data，GET请求也不发送body）
        response = requests.get(args.url, headers=headers)
        print(f"状态码: {response.status_code}")
        print("响应体:")
        print(response.text)
    except Exception as e:
        print(f"请求失败: {str(e)}", file=sys.stderr)


if __name__ == '__main__':
    main()
