#!/usr/bin/env python3
"""
通用博客文章抓取器
支持多种博客平台，智能识别和提取文章内容
"""

import sys
import json
import re
import time
import random
import argparse
import logging
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

try:
    from html2text import HTML2Text
except ImportError:
    HTML2Text = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import openai
except ImportError:
    openai = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BlogPlatform:
    """博客平台识别和配置"""

    # 平台识别规则
    PLATFORMS = {
        'wordpress': {
            'indicators': ['wp-content', 'wordpress', 'wp-includes'],
            'article_list': ['article', 'div.post', 'div.entry'],
            'article_link': 'a[href*="/"]',
            'article_content': ['article', 'div.entry-content', 'div.post-content'],
            'title': ['h1.entry-title', 'h1.post-title', 'h1']
        },
        'ghost': {
            'indicators': ['ghost', 'ghost-script'],
            'article_list': ['article'],
            'article_link': 'a[href*="/"]',
            'article_content': ['article', 'div.post-content'],
            'title': ['h1.post-title', 'h1']
        },
        'medium': {
            'indicators': ['medium.com', 'medium'],
            'article_list': ['article'],
            'article_link': 'a[href*="/"]',
            'article_content': ['article'],
            'title': ['h1']
        },
        'substack': {
            'indicators': ['substack.com', 'substack'],
            'article_list': ['div.post'],
            'article_link': 'a[href*="/p/"]',
            'article_content': ['div.post-content'],
            'title': ['h1.post-title', 'h1']
        },
        'hugo': {
            'indicators': ['hugo', 'themes/'],
            'article_list': ['article', 'div.post', 'div.entry'],
            'article_link': 'a[href*="/posts/"]',
            'article_content': ['article', 'div.content'],
            'title': ['h1']
        },
        'jekyll': {
            'indicators': ['jekyll', '_posts'],
            'article_list': ['article', 'div.post', 'div.entry'],
            'article_link': 'a[href*="/"]',
            'article_content': ['article', 'div.post-content'],
            'title': ['h1']
        },
        'generic': {
            'article_list': ['article', 'div.post', 'div.entry', 'div[class*="post"]', 'div[class*="article"]'],
            'article_link': 'a[href*="/"]',
            'article_content': ['article', 'main', 'div[class*="content"]', 'div[class*="post"]'],
            'title': ['h1', 'title']
        }
    }

    @classmethod
    def identify_platform(cls, url: str, driver) -> str:
        """识别博客平台"""
        try:
            driver.get(url)
            page_source = driver.page_source.lower()

            for platform, config in cls.PLATFORMS.items():
                if platform == 'generic':
                    continue
                for indicator in config.get('indicators', []):
                    if indicator in page_source:
                        logger.info(f"识别平台: {platform}")
                        return platform

            logger.info("使用通用配置")
            return 'generic'

        except Exception as e:
            logger.warning(f"平台识别失败: {e}")
            return 'generic'


