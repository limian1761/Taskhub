# 请求Header记录功能

## 概述

Taskhub项目现在支持自动记录所有HTTP请求的Header信息，这对于调试、监控和安全审计非常有用。

## 功能特性

- **自动记录所有请求Header**：包括User-Agent、Content-Type、Accept、Authorization等
- **客户端IP记录**：记录请求来源的IP地址
- **响应状态记录**：记录每个请求的响应状态码
- **JSON格式输出**：便于解析和分析
- **安全性考虑**：Authorization header会被隐藏显示为"***"
- **错误处理**：即使记录失败也不会影响正常请求处理

## 日志文件

系统会生成以下日志文件：

- `logs/taskhub.log` - 主要的应用日志
- `logs/requests.log` - 专门的请求Header日志

## 日志格式示例

```
2024-01-15 10:30:45,123 [INFO] taskhub.request: 请求Header信息: {
  "method": "GET",
  "url": "http://localhost:8000/api/status",
  "client_ip": "127.0.0.1",
  "headers": {
    "host": "localhost:8000",
    "user-agent": "TestClient/1.0",
    "accept": "application/json",
    "authorization": "***"
  },
  "user_agent": "TestClient/1.0",
  "content_type": "unknown",
  "accept": "application/json",
  "authorization": "***"
}

2024-01-15 10:30:45,125 [INFO] taskhub.request: 响应状态: 200 - GET http://localhost:8000/api/status
```

## 配置

### 日志级别

在 `configs/logging.json` 中可以配置日志级别：

```json
{
  "loggers": {
    "taskhub.request": {
      "handlers": ["console", "request_file"],
      "level": "INFO",
      "propagate": false
    }
  }
}
```

### 日志格式

可以自定义日志格式：

```json
{
  "formatters": {
    "request": {
      "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    }
  }
}
```

## 使用方法

### 1. 启动服务器

```bash
# 启动Admin服务器
python src/admin_server.py

# 启动Web服务器
python src/web_server.py

# 启动Taskhub服务器
python src/taskhub/server.py
```

### 2. 发送测试请求

```bash
# 使用curl测试
curl -H "User-Agent: TestClient/1.0" \
     -H "Accept: application/json" \
     -H "Authorization: Bearer test-token" \
     http://localhost:8000/api/status

# 使用Python测试脚本
python test_request_logging.py
```

### 3. 查看日志

```bash
# 查看请求日志
tail -f logs/requests.log

# 查看所有日志
tail -f logs/taskhub.log
```

## 记录的Header信息

系统会记录以下Header信息：

- **method**: HTTP方法 (GET, POST, PUT, DELETE等)
- **url**: 完整的请求URL
- **client_ip**: 客户端IP地址
- **headers**: 所有请求头
- **user_agent**: User-Agent头
- **content_type**: Content-Type头
- **accept**: Accept头
- **authorization**: Authorization头 (隐藏显示)

## 安全考虑

1. **敏感信息保护**：Authorization header会被隐藏显示为"***"
2. **日志文件权限**：确保日志文件有适当的访问权限
3. **日志轮转**：建议配置日志轮转以避免文件过大
4. **生产环境**：在生产环境中可能需要调整日志级别

## 故障排除

### 日志文件不存在

确保 `logs` 目录存在：

```bash
mkdir -p logs
```

### 权限问题

确保应用有写入日志文件的权限：

```bash
chmod 755 logs/
chmod 644 logs/*.log
```

### 日志级别问题

如果看不到请求日志，检查日志级别配置：

```json
{
  "loggers": {
    "taskhub.request": {
      "level": "INFO"
    }
  }
}
```

## 扩展功能

### 自定义Header过滤

可以在中间件中添加自定义的Header过滤逻辑：

```python
# 过滤敏感Header
sensitive_headers = ['authorization', 'cookie', 'x-api-key']
filtered_headers = {k: v for k, v in headers.items() 
                   if k.lower() not in sensitive_headers}
```

### 请求体记录

如果需要记录请求体，可以添加：

```python
# 记录请求体 (仅对特定Content-Type)
if request.headers.get("content-type") == "application/json":
    body = await request.body()
    request_info["body"] = body.decode()
```

### 性能监控

可以添加请求时间记录：

```python
import time

start_time = time.time()
response = await call_next(request)
end_time = time.time()

request_info["duration"] = end_time - start_time
```

## 注意事项

1. **性能影响**：Header记录会轻微影响请求处理性能
2. **存储空间**：大量请求会产生大量日志，注意磁盘空间
3. **隐私合规**：确保符合相关的隐私法规要求
4. **日志管理**：建议实施日志轮转和清理策略 