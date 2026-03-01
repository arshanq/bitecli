import argparse
import sys
import os
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text

from . import config
from . import fetcher
from . import db
from . import llm

console = Console()

def print_header():
    title = Text(" BiteCLI - Your Terminal Educator ", style="bold white on blue")
    console.print(title, justify="center")
    console.print()

def do_fetch():
    with console.status("[bold green]Fetching latest educational content...[/]"):
        count = fetcher.fetch_feeds(console=console)
    if count > 0:
        console.print(f"[bold green]Success![/] Fetched {count} new article(s).")
    else:
        console.print("[yellow]No new articles found right now.[/]")

def do_serve():
    db.init_db()
    
    # Are there any feeds or unread articles?
    stats = db.get_stats()
    if stats["total"] == 0:
        console.print("[yellow]Your library is empty. Run `bitecli fetch` first.[/]")
        return
        
    article = db.get_unread_article()
    if not article:
        console.print("[yellow]You've caught up! Run `bitecli fetch` to get more content.[/]")
        return
        
    print_header()
    
    # We now fetch the pre-computed summary
    summary = article.get('summary')
    if not summary:
        console.print("[red]Error:[/] The background summarizer hasn't prepared this article yet.")
        console.print("Run `bitecli fetch` to fill your buffered lessons.")
        return
    
    db.mark_as_read(article['id'])
    
    # Render the markdown properly
    md = Markdown(summary)
    panel = Panel(md, title=f"  [bold]{article['title']}[/]  ", subtitle=f"Source: {article['feed_name']} - {article['url']}", border_style="blue")
    
    console.print(panel)
    
    # Print reading stats
    stats = db.get_stats()
    unread = stats['unread']
    console.print(f"[dim]You have [bold]{unread}[/] unread bite-sized lessons left.[/]", justify="right")

def do_config(args):
    if args.provider:
        config.set_llm_provider(args.provider)
        console.print(f"[green]Default LLM provider set to {args.provider}[/]")
    
    if args.key:
        provider = args.provider or config.load_config().get('llm_provider', 'gemini')
        config.set_api_key(provider, args.key)
        console.print(f"[green]API key updated for {provider}[/]")
        
    if not args.provider and not args.key:
        conf = config.load_config()
        console.print(f"[bold]Current Provider:[/] {conf.get('llm_provider')}")
        console.print(f"[bold]Feeds Configured:[/] {len(conf.get('feeds', []))}")
        keys_set = [k for k, v in conf.get('api_keys', {}).items() if v]
        console.print(f"[bold]API Keys Configured For:[/] {', '.join(keys_set) if keys_set else 'None'}")
        
        console.print("\nTo update provider: `bitecli config --provider <gemini|openai|claude|perplexity>`")
        console.print("To set API key: `bitecli config --key <YOUR_KEY>`")

def do_clean(args):
    if args.all:
        count = db.delete_all_articles()
        console.print(f"[green]Cleared {count} article(s) from the cache.[/]")
    else:
        count = db.delete_read_articles()
        if count:
            console.print(f"[green]Removed {count} already-read article(s) from the cache.[/]")
        else:
            console.print("[yellow]Nothing to clean — no read articles in cache.[/]")

def do_hook():
    shell = os.environ.get('SHELL', '')
    rc_file = ""
    if "zsh" in shell:
        rc_file = "~/.zshrc"
    elif "bash" in shell:
        rc_file = "~/.bashrc"
    else:
        rc_file = "~/.profile"
        
    msg = f"""
    [bold underline]Automate BiteCLI[/]
    
    To get a bite-sized lesson every time you open a terminal, add this line to the end of your [bold]{rc_file}[/]:
    
    [bold green]bitecli serve --hook[/]
    
    (Note: The --hook flag ensures it runs quietly and exits gracefully if there's an error.)
    """
    console.print(Panel(msg, border_style="cyan"))

def main():
    parser = argparse.ArgumentParser(description="BiteCLI: Bite-sized terminal education")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # fetch
    subparsers.add_parser("fetch", help="Fetch new articles from configured feeds")
    
    # serve
    serve_parser = subparsers.add_parser("serve", help="Read a new bite-sized lesson")
    serve_parser.add_argument("--hook", action="store_true", help="Run in hook mode (silent failures)")
    
    # config
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_parser.add_argument("--provider", choices=["gemini", "openai", "claude", "perplexity"], help="Set the LLM provider")
    config_parser.add_argument("--key", help="Set the API key for the current or specified provider")
    
    # clean
    clean_parser = subparsers.add_parser("clean", help="Remove cached articles")
    clean_parser.add_argument("--all", action="store_true", help="Remove all articles, not just read ones")

    # hook
    subparsers.add_parser("hook", help="Show instructions to install shell hook")
    
    args = parser.parse_args()
    
    try:
        if args.command == "fetch":
            do_fetch()
        elif args.command == "serve" or args.command is None:
            # `bitecli` with no args defaults to serve, or you can run `bitecli serve`
            do_serve()
        elif args.command == "config":
            do_config(args)
        elif args.command == "clean":
            do_clean(args)
        elif args.command == "hook":
            do_hook()
    except Exception as e:
        if getattr(args, "hook", False):
            # Fail silently in hook mode so we don't spam terminal startup
            sys.exit(0)
        else:
            console.print(f"[bold red]Error:[/] {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    main()
