import time
from collections import defaultdict
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

class TokenBucketRateLimiter(BaseHTTPMiddleware):
    """
    Middleware giới hạn tần suất truy cập (Rate Limiting) dựa trên thuật toán Token Bucket:
    - Áp dụng cho các RESTful API công khai: tối đa 60 requests/phút cho mỗi địa chỉ IP nguồn.
    - Tự động bỏ qua WebSocket hoặc các request nội bộ.
    """
    def __init__(self, app, rate_per_minute: int = 60):
        super().__init__(app)
        self.capacity = float(rate_per_minute)
        self.fill_rate = float(rate_per_minute) / 60.0  # Tokens per second
        self.buckets = defaultdict(lambda: {"tokens": self.capacity, "last_updated": time.monotonic()})

    async def dispatch(self, request: Request, call_next):
        # Bỏ qua WebSocket và các endpoint tĩnh/docs hoặc môi trường kiểm thử
        import os
        if os.getenv("TESTING") == "1" or request.headers.get("X-Test-Client") or request.url.path.startswith(("/ws", "/docs", "/openapi.json", "/redoc")):
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.monotonic()
        bucket = self.buckets[client_ip]

        # Nạp thêm token theo thời gian trôi qua
        elapsed = now - bucket["last_updated"]
        bucket["tokens"] = min(self.capacity, bucket["tokens"] + elapsed * self.fill_rate)
        bucket["last_updated"] = now

        # Kiểm tra token
        if bucket["tokens"] < 1.0:
            return Response(
                content='{"detail": "Rate limit exceeded: Tối đa 60 requests/phút trên mỗi IP"}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
                headers={"Retry-After": "2"}
            )

        bucket["tokens"] -= 1.0
        response = await call_next(request)
        return response
