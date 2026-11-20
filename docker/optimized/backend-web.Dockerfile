# Backend-Web 服务 Dockerfile（优化版）
# 基于通用基础镜像 xianyu-base（已预装 chromium/playwright/patchright 及系统依赖），
# 仅安装服务自身依赖，构建速度大幅提升
# 使用: docker compose -f docker-compose-optimized.yml up -d --build

ARG BASE_IMAGE=xianyu-base:latest
FROM ${BASE_IMAGE}

WORKDIR /app

# 复制项目源码
COPY common /app/common
COPY backend-web /app/backend-web
COPY launcher /app/launcher

# 从pyproject.toml提取并安装依赖
# （playwright/patchright 已在基础镜像中安装，pip 检测已满足会自动跳过，chromium revision 保持一致）
RUN python -c "\
import tomllib; \
deps = tomllib.load(open('/app/backend-web/pyproject.toml','rb')).get('project',{}).get('dependencies',[]); \
open('/tmp/requirements.txt','w').write('\n'.join(deps))" && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# 创建日志目录
RUN mkdir -p /app/backend-web/logs /app/static/uploads

# 暴露端口
EXPOSE 8089

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV TZ=Asia/Shanghai

# 启动服务
CMD ["python", "backend-web/main.py"]
