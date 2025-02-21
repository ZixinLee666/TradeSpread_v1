"""
my2pdf.py - 将指定Python文件转换为保留中文的PDF
用法: python my2pdf.py 文件名（不含.py扩展名）
示例: python my2pdf.py demo
"""

from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import os
import sys

# 配置参数
FONT_NAME = "NotoSansSC"  # 使用的字体标识
FONT_REL_PATH = "fonts/NotoSansSC-Regular.ttf"  # 字体相对路径
FONT_DOWNLOAD_URL = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansSC-Regular.otf"


def check_font():
    """检查字体文件是否存在"""
    font_path = os.path.join(os.path.dirname(__file__), FONT_REL_PATH)
    if not os.path.exists(font_path):
        print(f"错误: 字体文件未找到，请执行以下操作：")
        print(f"1. 从 {FONT_DOWNLOAD_URL} 下载字体")
        print(f"2. 创建 fonts 文件夹")
        print(f"3. 将字体文件重命名为 {FONT_REL_PATH} 并放入fonts文件夹")
        print("目录结构应如下：")
        print("├── my2pdf.py")
        print("└── fonts/")
        print("    └── NotoSansSC-Regular.ttf")
        sys.exit(1)
    return font_path


def my2pdf(filename):
    """主转换函数"""
    # 输入输出路径
    input_path = f"{filename}.py"
    output_path = f"{filename}.pdf"

    # 检查字体
    font_path = check_font()

    # 注册字体
    try:
        pdfmetrics.registerFont(TTFont(FONT_NAME, font_path))
    except Exception as e:
        print(f"字体注册失败: {str(e)}")
        sys.exit(1)

    # 读取代码内容
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
    except Exception as e:
        print(f"文件读取失败: {str(e)}")
        sys.exit(1)

    # 配置样式
    styles = getSampleStyleSheet()
    style = styles["Normal"]
    style.fontName = FONT_NAME
    style.fontSize = 10
    style.leading = 15  # 行距
    style.wordWrap = 'CJK'  # 中文换行

    # 生成PDF
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=30,
        rightMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    # 转换换行符并保留空格
    formatted_content = code_content.replace(' ', '&nbsp;').replace('\n', '<br/>')
    story = [Paragraph(formatted_content, style)]

    try:
        doc.build(story)
        print(f"成功生成: {output_path}")
    except Exception as e:
        print(f"PDF生成失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    my2pdf(sys.argv[1])