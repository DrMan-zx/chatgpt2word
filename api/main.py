"""
ChatGPT HTML to Word Converter API

Main FastAPI application entry point.
Provides a single endpoint /convert that accepts ChatGPT HTML and returns a .docx file.
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import re
import subprocess
from typing import Optional
from pathlib import Path
from bs4 import BeautifulSoup

app = FastAPI(
    title="ChatGPT to Word Converter",
    description="Convert ChatGPT HTML exports with KaTeX formulas to editable Word documents",
    version="1.0.0"
)

# --- CORS 配置（开发时使用，生产环境请限制为可信域） ---
origins = [
    "https://chatgpt.com",
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # 开发调试可临时改为 ["*"]，生产请列出具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
MAX_HTML_SIZE = 50 * 1024 * 1024  # 50MB
PANDOC_TIMEOUT = 30  # seconds


def pdf_preprocess_html(html_content: str) -> str:
    """
    预处理 ChatGPT HTML，移除不必要的标记以提高转换质量。

    Args:
        html_content: 原始 HTML 内容

    Returns:
        清理后的 HTML 内容
    """
    soup = BeautifulSoup(html_content, 'lxml')

    # 1. 移除所有 data-* 属性（ChatGPT特有）
    for tag in soup.find_all():
        attrs_to_remove = [attr for attr in tag.attrs if attr.startswith('data-')]
        for attr in attrs_to_remove:
            del tag[attr]

    # 2. 清理嵌套的复杂容器
    for div in soup.find_all("div"):
        if len(div.attrs) == 1 and 'class' in div.attrs:
            if not div.find() and not div.get_text().strip():
                div.decompose()

    # 3. 返回处理后的 HTML，保留原始 emoji
    result = str(soup)
    return result

def preprocess_html(html_content: str) -> str:
    """
    预处理 ChatGPT HTML，移除不必要的标记以提高转换质量。

    Args:
        html_content: 原始 HTML 内容

    Returns:
        清理后的 HTML 内容
    """
    soup = BeautifulSoup(html_content, 'lxml')

    # 1. 移除所有 data-* 属性（ChatGPT特有）
    for tag in soup.find_all():
        attrs_to_remove = [attr for attr in tag.attrs if attr.startswith('data-')]
        for attr in attrs_to_remove:
            del tag[attr]

    # 2. 优化数学公式处理 - 仅在检测到公式时处理
    # Check if there are any KaTeX annotations before processing
    if soup.find_all("annotation", {"encoding": "application/x-tex"}):
        for ann in soup.find_all("annotation", {"encoding": "application/x-tex"}):
            latex = ann.get_text().strip()
            katex_span = ann.find_parent("span", class_="katex")
            if katex_span:
                # 检查是否为行内或块级公式
                parent_classes = katex_span.parent.get('class', []) if katex_span.parent else []
                katex_classes = katex_span.get('class', [])

                # 判断是否为行内公式
                is_inline = ('inline' in parent_classes or
                            'katex-inline' in katex_classes or
                            'katex' in katex_classes and 'katex-display' not in katex_classes)

                # 策略 1: 创建适合 Pandoc 处理的 LaTeX 格式
                # 使用 $ 表示行内公式，\\[ \\] 表示块级公式
                if is_inline:
                    latex_formatted = f"${latex}$"
                else:
                    latex_formatted = f"\\[{latex}\\]"

                # 创建包含 LaTeX 的 span，让 Pandoc 识别为数学公式
                new_span = soup.new_tag("span")
                new_span.string = latex_formatted

                # 替换原始 KaTeX 元素
                katex_span.replace_with(new_span)

    # 3. 完全重构表格 - 彻底清理所有容器
    # 查找所有表格并用纯净版本替换
    tables = soup.find_all("table")
    for table in tables:
        # 创建新表格
        new_table = soup.new_tag("table")
        # 复制表格内容，保持原有结构
        for row in table.find_all("tr"):
            new_row = soup.new_tag("tr")
            for cell in row.find_all(["th", "td"]):
                new_cell = soup.new_tag(cell.name)
                # 保留文本和数学公式
                new_cell.string = cell.get_text()
                new_row.append(new_cell)
            new_table.append(new_row)
        # 直接替换原表格（忽略所有父容器）
        table.replace_with(new_table)

    # 4. 清理所有表格周围的装饰性容器
    for div in soup.find_all("div"):
        if div.find("table") and not div.get_text().strip():
            # 如果 div 只包含表格且没有文本内容，替换为表格
            table = div.find("table")
            if table:
                div.replace_with(table)

    # 5. 简化代码块
    pre_tags = soup.find_all("pre")
    for pre_tag in pre_tags:
        # 查找实际的代码内容
        code_div = pre_tag.find("div", class_="overflow-y-auto")
        if code_div:
            code_tag = code_div.find("code")
            if code_tag:
                code_text = code_tag.get_text()
                new_pre = soup.new_tag("pre")
                new_code = soup.new_tag("code")
                new_code.string = code_text
                new_pre.append(new_code)
                pre_tag.replace_with(new_pre)

    # 5. 清理嵌套的复杂容器
    for div in soup.find_all("div"):
        if len(div.attrs) == 1 and 'class' in div.attrs:
            if not div.find() and not div.get_text().strip():
                div.decompose()

    # 6. 返回处理后的 HTML，保留原始 emoji
    result = str(soup)
    return result

def validate_html(html: str) -> bool:
    """
    Validate HTML content (no longer requires KaTeX formulas).

    Args:
        html: HTML content to validate

    Returns:
        True if valid, raises HTTPException if invalid

    Raises:
        HTTPException: 400 if invalid HTML
    """
    if not html or not isinstance(html, str):
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_request", "message": "HTML content is required"}
        )

    # Basic validation - check if it contains HTML tags
    if not ('<' in html and '>' in html):
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_html", "message": "Invalid HTML format"}
        )

    return True  # Accept any HTML content now

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to remove invalid characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    if not filename:
        return "converted"

    # Remove invalid characters: \ / : * ? " < > | and control characters
    sanitized = re.sub(r'[\\/:*?"<>|]', '_', filename)

    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')

    # Limit length
    if len(sanitized) > 100:
        sanitized = sanitized[:100]

    return sanitized or "converted"

def convert_html_to_docx(html_content: str) -> bytes:
    """
    Convert HTML with KaTeX formulas to a .docx file.
    Uses direct HTML → DOCX conversion for better table formatting.

    Args:
        html_content: ChatGPT HTML containing KaTeX formulas

    Returns:
        Binary .docx file content

    Raises:
        HTTPException: 500 if conversion fails
    """
    try:
        # Stage 1: Preprocess HTML
        cleaned_html = preprocess_html(html_content)

        # Stage 2: HTML → DOCX (direct conversion)
        with tempfile.TemporaryDirectory() as tmpdir:
            html_file = Path(tmpdir) / "temp.html"
            docx_file = Path(tmpdir) / "temp.docx"

            # Write cleaned HTML to temp file
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(cleaned_html)

            # Convert HTML to DOCX with LaTeX math support
            cmd = [
                "pandoc",
                str(html_file),
                "-f", "html+tex_math_dollars+tex_math_double_backslash",  # 支持 $ 和 \\[\\] 公式
                "-t", "docx",
                "-o", str(docx_file)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=PANDOC_TIMEOUT,
                check=False
            )

            if result.returncode != 0:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "html_to_docx_failed",
                        "message": f"Failed to convert HTML to DOCX: {result.stderr}"
                    }
                )

            # Read and return the docx file
            with open(docx_file, "rb") as f:
                return f.read()

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "conversion_timeout",
                "message": "Conversion timed out"
            }
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "conversion_failed",
                "message": f"Conversion failed: {str(e)}"
            }
        )

def convert_html_to_pdf(html_content: str) -> bytes:
    """
    使用 wkhtmltopdf + MathJax2，将 HTML 转为 PDF。
    - 用 wrap_with_mathjax_template 包装 HTML，注入 MathJax2 CDN。
    - wkhtmltopdf 等待 window.status == 'onloadready' 再开始渲染。
    """
    try:
        # 1. 如需，你也可以先做自己的清洗
        # cleaned_html = preprocess_html(html_content)
        cleaned_html = html_content

        # 2. 包装成完整 HTML（含 MathJax2 脚本）
        full_html = wrap_with_mathjax_template(cleaned_html)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            html_file = tmpdir_path / "temp_mathjax.html"
            pdf_file = tmpdir_path / "temp_mathjax.pdf"

            # 写入完整 HTML
            with open(html_file, "w", encoding="utf-8", errors="ignore") as f:
                f.write(full_html)

            # 3. 直接调用 wkhtmltopdf，而不是再通过 pandoc
            cmd_pdf = [
                "wkhtmltopdf",
                "--enable-local-file-access",
                "--javascript-delay", "2000",        # 兜底延时，给 MathJax 一些时间
                "--window-status", "onloadready",    # 等待 window.status = 'onloadready'
                str(html_file),
                str(pdf_file),
            ]

            result_pdf = subprocess.run(
                cmd_pdf,
                capture_output=True,
                text=True,
                timeout=PANDOC_TIMEOUT,
                check=False
            )

            if pdf_file.exists() and pdf_file.stat().st_size > 0:
                with open(pdf_file, "rb") as f:
                    return f.read()

            if result_pdf.returncode != 0:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "html_to_pdf_failed",
                        "message": (
                            "Failed to convert HTML to PDF with wkhtmltopdf. "
                            f"stderr: {result_pdf.stderr}"
                        )
                    }
                )

            raise HTTPException(
                status_code=500,
                detail={
                    "error": "empty_pdf_output",
                    "message": "PDF file is empty after conversion."
                }
            )

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "conversion_timeout",
                "message": "Conversion timed out"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "conversion_failed",
                "message": f"Conversion failed: {str(e)}"
            }
        )

def wrap_with_mathjax_template(inner_html: str) -> str:
    """
    将内容包装为完整 HTML 文档，并引入 MathJax2 CDN。
    使用 window.status='onloadready' 配合 wkhtmltopdf 的 --window-status 选项。
    """
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>MathJax PDF</title>
  <style>
    /* 全局默认字体大小：接近 Word 小四（约 12pt ≈ 30px） */
    html, body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans",
                   "Liberation Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol",
                   "Noto Color Emoji";
      font-size: 30px;      /* 小四号 */
      line-height: 1.6;
      margin: 30px;
    }}

    p {{
      font-size: 30px;
      margin: 0 0 0.8em 0;
    }}

    h1 {{ font-size: 34px; }}
    h2 {{ font-size: 30px; }}
    h3 {{ font-size: 26px; }}

    table {{
      border-collapse: collapse;
      width: 100%;
      font-size: 30px;
    }}

    th, td {{
      border: 1px solid #ccc;
      padding: 4px 8px;
    }}

    code, pre {{
      font-family: Consolas, "Courier New", monospace;
      font-size: 24px;  /* 代码稍微小一点，看着更像编辑器效果 */
    }}
  </style>
</head>
<body>
  <div id="wrapper">
    {inner_html}
  </div>

  <script type="text/javascript">
    var el = document.createElement("script"); // 不要使用const等es6语法
    el.setAttribute("id", "MathJax-script");
    el.src = "https://cdn.staticfile.org/mathjax/2.7.1/MathJax.js?config=TeX-AMS-MML_HTMLorMML";
    document.body.appendChild(el);

    if (el.readyState) {{
      // IE
      el.onreadystatechange = function () {{
        if (el.readyState === "complete" || el.readyState === "loaded") {{
          el.onreadystatechange = null;
          mathjaxConfig();
        }}
      }};
    }} else {{
      // 非 IE
      el.onload = function () {{
        mathjaxConfig();
      }};
    }}

    function mathjaxConfig() {{
      if (window.MathJax) {{
        window.MathJax.Hub.Config({{
          extensions: ["tex2jax.js"],
          jax: ["input/TeX", "output/HTML-CSS"],
          tex2jax: {{
            inlineMath: [["\\\\(", "\\\\)"]],
            displayMath: [
              ["$$", "$$"],
              ["\\\\[", "\\\\]"],
            ],
            processEscapes: true,
          }},
          "HTML-CSS": {{
            availableFonts: ["TeX"],
            preferredFont: "TeX",
            minScaleAdjust: 100,
          }},
        }});

        window.MathJax.Hub.Queue([
          "Typeset",
          MathJax.Hub,
          document.getElementById("wrapper"),
          function () {{
            // MathJax 把公式都渲染完成后，通知 wkhtmltopdf
            window.status = "onloadready";
          }},
        ]);
      }}
    }}
  </script>
</body>
</html>
"""

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "ChatGPT to Word Converter",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/convert")
async def convert_html(
    html: str = Form(...),
    filename: Optional[str] = Form(None),
    output_format: str = Form("docx")
):
    """
    Convert ChatGPT HTML with KaTeX formulas to Word or PDF document.

    - **html**: Complete ChatGPT HTML content (required)
    - **filename**: Custom filename without extension (optional)
    - **output_format**: Output format - "docx" or "pdf" (default: "docx")

    Returns:
        Binary document file with appropriate content-disposition header
    """
    # Validate output format
    if output_format not in ["docx", "pdf"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_format",
                "message": "Output format must be 'docx' or 'pdf'"
            }
        )

    # Validate HTML size
    html_size = len(html.encode('utf-8'))
    if html_size > MAX_HTML_SIZE:
        raise HTTPException(
            status_code=413,
            detail={
                "error": "too_large",
                "message": f"HTML size ({html_size} bytes) exceeds limit ({MAX_HTML_SIZE} bytes)"
            }
        )

    # Validate HTML contains formulas
    validate_html(html)

    # Sanitize filename
    sanitized_filename = sanitize_filename(filename)

    try:
        # Convert HTML to requested format
        if output_format == "docx":
            content = convert_html_to_docx(html)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            file_ext = "docx"
        else:  # pdf
            content = convert_html_to_pdf(html)
            media_type = "application/pdf"
            file_ext = "pdf"

        # Return streaming response
        return StreamingResponse(
            iter([content]),
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{sanitized_filename}.{file_ext}"'
            }
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation, timeout, etc.)
        raise
    except Exception as e:
        # Catch-all for unexpected errors
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": f"Unexpected error: {str(e)}"
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
