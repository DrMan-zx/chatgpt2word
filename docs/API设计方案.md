# ChatGPT HTML 转 Word API 设计方案

## 设计目标

**核心原则**：插件与后端彻底解耦，插件只需适配一次，后续无论后端如何演进（同步→异步→分布式→微服务），插件都无需更新。

## 接口设计（对插件稳定）

### 基本信息
- **接口路径**：`POST /convert`
- **内容类型**：`multipart/form-data`
- **字符编码**：UTF-8

### 请求格式
```
POST /convert
Content-Type: multipart/form-data

Form Fields:
  - html: (required, string) 完整的 ChatGPT HTML 内容
  - filename: (optional, string) 自定义文件名（不含扩展名）
  - output_format: (optional, string) 输出格式："docx" 或 "pdf"（默认："docx"）

Example Request:
  html: "<!DOCTYPE html>...</html>"
  filename: "第3章_数学公式整理"
  output_format: "pdf"
```

### 成功响应
```
HTTP/1.1 200 OK

# 当 output_format="docx" 时：
Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document
Content-Disposition: attachment; filename="{filename}.docx"
[Binary Word Document Stream]

# 当 output_format="pdf" 时：
Content-Type: application/pdf
Content-Disposition: attachment; filename="{filename}.pdf"
[Binary PDF Document Stream]
```

### 健康检查端点
```
GET /
响应:
{
  "service": "ChatGPT to Word Converter",
  "version": "1.0.0",
  "status": "running"
}

GET /health
响应:
{
  "status": "healthy"
}
```

### 核心特性更新
- ✅ **已实现 Emoji 支持**：保留原始 Unicode emoji，支持现代 Word 显示
- ✅ **优化数学公式处理**：将 KaTeX 转换为标准 LaTeX 格式，提高兼容性
- ✅ **智能表格重构**：清理 ChatGPT 特有的装饰性容器，确保表格正确显示
- ✅ **代码块优化**：简化复杂嵌套结构，保持代码可读性
- ✅ **多格式支持**：同时支持 DOCX 和 PDF 输出

### 当前实现状态
- ✅ **阶段一实现完成**：简单同步处理，支持基础功能
- ✅ **核心功能验证**：HTML 预理、数学公式转换、文档生成
- ✅ **错误处理**：完整的错误代码和用户友好的错误信息

### 错误响应
```
HTTP/1.1 4xx/5xx
Content-Type: application/json

{
  "error": "ERROR_CODE",
  "message": "人类可读的错误描述"
}

Error Codes:
  - 400 - "invalid_request"     - 缺少必要的参数
  - 400 - "invalid_format"      - 无效的输出格式（output_format 不是 "docx" 或 "pdf"）
  - 413 - "too_large"           - HTML 内容超过大小限制
  - 422 - "no_formulas"         - 未检测到数学公式
  - 500 - "conversion_failed"   - Pandoc 转换失败
  - 500 - "conversion_timeout"  - 转换超时（超过 30 秒）
  - 429 - "rate_limited"        - 请求过于频繁
```

### 核心特性
- ✅ **单一接口**：插件只需要一个 POST 请求
- ✅ **同步体验**：前端始终是"发送请求→等待→接收文件"的流程
- ✅ **错误统一**：所有错误都返回 JSON 格式，便于插件处理
- ✅ **文件命名**：前端可自定义文件名，提升用户体验

---

## 后端演进路线（对后端灵活）

### ✅ 阶段一：简单同步（已实现）
**当前状态**：已实现并部署
**适用场景**：小流量（<5 并发），验证可行性

**已实现的核心功能**：
```python
@app.post("/convert")
async def convert_html(
    html: str = Form(...),
    filename: Optional[str] = Form(None),
    output_format: str = Form("docx")
):
    """当前实现：包含完整预处理和错误处理"""
    # 1. 参数验证和大小限制
    # 2. HTML 内容验证（检查 KaTeX 公式）
    # 3. HTML 预处理（清理 KaTeX、优化表格、处理代码块）
    # 4. Pandoc 转换（支持 DOCX 和 PDF）
    # 5. 错误处理和超时控制
```

**技术栈**：
- FastAPI 1.0.0 + uvicorn
- BeautifulSoup4 + lxml（HTML 解析）
- Pandoc 3.8+（文档转换）
- 完整的错误处理机制

**优势**：
- ✅ 架构简单，易于调试和维护
- ✅ 完整的 HTML 预处理，优化 ChatGPT 特有格式
- ✅ 支持 Emoji 和数学公式处理
- ✅ 零外部依赖（除 Pandoc）

**限制**：
- 一次只能处理一个请求
- 响应时间 = 转换时间（平均 3-5 秒）

**下一步优化方向**：
- 添加进程池支持并发处理
- 实现结果缓存
- 添加监控和日志

---

