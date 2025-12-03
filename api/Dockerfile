# ChatGPT to Word Converter API Docker Image
# Version: 1.0.0
# Description: Converts ChatGPT HTML exports with KaTeX formulas to Word/PDF documents

FROM python:3.11-slim

# Metadata
LABEL maintainer="ChatGPT2Word Team"
LABEL version="1.0.0"
LABEL description="ChatGPT HTML to Word Converter API"

# 设置工作目录
WORKDIR /app

# 1. 写入中科大 Debian 源（trixie）
RUN set -eux; \
    echo "deb https://mirrors.ustc.edu.cn/debian trixie main contrib non-free non-free-firmware" > /etc/apt/sources.list; \
    echo "deb https://mirrors.ustc.edu.cn/debian trixie-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list; \
    echo "deb https://mirrors.ustc.edu.cn/debian-security trixie-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list

# 创建非 root 用户提高安全性
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 2. 安装系统依赖（pandoc、LaTeX 等）
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 文档转换工具
    pandoc \
    # LaTeX 支持（PDF 生成和数学公式）
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    # 系统工具
    xzdec \
    curl \
    ca-certificates \
    fontconfig \
    # 清理 apt 缓存减小镜像大小
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/*

# 3. 使用项目内的 .deb 安装 wkhtmltopdf（离线安装 + 补依赖）
#   依赖：libjpeg62-turbo（在 trixie 仍有），libssl1.1（从 bullseye snapshot 拉取）
COPY wkhtmltox_0.12.6.1-2.bullseye_amd64.deb /tmp/wkhtml.deb

RUN set -eux; \
    # 增加 bullseye snapshot 源，用于安装 libssl1.1
    echo "deb http://snapshot.debian.org/archive/debian/20220620T211058Z bullseye main" > /etc/apt/sources.list.d/bullseye-snapshot.list; \
    apt-get update; \
    # 安装 wkhtmltox 需要的依赖
    apt-get install -y --no-install-recommends \
        libjpeg62-turbo \
        libssl1.1; \
    # 安装 wkhtmltox（wkhtmltopdf）
    dpkg -i /tmp/wkhtml.deb || apt-get -f install -y; \
    # 确保在 PATH 中可以找到（一般安装到 /usr/local/bin）
    if [ -x /usr/local/bin/wkhtmltopdf ]; then ln -sf /usr/local/bin/wkhtmltopdf /usr/bin/wkhtmltopdf; fi; \
    if [ -x /usr/local/bin/wkhtmltoimage ]; then ln -sf /usr/local/bin/wkhtmltoimage /usr/bin/wkhtmltoimage; fi; \
    rm -f /tmp/wkhtml.deb; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/* /tmp/*

# 4. 复制依赖文件（利用 Docker 层缓存）
COPY requirements.txt .

# 5. 升级 pip 并安装 Python 依赖（使用清华源）
RUN pip install --no-cache-dir --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 6. 复制应用代码
COPY main.py .

# 将应用目录所有权给非 root 用户
RUN chown -R appuser:appuser /app

# 切换到非 root 用户
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查 - 确保服务正常运行
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动应用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
