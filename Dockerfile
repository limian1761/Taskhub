FROM python:3.11-slim

WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 安装uv
RUN pip install uv

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 安装依赖
RUN uv sync --frozen

# 复制源代码
COPY src/ ./src/
COPY configs/ ./configs/

# 创建必要的目录
RUN mkdir -p /app/data /app/logs

# 暴露端口
EXPOSE 8001
EXPOSE 8000

# 默认启动命令
CMD ["uv", "run", "python", "-m", "src.server", "--transport", "stdio"]