class BlogScraper:
    """通用博客抓取器"""

    def __init__(self, url: str, output_dir: str = "./blog_articles",
                 enable_ai: bool = False, config_file: str = None):
        self.base_url = url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # 创建子目录
        (self.output_dir / "articles").mkdir(exist_ok=True)
        (self.output_dir / "summaries").mkdir(exist_ok=True)
        (self.output_dir / "images").mkdir(exist_ok=True)

        # 配置
        self.config = self.load_config(config_file)
        self.enable_ai = enable_ai or self.config.get('enable_ai', False)
        self.min_delay = self.config.get('min_delay', 2)
        self.max_delay = self.config.get('max_delay', 5)
        self.max_retries = self.config.get('max_retries', 3)

        # API keys
        self.anthropic_key = self.config.get('anthropic_api_key')
        self.openai_key = self.config.get('openai_api_key')

        self.driver = None
        self.platform = None
        self.platform_config = None

        # 进度跟踪
        self.progress = self.load_progress()

    def load_config(self, config_file: str) -> dict:
        """加载配置文件"""
        default_config = {
            'min_delay': 2,
            'max_delay': 5,
            'max_retries': 3,
            'anthropic_api_key': None,
            'openai_api_key': None,
            'enable_ai': False,
            'custom_selectors': {}
        }

        config_paths = [
            config_file,
            '~/.claude/skills/blog-scraper/config.json',
            './blog_scraper_config.json'
        ]

        for path in config_paths:
            if path and Path(path).expanduser().exists():
                try:
                    with open(Path(path).expanduser(), 'r', encoding='utf-8') as f:
                        user_config = json.load(f)
                        default_config.update(user_config)
                        logger.info(f"配置已加载: {path}")
                        break
                except Exception as e:
                    logger.warning(f"配置加载失败 {path}: {e}")

        return default_config

    def load_progress(self) -> dict:
        """加载进度"""
        progress_file = self.output_dir / "progress.json"
        if progress_file.exists():
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {'articles': [], 'scraped_urls': []}

    def save_progress(self):
        """保存进度"""
        progress_file = self.output_dir / "progress.json"
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2)

    def is_scraped(self, url: str) -> bool:
        """检查是否已抓取"""
        return url in self.progress.get('scraped_urls', [])

    def setup_driver(self, headless: bool = True):
        """设置浏览器"""
        options = Options()

        if headless:
            options.add_argument('--headless=new')

        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        })

        logger.info("浏览器已启动")

    def human_delay(self):
        """模拟人类延迟"""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)

    def scroll_page(self):
        """滚动页面"""
        for _ in range(3):
            self.driver.execute_script("window.scrollBy(0, window.innerHeight * 0.5)")
            time.sleep(0.5 + random.random() * 0.5)

    def get_article_links(self) -> List[Dict]:
        """获取文章链接列表"""
        logger.info(f"正在获取文章列表: {self.base_url}")

        try:
            self.driver.get(self.base_url)
            self.human_delay()

            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            time.sleep(3)

            # 使用平台配置
            config = self.platform_config or BlogPlatform.PLATFORMS['generic']

            # 查找文章容器
            articles = []
            for list_selector in config['article_list']:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, list_selector)
                    if elements:
                        logger.info(f"找到 {len(elements)} 个文章容器")
                        for elem in elements:
                            try:
                                link = elem.find_element(By.TAG_NAME, "a")
                                url = link.get_attribute('href')
                                title = link.text.strip()

                                if url and title and len(title) > 5:
                                    articles.append({
                                        'title': title,
                                        'url': url,
                                        'date': ''
                                    })
                            except:
                                continue
                        break
                except:
                    continue

            # 如果没找到，尝试所有链接
            if not articles:
                logger.info("尝试通用链接提取")
                links = self.driver.find_elements(By.TAG_NAME, "a")
                seen = set()

                for link in links:
                    try:
                        url = link.get_attribute('href')
                        if url and self.is_article_url(url):
                            if url not in seen:
                                seen.add(url)
                                title = link.text.strip()
                                if title and len(title) > 5:
                                    articles.append({
                                        'title': title,
                                        'url': url,
                                        'date': ''
                                    })
                    except:
                        continue

            # 去重
            seen_urls = set()
            unique_articles = []
            for article in articles:
                if article['url'] not in seen_urls:
                    seen_urls.add(article['url'])
                    unique_articles.append(article)

            logger.info(f"找到 {len(unique_articles)} 篇文章")
            return unique_articles

        except Exception as e:
            logger.error(f"获取文章列表失败: {e}")
            return []

    def is_article_url(self, url: str) -> bool:
        """判断是否为文章 URL"""
        # 排除的路径
        exclude = ['tag', 'category', 'author', 'page', 'search', 'admin', 'login', 'signup']

        parsed = urlparse(url)
        path = parsed.path.lower()

        # 排除
        for exc in exclude:
            if exc in path:
                return False

        # 文章路径特征
        article_indicators = ['post', 'article', 'blog', '/p/', '/20']
        return any(ind in path for ind in article_indicators)

    def extract_article(self, url: str, retry: int = 0) -> Optional[Dict]:
        """提取文章内容"""
        try:
            logger.info(f"正在提取: {url}")
            self.driver.get(url)

            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            self.human_delay()
            self.scroll_page()
            time.sleep(2)

            # 使用平台配置
            config = self.platform_config or BlogPlatform.PLATFORMS['generic']

            # 查找内容
            content_elem = None
            for content_selector in config['article_content']:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, content_selector)
                    if elem:
                        content_elem = elem
                        break
                except:
                    continue

            if not content_elem:
                logger.warning("未找到文章内容")
                return None

            content_html = content_elem.get_attribute('innerHTML')

            # 提取标题
            title = ""
            for title_selector in config['title']:
                try:
                    title_elem = self.driver.find_element(By.CSS_SELECTOR, title_selector)
                    title = title_elem.text.strip()
                    if title:
                        break
                except:
                    continue

            # 提取元数据
            meta = {}
            try:
                # 日期
                date_elem = self.driver.find_element(By.CSS_SELECTOR, "time, .date, .post-date")
                meta['date'] = date_elem.text.strip()
            except:
                pass

            try:
                # 作者
                author_elem = self.driver.find_element(By.CSS_SELECTOR, ".author, .by-author, [class*='author']")
                meta['author'] = author_elem.text.strip()
            except:
                pass

            logger.info(f"标题: {title}")
            logger.info(f"内容长度: {len(content_html)} 字符")

            return {
                'title': title,
                'content': content_html,
                'meta': meta,
                'url': url
            }

        except Exception as e:
            logger.error(f"提取失败 (尝试 {retry + 1}/{self.max_retries}): {e}")

            if retry < self.max_retries - 1:
                time.sleep(5)
                return self.extract_article(url, retry + 1)

            return None

    def html_to_markdown(self, html_content: str) -> str:
        """HTML 转 Markdown"""
        if not html_content:
            return ""

        if HTML2Text:
            h = HTML2Text()
            h.ignore_links = False
            h.ignore_images = False
            h.ignore_emphasis = False
            h.body_width = 0
            return h.handle(html_content)
        else:
            import html as html_module
            text = html_module.unescape(re.sub(r'<[^>]+>', ' ', html_content))
            text = re.sub(r'\s+', ' ', text)
            return text.strip()

    def generate_summary(self, content: str) -> str:
        """生成 AI 摘要"""
        if not self.enable_ai:
            return ""

        try:
            if self.anthropic_key and anthropic:
                client = anthropic.Anthropic(api_key=self.anthropic_key)
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=300,
                    messages=[{
                        "role": "user",
                        "content": f"请为以下文章生成一个简洁的摘要（2-3句话）：\n\n{content[:3000]}"
                    }]
                )
                return response.content[0].text.strip()

            elif self.openai_key and openai:
                client = openai.OpenAI(api_key=self.openai_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{
                        "role": "user",
                        "content": f"请为以下文章生成一个简洁的摘要（2-3句话）：\n\n{content[:3000]}"
                    }],
                    max_tokens=200
                )
                return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"摘要生成失败: {e}")

        return ""

    def save_article(self, article_data: Dict, article_info: Dict) -> bool:
        """保存文章"""
        try:
            title = article_info['title']
            url = article_info['url']

            # 安全文件名
            safe_title = re.sub(r'[^\w\s-]', '', title).strip()
            safe_title = re.sub(r'[-\s]+', '-', safe_title)

            # Markdown 内容
            markdown_content = self.html_to_markdown(article_data['content'])

            # 保存文章
            article_file = self.output_dir / "articles" / f"{safe_title}.md"
            with open(article_file, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n")
                f.write(f"**来源**: {url}\n\n")
                if article_data.get('meta'):
                    for key, value in article_data['meta'].items():
                        f.write(f"**{key}**: {value}\n")
                    f.write("\n")
                f.write(markdown_content)

            logger.info(f"✓ 文章已保存: {article_file}")

            # 生成摘要
            if self.enable_ai:
                summary = self.generate_summary(markdown_content)
                if summary:
                    summary_file = self.output_dir / "summaries" / f"{safe_title}-summary.md"
                    with open(summary_file, 'w', encoding='utf-8') as f:
                        f.write(f"# {title} - 摘要\n\n{summary}")
                    logger.info(f"✓ 摘要已保存: {summary_file}")

            return True

        except Exception as e:
            logger.error(f"保存失败: {e}")
            return False

    def scrape(self, limit: int = None, reset: bool = False):
        """运行抓取器"""
        try:
            # 识别平台
            self.setup_driver()
            self.platform = BlogPlatform.identify_platform(self.base_url, self.driver)
            self.platform_config = BlogPlatform.PLATFORMS.get(self.platform, BlogPlatform.PLATFORMS['generic'])

            # 获取文章列表
            articles = self.get_article_links()

            if not articles:
                logger.warning("未找到文章")
                return

            # 限制数量
            if limit:
                articles = articles[:limit]

            logger.info(f"准备抓取 {len(articles)} 篇文章")

            success_count = 0
            skip_count = 0

            for i, article in enumerate(articles, 1):
                logger.info(f"\n进度: {i}/{len(articles)}")

                # 检查是否已抓取
                if not reset and self.is_scraped(article['url']):
                    logger.info("跳过已抓取的文章")
                    skip_count += 1
                    continue

                # 提取内容
                article_data = self.extract_article(article['url'])

                if article_data:
                    # 保存
                    if self.save_article(article_data, article):
                        success_count += 1
                        self.progress['scraped_urls'].append(article['url'])
                        self.progress['articles'].append({
                            'title': article['title'],
                            'url': article['url'],
                            'scraped_at': datetime.now().isoformat()
                        })
                        self.save_progress()

                # 延迟
                if i < len(articles):
                    delay = random.uniform(8, 15)
                    logger.info(f"等待 {delay:.1f} 秒...")
                    time.sleep(delay)

            logger.info(f"\n抓取完成！")
            logger.info(f"成功: {success_count}, 跳过: {skip_count}, 总计: {len(articles)}")
            logger.info(f"保存位置: {self.output_dir}")

        except KeyboardInterrupt:
            logger.info("\n用户中断")
        except Exception as e:
            logger.error(f"抓取过程出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='通用博客文章抓取器')
    parser.add_argument('url', help='博客网址')
    parser.add_argument('-o', '--output', default='./blog_articles', help='输出目录')
    parser.add_argument('-n', '--number', type=int, help='抓取数量限制')
    parser.add_argument('--headless', action='store_true', default=True, help='无头模式')
    parser.add_argument('--no-headless', action='store_false', dest='headless', help='显示浏览器')
    parser.add_argument('--ai', action='store_true', help='启用 AI 摘要')
    parser.add_argument('--reset', action='store_true', help='重置进度')

    args = parser.parse_args()

    logger.info(f"博客抓取器启动")
    logger.info(f"目标: {args.url}")
    logger.info(f"输出: {args.output}")

    scraper = BlogScraper(
        url=args.url,
        output_dir=args.output,
        enable_ai=args.ai
    )

    scraper.scrape(limit=args.number, reset=args.reset)


if __name__ == "__main__":
    main()
