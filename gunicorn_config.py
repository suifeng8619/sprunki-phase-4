# Gunicorn配置文件
bind = "0.0.0.0:9028"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
threads = 2
max_requests = 1000
max_requests_jitter = 50

# 日志配置
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"

# 性能优化
preload_app = True
