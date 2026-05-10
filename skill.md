# Blog Scraper

通用博客文章抓取器 - 自动识别、提取、保存博客文章为 Markdown 格式。

## 功能

自动抓取个人博客文章，支持：
- 通用博客平台识别
- 智能文章列表发现
- 自动内容提取
- Markdown 格式转换
- AI 摘要生成（可选）
- 增量抓取
- 定期任务

## 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `url` | 博客网址 | 必需 |
| `-o` | 输出目录 | `./blog_articles` |
| `-n` | 抓取数量限制 | 全部 |
| `-h` | 无头模式 | true |
| `--no-headless` | 显示浏览器 | - |
| `--ai` | 启用 AI 摘要 | false |
| `--reset` | 重置进度 | false |

## 使用示例

```bash
# 基础抓取
/blog-scraper https://example.com

# 指定输出目录
/blog-scraper https://blog.example.com -o ~/my_blog

# 抓取前 10 篇
/blog-scraper https://example.com -n 10

# 启用 AI 摘要
/blog-scraper https://example.com --ai

# 显示浏览器（调试用）
/blog-scraper https://example.com --no-headless

# 重置进度重新抓取
/blog-scraper https://example.com --reset
```

## 支持的博客类型

自动识别并支持：
- 通用个人博客（article 标签）
- WordPress 博客
- Hugo/Jekyll 静态博客
- Medium 博客
- Substack 新闻通讯
- Ghost 博客
- 自定义博客（通过配置）

## 配置

创建 `~/.claude/skills/blog-scraper/config.json`:

```json
{
  "default_output_dir": "./blog_articles",
  "min_delay": 2,
  "max_delay": 5,
  "max_retries": 3,
  "anthropic_api_key": null,
  "openai_api_key": null,
  "custom_selectors": {
    "example.com": {
      "article_list": "div.post",
      "article_link": "a.title",
      "article_content": "article.content"
    }
  }
}
```

## 输出结构

```
blog_articles/
├── articles/           # 文章 Markdown
├── summaries/          # AI 摘要
├── images/             # 下载的图片
├── metadata.json       # 文章元数据
├── progress.json       # 抓取进度
└── scraper.log         # 运行日志
```

## 定期抓取

```bash
# 添加到 crontab
0 2 * * * /blog-scraper https://yourblog.com >> ~/blog_scraper.log 2>&1
```

## 依赖

- Python 3.14+
- selenium
- html2text
- requests
- beautifulsoup4

安装：
```bash
pip3 install --break-system-packages selenium html2text requests beautifulsoup4
```

## 注意事项

- 遵守 robots.txt
- 设置合理的抓取延迟
- 避免高峰时段抓取
- 仅用于个人学习
