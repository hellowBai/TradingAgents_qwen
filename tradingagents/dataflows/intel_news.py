# 在文件顶部添加必要的导入
import feedparser
from datetime import datetime, timedelta
import re

# ... 现有代码 ...

def get_domestic_rss_news(curr_date, look_back_days=7, limit=5):
    """
    获取国内RSS新闻，时间范围从curr_date往前推look_back_days天
    保持与get_global_news_openai相似的输入输出格式
    
    Args:
        curr_date: 当前日期字符串 (格式: 'YYYY-MM-DD')
        look_back_days: 回溯天数，默认7天
        limit: 返回文章数量限制，默认5篇
        
    Returns:
        str: 格式化的新闻文本，每篇新闻包含标题、链接、发布时间和摘要
    """
    # 解析日期
    try:
        end_date = datetime.strptime(curr_date, '%Y-%m-%d')
        start_date = end_date - timedelta(days=look_back_days)
    except ValueError:
        # 如果日期格式不正确，使用当前日期
        end_date = datetime.now()
        start_date = end_date - timedelta(days=look_back_days)
    
    # 国内主要财经新闻RSS源列表
    rss_feeds = [
        # 新浪财经
        'http://rss.sina.com.cn/finance/finance.xml',
        # 网易财经
        'http://money.163.com/special/002526BH/feed.xml',
        # 东方财富
        'http://rss.eastmoney.com/feed.xml',
        # 财新网
        'http://www.caixin.com/rss/finance.xml',
        # 第一财经
        'http://www.yicai.com/rss/finance.xml',
        # 和讯网
        'http://news.hexun.com/rss/finance.xml',
    ]
    
    all_articles = []
    
    for rss_url in rss_feeds:
        try:
            feed = feedparser.parse(rss_url)
            
            for entry in feed.entries:
                # 检查文章发布时间是否在指定范围内
                if hasattr(entry, 'published_parsed'):
                    article_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed'):
                    article_date = datetime(*entry.updated_parsed[:6])
                else:
                    continue
                
                # 过滤时间范围
                if start_date <= article_date <= end_date:
                    # 提取文章信息
                    title = getattr(entry, 'title', '无标题')
                    link = getattr(entry, 'link', '')
                    
                    # 获取摘要或描述
                    if hasattr(entry, 'summary'):
                        summary = entry.summary
                        # 清理HTML标签
                        summary = re.sub(r'<[^>]+>', '', summary)
                        summary = summary.strip()
                    elif hasattr(entry, 'description'):
                        summary = entry.description
                        summary = re.sub(r'<[^>]+>', '', summary)
                        summary = summary.strip()
                    else:
                        summary = '无摘要'
                    
                    # 限制摘要长度
                    if len(summary) > 200:
                        summary = summary[:197] + '...'
                    
                    article_info = {
                        'title': title,
                        'link': link,
                        'date': article_date.strftime('%Y-%m-%d %H:%M:%S'),
                        'summary': summary,
                        'source': feed.feed.get('title', '未知来源')
                    }
                    
                    all_articles.append(article_info)
                    
                    # 如果达到限制数量，停止收集
                    if len(all_articles) >= limit * 2:  # 多收集一些用于去重
                        break
        except Exception as e:
            print(f"Error parsing RSS feed {rss_url}: {e}")
            continue
    
    # 去重（基于标题）
    unique_articles = []
    seen_titles = set()
    
    for article in all_articles:
        # 简单去重：检查标题是否已存在
        title_key = article['title'].lower().strip()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_articles.append(article)
    
    # 按时间排序（最新的在前）
    unique_articles.sort(key=lambda x: x['date'], reverse=True)
    
    # 限制返回数量
    unique_articles = unique_articles[:limit]
    
    # 格式化输出，保持与get_global_news_openai相似的格式
    if not unique_articles:
        return f"在{look_back_days}天内（{start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}）未找到相关国内新闻。"
    
    output_lines = [f"国内新闻 ({start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}):\n"]
    
    for i, article in enumerate(unique_articles, 1):
        output_lines.append(f"{i}. {article['title']}")
        output_lines.append(f"   链接: {article['link']}")
        output_lines.append(f"   发布时间: {article['date']}")
        output_lines.append(f"   来源: {article['source']}")
        output_lines.append(f"   摘要: {article['summary']}")
        output_lines.append("")  # 空行分隔
    
    output_lines.append(f"共找到 {len(unique_articles)} 篇相关新闻。")
    
    return "\n".join(output_lines)
