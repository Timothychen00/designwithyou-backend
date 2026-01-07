# gunicorn.conf.py  — 避免 /dev 權限問題，用 /tmp（macOS）
bind = "0.0.0.0:8000"
workers = 8                # 先保守，等壓測再調
threads = 3
worker_class = "uvicorn.workers.UvicornWorker"
worker_tmp_dir = "/tmp"    # 關鍵：不要用 /dev
timeout = 60
graceful_timeout = 30
max_requests = 10000
max_requests_jitter = 1000
forwarded_allow_ips = "*"