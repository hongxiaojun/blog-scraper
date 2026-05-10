#!/bin/bash
# Blog Scraper Skill 安装脚本

set -e

echo "================================================"
echo "  Blog Scraper Skill - 安装"
echo "================================================"
echo ""

# 检查 Python
echo "检查 Python..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3"
    exit 1
fi
echo "✓ Python3: $(python3 --version)"
echo ""

# 检查 Chrome
echo "检查 Chrome..."
if [ -d "/Applications/Google Chrome.app" ] || [ -d "/opt/google/chrome" ]; then
    echo "✓ Chrome 已安装"
else
    echo "⚠️  未找到 Chrome，正在安装..."
    if command -v brew &> /dev/null; then
        brew install --cask google-chrome
    else
        echo "请手动安装 Chrome: https://www.google.com/chrome/"
    fi
fi
echo ""

# 安装 Python 依赖
echo "安装 Python 依赖..."
pip3 install --break-system-packages selenium html2text beautifulsoup4 > /dev/null 2>&1
echo "✓ 依赖已安装"
echo ""

# 检查 skill 文件
SKILL_DIR="$HOME/.claude/skills/blog-scraper"
if [ -d "$SKILL_DIR" ]; then
    echo "✓ Skill 文件已就绪"
    ls -lh "$SKILL_DIR"
else
    echo "错误: Skill 目录不存在"
    exit 1
fi
echo ""

# 测试
echo "测试 Skill..."
if [ -x "$SKILL_DIR/blog-scraper" ]; then
    echo "✓ Skill 脚本可执行"
else
    echo "错误: Skill 脚本不可执行"
    exit 1
fi
echo ""

echo "================================================"
echo "安装完成！"
echo "================================================"
echo ""
echo "使用方法:"
echo "  /blog-scraper https://example.com"
echo ""
echo "查看帮助:"
echo "  /blog-scraper --help"
echo ""
echo "配置文件:"
echo "  ~/.claude/skills/blog-scraper/config.json"
echo ""
