import requests

# 读取 HTML 文件
with open('1.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

# 发送请求
response = requests.post(
    'http://localhost:8000/convert',
    data={
        'html': html_content,
        'filename': 'test_output',
        'output_format': 'pdf'
    }
)

# 保存 PDF
if response.status_code == 200:
    with open('output.pdf', 'wb') as f:
        f.write(response.content)
    print('✅ PDF 已保存为 output.pdf')
else:
    print(f'❌ 错误: {response.status_code}')
    print(response.json())