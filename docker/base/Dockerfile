# 通用基础镜像 Dockerfile
# 统一安装 chromium（playwright + patchright）、字体等系统依赖，只构建一次；
# backend-web / websocket / scheduler 的 Dockerfile 直接 FROM 本镜像，
# 避免每个镜像构建时重复安装 chromium 导致耗时过长。
# 构建: docker build -f docker/base/Dockerfile -t xianyu-base:latest .

# 基础镜像走 docker.io 官方名（由 buildx 的 buildkitd 镜像加速配置拉取，见流水线 BUILDKIT 配置）
FROM python:3.11-slim

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# 配置国内镜像源
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list 2>/dev/null || true
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装系统依赖（字体为 chromium 渲染中文字符必需）
RUN apt-get update && apt-get install -y curl ca-certificates gcc \
    fonts-dejavu-core fonts-liberation \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 安装 playwright / patchright 并下载 chromium
# patchright 锁定为与 playwright 完全相同的版本 → chromium revision 一致，
# patchright install 检测到浏览器已存在会直接跳过，避免重复下载一份 chromium
# 说明: chromium-headless-shell 是 playwright 官方无头模式必需组件（项目大量使用 headless=True），不可跳过
RUN pip install --no-cache-dir "playwright" \
    && PW_VERSION=$(python -c "import playwright; print(playwright.__version__)") \
    && pip install --no-cache-dir "patchright==${PW_VERSION}" \
    || pip install --no-cache-dir "patchright>=1.61.0" \
    && python -m playwright install --with-deps chromium \
    && python -m patchright install --with-deps chromium

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV TZ=Asia/Shanghai

WORKDIR /app
