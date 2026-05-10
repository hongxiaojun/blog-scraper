# Blog Scraper Skill

通用博客文章抓取器 - 自动识别、提取、保存博客文章为 Markdown 格式。

## 安装

```bash
# 安装依赖
pip3 install --break-system-packages selenium html2text beautifulsoup4

# 或使用安装脚本
bash ~/.claude/skills/blog-scraper/install.sh
```

## 使用

### 基础用法

```bash
# 抓取博客（全部文章）
/blog-scraper https://example.com

# 抓取指定数量
/blog-scraper https://example.com -n 10

# 指定输出目录
/blog-scraper https://example.com -o ~/my_blog

# 启用 AI 摘要
/blog-scraper https://example.com --ai

# 显示浏览器（调试）
/blog-scraper https://example.com --no-headless

# 重置进度重新抓取
/blog-scraper https://example.com --reset
```

### 配置 AI 摘要

编辑 `~/.claude/skills/blog-scraper/config.json`:

```json
{
  "enable_ai": true,
  "anthropic_api_key": "sk-ant-...",
  "openai_api_key": "sk-..."
}
```

或使用环境变量：

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
```

## 支持的博客平台

自动识别并支持：

- ✅ WordPress 博客
- ✅ Ghost 博客
- ✅ Medium 博客
- ✅ Substack 新闻通讯
- ✅ Hugo/Jekyll 静态博客
- ✅ 通用博客（智能识别）

## 自定义配置

### 添加自定义博客选择器

编辑 `config.json`:

```json
{
  "custom_selectors": {
    "mysite.com": {
      "article_list": ["div.post"],
      "article_link": "a.title",
      "article_content": ["div.content"],
      "title": ["h1.post-title"]
    }
  }
}
```

### 调整抓取参数

```json
{
  "min_delay": 2,
  "max_delay": 5,
  "max_retries": 3
}
```

## 输出结构

```
blog_articles/
├── articles/           # Markdown 文章
├── summaries/          # AI 摘要
├── images/             # 图片
├── progress.json       # 抓取进度
└── metadata.json       # 元数据
```

## 定期抓取

添加到 crontab：

```bash
crontab -e

# 每天凌晨 3 点抓取
0 3 * * * /blog-scraper https://yourblog.com -o ~/my_blog >> ~/blog_scraper.log 2>&1
```

## 故障排除

### 依赖缺失

```bash
pip3 install --break-system-packages selenium html2text beautifulsoup4
```

### Chrome 未找到

```bash
# macOS
brew install --cask google-chrome

# Linux
sudo apt-get install chromium-browser
```

### 抓取失败

1. 使用 `--no-headless` 查看浏览器行为
2. 增加 `min_delay` 和 `max_delay`
3. 检查网站是否需要登录

## 注意事项

- ⚠️ 遵守 robots.txt
- ⚠️ 设置合理的抓取延迟
- ⚠️ 避免高峰时段抓取
- ⚠️ 仅用于个人学习
- ⚠️ 尊重版权

## 示例

```bash
# 抓取 Paul Graham 的文章
/blog-scraper https://paulgraham.com -o ~/pg_articles -n 50

# 抓取个人博客
/blog-scraper https://myblog.com --ai

# 调试模式
/blog-scraper https://example.com --no-headless -n 1
```

## 技术细节

- **浏览器**: Chrome + Selenium
- **内容提取**: 智能选择器 + BeautifulSoup
- **Markdown 转换**: html2text
- **平台识别**: 自动检测博客类型
- **增量抓取**: 进度文件跟踪

## 许可

仅供个人学习使用。请遵守目标网站的使用条款。

---

**版本**: 1.0.0
**更新**: 2026-05-10
