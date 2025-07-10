class res:
    def __init__(self, req_id, code, result, timestamp):
        self.req_id = req_id
        self.code = code
        self.result = result
        self.timestamp = timestamp

    def __repr__(self):
        return f"{self.req_id} {self.code} {self.result} {self.timestamp}"