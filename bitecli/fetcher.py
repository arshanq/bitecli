import feedparser
from . import db
from . import config

def fetch_feeds() -> int:
    """
    Fetches all configured feeds and stores new articles in the database.
    Returns the number of new articles inserted.
    """
    db.init_db()
    feeds = config.get_feeds()
    
    new_articles_count = 0
    
    for feed in feeds:
        try:
            parsed = feedparser.parse(feed["url"])
            if not parsed.entries:
                continue
                
            for entry in parsed.entries:
                # Basic metadata extraction depending on RSS/Atom variants
                title = entry.get("title", "No Title")
                link = entry.get("link", "")
                
                if not link:
                    continue
                
                content = ""
                if "content" in entry:
                    content = entry.content[0].value
                elif "summary" in entry:
                    content = entry.get("summary", "")
                elif "description" in entry:
                    content = entry.get("description", "")
                
                published = entry.get("published", entry.get("updated", ""))
                
                article = {
                    "title": title,
                    "url": link,
                    "content": content,
                    "published": published,
                    "feed_name": feed["name"]
                }
                
                inserted = db.store_article(article)
                if inserted:
                    new_articles_count += 1
                    
        except Exception as e:
            # We silently ignore errors per feed, CLI will handle broad reporting
            pass
            
    return new_articles_count