### 阶段二：进程池（优化）
**适用场景**：中等流量（5-20 并发）
```python
@app.post("/convert")
def convert(request: ConvertRequest):
    """使用进程池并行处理"""
    with ThreadPoolExecutor(max_workers=CPU_CORES) as executor:
        future = executor.submit(run_pandoc, request.html)
        docx_bytes = future.result(timeout=30)
    return Response(docx_bytes, media_type=WORD_MIME_TYPE)
```

**优势**：
- 支持多并发
- 利用多核 CPU
- 接口完全不变

**参数配置**：
- `max_workers`：建议设为 CPU 核心数
- `timeout`：防止单个任务阻塞（建议 30 秒）

**容量估算**：
- 4 核 CPU：同时处理 4 个转换任务
- 平均转换时间 5 秒：每小时处理 ~300 个请求
- 建议负载：20 并发用户以内

---

### 阶段三：任务队列（扩展）
**适用场景**：大流量（>20 并发），需要后台处理
```python
@app.post("/convert")
def convert(request: ConvertRequest):
    """内部使用队列，但对前端保持同步体验"""
    # 负载较轻：直接处理
    if get_queue_length() < 5:
        docx_bytes = run_pandoc_directly(request.html)
    else：
        # 负载较重：放入队列
        task = conversion_task.delay(request.html)
        docx_bytes = task.get(timeout=30)

    return Response(docx_bytes, media_type=WORD_MIME_TYPE)
```

**技术栈**：
- **队列**：Celery + Redis
- **超时**：30 秒（可配置）
- **降级**：负载高时自动切换到队列

**优势**：
- 无缝扩展能力
- 稳定处理高并发
- 失败任务可重试

**监控指标**：
- 队列长度（`queue_length`）
- 平均等待时间（`avg_wait_time`）
- 任务成功率（`success_rate`）

---

### 阶段四：分布式微服务（大规模）
**适用场景**：超高流量（>100 并发），企业级
```python
@app.post("/convert")
def convert(request: ConvertRequest):
    """调用分布式转换服务"""
    docx_bytes = conversion_service.convert(
        html=request.html,
        timeout=30,
        priority="normal"
    )
    return Response(docx_bytes, media_type=WORD_MIME_TYPE)
```

**架构组件**：
- **API Gateway**：统一入口，路由分发
- **Service Discovery**：服务注册与发现
- **Load Balancer**：负载均衡
- **Conversion Cluster**：转换服务集群
- **Result Cache**：结果缓存（Redis）
- **Metrics**：监控与告警

**技术栈**：
- 服务注册：Consul / Eureka
- 负载均衡：Nginx / HAProxy
- 缓存：Redis Cluster
- 监控：Prometheus + Grafana

---

## 动态负载策略

### 智能路由
```python
def smart_convert(html: str) -> bytes:
    """根据当前负载自动选择转换策略"""
    current_load = get_system_load()

    if current_load < 0.5:  # 低负载
        return direct_conversion(html)

    elif current_load < 0.8:  # 中等负载
        return pooled_conversion(html)

    else:  # 高负载
        return queued_conversion(html)
```

### 降级策略
```
正常模式（负载 < 50%）
  ↓
警告模式（负载 50-80%）：启动更多 workers
  ↓
降级模式（负载 > 80%）：启用队列 + 限流
  ↓
紧急模式（负载 > 95%）：只处理 VIP 用户
```

---

## 当前技术架构

### 已实现的核心模块
```python
api/
├── main.py                   # ✅ FastAPI 应用入口（完整实现）
├── requirements.txt          # ✅ 依赖管理
└── Dockerfile              # ✅ 容器化部署

# 当前已实现的功能模块：
main.py 包含以下核心组件：
- preprocess_html()          # ✅ HTML 预处理（KaTeX、表格、代码块）
- validate_html()            # ✅ HTML 验证（检查 KaTeX 公式）
- convert_html_to_docx()     # ✅ DOCX 转换
- convert_html_to_pdf()      # ✅ PDF 转换
- sanitize_filename()        # ✅ 文件名清理
- 完整的错误处理和超时机制
```

### 当前依赖配置
```python
# requirements.txt（已实现）
fastapi==0.104.1
uvicorn[standard]==0.24.0
beautifulsoup4==4.12.2
lxml==4.9.3
python-multipart==0.0.6
pathlib  # 文件路径处理
tempfile  # 临时文件管理
subprocess  # Pandoc 调用
```

### 已优化的处理流程
1. **HTML 预处理**：
   - ✅ 移除 ChatGPT 特有的 data-* 属性
   - ✅ KaTeX 公式转换为标准 LaTeX 格式
   - ✅ 表格结构优化和容器清理
   - ✅ 代码块简化
   - ✅ 保留原始 Emoji 字符

