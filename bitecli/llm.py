import requests
import json
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from . import config
from . import db

_TWO_WEEKS = timedelta(weeks=2)

def _is_too_old_for_summary(article: dict, unfiltered_feed_names: set) -> bool:
    """Returns True if the article is older than 2 weeks and not from a research or documentation feed."""
    if article.get('feed_name') in unfiltered_feed_names:
        return False
    published = article.get('published', '')
    if not published:
        return False
    try:
        published_dt = parsedate_to_datetime(published)
    except Exception:
        try:
            published_dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
        except Exception:
            return False
    return (datetime.now(tz=timezone.utc) - published_dt) > _TWO_WEEKS

SYSTEM_PROMPT = """You are an expert technical educator. 
Summarize the provided technical article or research topic into a short, 'bite-sized' educational markdown lesson that is visually appealing and easy to read on a terminal.
Focus on the core concepts, why it matters, and key takeaways. Use bullet points and inline code blocks if relevant. Do NOT wrap the entire response in a markdown code block. Maintain a professional yet accessible tone. Keep it concise (around 200-300 words)."""

def generate_summary(article_title: str, article_content: str, article_url: str) -> str:
    """Uses the configured LLM to generate a summary."""
    conf = config.load_config()
    provider = conf.get("llm_provider", "gemini")
    api_key = conf.get("api_keys", {}).get(provider, "")
    
    if not api_key:
        return f"Error: No API key found for provider '{provider}'. Please run `bitecli config` to set it."
        
    prompt = f"Title: {article_title}\nURL: {article_url}\nContent Snippet: {article_content[:5000]}"
    
    try:
        if provider == "gemini":
            return _call_gemini(api_key, prompt)
        elif provider == "openai":
            return _call_openai(api_key, prompt)
        elif provider == "claude":
            return _call_claude(api_key, prompt)
        elif provider == "perplexity":
            return _call_perplexity(api_key, prompt)
        else:
            return f"Error: Unsupported provider '{provider}'"
    except Exception as e:
        return f"Error summarizing content: {str(e)}"

def fill_summary_buffer(console=None, force=False):
    """
    Checks how many buffered summaries exist. If below the limit, 
    fetches unsummarized articles and generates summaries for them 
    up to the limit.
    """
    conf = config.load_config()
    limit = conf.get("max_buffered_summaries", 7)
    
    # Are we already full?
    stats = db.get_stats()
    buffered = stats.get('buffered', 0)
    
    if buffered >= limit and not force:
        return 0
        
    needed = limit - buffered
    unfiltered_feed_names = {f['name'] for f in config.get_feeds() if f.get('type') in ('research', 'documentation')}
    # Fetch extra candidates to account for articles filtered out by age
    candidates = db.get_unsummarized_articles(needed * 3)
    articles_to_summarize = [
        a for a in candidates
        if not _is_too_old_for_summary(a, unfiltered_feed_names)
    ][:needed]

    if not articles_to_summarize:
        return 0
        
    count = 0
    for article in articles_to_summarize:
        if console:
            console.print(f"[dim]Background buffering summary for: {article['title']}[/]")
            
        summary = generate_summary(
            article_title=article['title'],
            article_content=article['content'],
            article_url=article['url']
        )
        
        # Only save if we got a real summary (not an error string lacking API key)
        if not summary.startswith("Error"):
            db.save_summary(article['id'], summary)
            count += 1
        else:
            if console:
                console.print(f"[red]{summary}[/]")
            break # Stop trying if API key is invalid
            
    return count

def _call_gemini(api_key: str, prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    resp = requests.post(url, headers=headers, json=data)
    resp.raise_for_status()
    result = resp.json()
    return result["candidates"][0]["content"]["parts"][0]["text"]

def _call_openai(api_key: str, prompt: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    }
    resp = requests.post(url, headers=headers, json=data)
    resp.raise_for_status()
    result = resp.json()
    return result["choices"][0]["message"]["content"]

def _call_perplexity(api_key: str, prompt: str) -> str:
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    }
    resp = requests.post(url, headers=headers, json=data)
    resp.raise_for_status()
    result = resp.json()
    return result["choices"][0]["message"]["content"]

def _call_claude(api_key: str, prompt: str) -> str:
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    resp = requests.post(url, headers=headers, json=data)
    resp.raise_for_status()
    result = resp.json()
    return result["content"][0]["text"]