2. **Pandoc 转换配置**：
   - ✅ 使用 `html+tex_math_dollars+tex_math_double_backslash` 格式
   - ✅ 支持多种 PDF 引擎（WeasyPrint, pdfLaTeX, XeLaTeX）
   - ✅ 30 秒超时保护
   - ✅ 详细的错误信息返回

### 部署配置
```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MAX_WORKERS=4
      - QUEUE_ENABLED=false
      - RATE_LIMIT=10/minute
    volumes:
      - ./logs:/app/logs

  # 高并发时启用
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery-worker:
    build: .
    command: celery -A app worker --loglevel=info
    environment:
      - QUEUE_ENABLED=true
    depends_on:
      - redis
```

---

## 安全与限制

### 输入限制
```python
# 文件大小限制
MAX_HTML_SIZE = 50 * 1024 * 1024  # 50MB

# 频率限制
RATE_LIMIT = {
    "anonymous": "10/minute",
    "registered": "100/minute",
    "premium": "1000/minute"
}

# 内容验证
def validate_html(html: str) -> bool:
    # 检查是否包含 KaTeX 内容
    has_katex = "<annotation encoding=\"application/x-tex\">" in html

    # 检查是否包含有效公式
    if not has_katex:
        raise ValidationError("no_formulas")

    # 检查 HTML 完整性
    if not html.strip().startswith("<"):
        raise ValidationError("invalid_request")

    return True
```

### 错误处理
```python
# 处理 Word 转换错误
try:
    docx_bytes = run_pandoc(html, format="docx")
except subprocess.TimeoutExpired:
    raise HTTPException(500, "conversion_timeout")
except Exception as e:
    logger.error(f"Pandoc conversion failed: {e}")
    raise HTTPException(500, "conversion_failed")

# 处理 PDF 转换错误（需要 LaTeX）
try:
    pdf_bytes = run_pandoc(html, format="pdf", pdf_engine="xelatex")
except subprocess.CalledProcessError as e:
    # PDF 转换失败，检查 LaTeX 错误日志
    if "xelatex" in str(e) or "LaTeX" in str(e):
        raise HTTPException(500, {
            "error": "pdf_generation_failed",
            "message": "PDF engine (LaTeX) not available or configuration error"
        })
    else:
        raise HTTPException(500, "conversion_failed")
```

---

## 监控与日志

### 关键指标
- **吞吐量**：每秒处理的转换数
- **响应时间**：P50, P95, P99
- **错误率**：各类型错误的百分比
- **资源使用**：CPU、内存、磁盘 I/O
- **队列长度**：（如果使用）

### 日志格式
```json
{
  "timestamp": "2024-11-04T15:45:30Z",
  "request_id": "uuid",
  "user_ip": "192.168.1.1",
  "html_size": 1024000,
  "convert_time": 3.45,
  "status": "success",
  "error_code": null
}
```

---

## 项目状态总结

### ✅ 已完成的核心功能
- ✅ **插件友好接口**：稳定的 POST /convert 接口，插件只需适配一次
- ✅ **完整的 HTML 预处理**：专门优化 ChatGPT 导出格式
- ✅ **数学公式支持**：KaTeX 到 LaTeX 转换，支持多种格式
- ✅ **Emoji 原生支持**：保留原始 Unicode 字符，现代 Word 完美显示
- ✅ **多格式输出**：支持 DOCX 和 PDF 两种格式
- ✅ **完整的错误处理**：详细的错误代码和用户友好信息
- ✅ **容器化部署**：Docker 支持，一键部署

### 🔧 当前技术特点
- **单进程同步处理**：适合小流量场景（<5 并发）
- **平均响应时间**：3-5 秒（取决于内容复杂度）
- **支持内容大小**：最大 50MB HTML 文件
- **核心依赖**：FastAPI + BeautifulSoup + Pandoc

### 📈 性能指标
- **支持格式**：ChatGPT HTML 导出（必须包含 KaTeX 公式）
- **输出质量**：保留表格、代码块、数学公式、Emoji
- **Word 兼容性**：Word 2016+（数学公式），Word 2013（基础功能）

### 🚀 下一步优化计划
```
当前阶段：简单同步（✅ 已实现）
    ↓
下一阶段：进程池并发（支持 20+ 并发）
    ↓
未来阶段：任务队列（高流量处理）
    ↓
扩展阶段：分布式微服务（企业级）
```

### 💡 设计验证
✅ **核心原则验证成功**：
- 接口设计稳定，插件无需更新
- HTML 预理专门针对 ChatGPT 格式优化
- 错误处理完善，用户体验良好
- 架构简单，易于维护和调试

### 🎯 项目价值
- **解决实际问题**：ChatGPT 数学公式导出到 Word 的痛点
- **技术方案成熟**：基于成熟的 Pandoc 和 FastAPI 技术
- **扩展性良好**：为未来性能优化预留了清晰的演进路径
- **用户体验优先**：简单的"发送-接收"流程，无复杂配置

**项目状态：MVP 已完成，可以投入生产使用**
