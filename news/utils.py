import requests
from datetime import datetime
from typing import Dict, Optional
from decouple import config
from .models import NewsArticle
from django.utils import timezone
import pytz
from logging import getLogger
import time


logger = getLogger(__name__)


# ONE BATCH FETCH AND SAVE ARTICLES
def fetch_and_save_articles(limit: int = 100, to_ts: Optional[int] = None):
    """
    Fetch news articles from CoinDesk API and save them to database
    
    Args:
        limit (int): Number of articles to fetch (default: 100)
        to_ts (int, optional): Timestamp to fetch articles up to. 
                               If None, uses current timestamp.
    
    Returns:
        tuple: (updated_flag, last_timestamp)
            - updated_flag: 1 if found existing article (should stop), 0 if all new, -1 if error
            - last_timestamp: timestamp of the last article in the batch
    """

    updated = 0
    last_timestamp = None
    created = 0

    api_key = config('COINDESK_API_KEY')
    
    url = 'https://data-api.coindesk.com/news/v1/article/list'
    if to_ts is None:
        to_ts = int(datetime.now().timestamp())

    params = {
        "lang": "EN",
        "limit": limit,
        "to_ts": to_ts,
        "api_key": api_key
    }
    
    headers = {
        "Content-type": "application/json; charset=UTF-8"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        json_response = response.json()
        articles = json_response.get('Data', [])

        if not articles:
            logger.info("No articles returned from API")
            return 0, 0, None

        seen_combinations = set()

        for article_data in articles:
            try:
                keywords_list = []
                if article_data.get('KEYWORDS'):
                    keywords_list = [k.strip() for k in article_data['KEYWORDS'].split('|')]
                
                categories_list = []
                if article_data.get('CATEGORY_DATA'):
                    categories_list = [cat['CATEGORY'] for cat in article_data['CATEGORY_DATA']]
                
                published_datetime = timezone.make_aware(
                    datetime.fromtimestamp(article_data['PUBLISHED_ON']),
                    timezone=pytz.UTC
                )


                unique_key = (published_datetime, article_data['TITLE'])
        
                if unique_key in seen_combinations:
                    logger.info(f"Duplicate in batch: {article_data['TITLE'][:50]}... - Skipping")
                    continue
                
                seen_combinations.add(unique_key)
                

                article, is_created = NewsArticle.objects.update_or_create(
                    id=article_data['ID'],
                    defaults={
                        'published_on': published_datetime,
                        'title': article_data['TITLE'],
                        'url': article_data['URL'],
                        'source_id': article_data['SOURCE_ID'],
                        'body': article_data['BODY'],
                        'keywords': keywords_list,
                        'sentiment': article_data.get('SENTIMENT', 'NEUTRAL'),
                        'categories': categories_list,
                    }
                )
                
                if is_created:
                    created += 1
                
                else:
                    updated = 1
                    logger.info(f"Found existing article: {article.id}, stopping...")
                    return updated, created, article_data['PUBLISHED_ON']
                
            except Exception as e:
                logger.error(f"Failed to save article {article_data.get('ID')}: {e}")
        
        # Get the timestamp of the last (oldest) article in this batch
        last_timestamp = articles[-1]['PUBLISHED_ON'] if articles else None
        
        return updated, created, last_timestamp
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching articles: {e}")
        return -1, created, last_timestamp


# FETCH ALL ARTICLES UNTIL TARGET TIMESTAMP
def fetch_all_articles_until(target_timestamp = None, delay: float = 0.5):
    """
    Fetch all articles from now back to a target timestamp
    
    Args:
        target_timestamp (int, optional): Stop when reaching this timestamp. 
        batch_size (int): Number of articles per API call (default: 100)
        delay (float): Delay in seconds between API calls to avoid rate limiting (default: 1.0)
    
    Returns:
        dict: Statistics about the operation
            - total_fetched: Total number of new articles saved
            - total_batches: Number of API calls made
            - stopped_reason: Why the fetch stopped ('reached_target', 'found_existing', 'no_more_data', 'error')
            - final_timestamp: The oldest timestamp reached
    """
    
    stats = {
        'total_fetched': 0,
        'total_batches': 0,
        'stopped_reason': None,
        'final_timestamp': None
    }
    
    # IF NEED TO GET PRIVIOUS DATA CHANGE THIS TO STARTING TIMESTAMP
    current_ts = int(datetime.now().timestamp())
    
    logger.info(f"Starting fetch from {datetime.fromtimestamp(current_ts)}")
    if target_timestamp:
        logger.info(f"Target timestamp: {datetime.fromtimestamp(target_timestamp)}")
    
    while True:
        stats['total_batches'] += 1
        
        logger.info(f"Batch {stats['total_batches']}: Fetching up to {datetime.fromtimestamp(current_ts)}")
        
        updated, created, last_ts = fetch_and_save_articles(to_ts=current_ts)
        
        if updated == -1:
            stats['stopped_reason'] = 'error'
            logger.error("Error occurred, stopping fetch")
            break

        stats['total_fetched'] += created
        stats['final_timestamp'] = last_ts
        
        if updated == 1:
            stats['stopped_reason'] = 'found_existing'
            logger.info("Found existing article, stopping fetch")
            break     
        
        logger.info(f"Saved batch. Last article timestamp: {datetime.fromtimestamp(last_ts)}")
        

        if target_timestamp and last_ts <= target_timestamp:
            stats['stopped_reason'] = 'reached_target'
            logger.info(f"Reached target timestamp: {datetime.fromtimestamp(target_timestamp)}")
            break
        
        current_ts = last_ts - 1
        
        logger.info(f"Waiting {delay} seconds before next batch...")
        time.sleep(delay)
    
    logger.info(f"Fetch complete. Total batches: {stats['total_batches']}, "
                f"Total new articles: {stats['total_fetched']}, "
                f"Reason: {stats['stopped_reason']}")
    
    return stats


# TO UPDATE NEW ARTICLES
def sync_new_articles():
    """
    Fetch all new articles from now until we find an existing article in the database
    
    Returns:
        dict: Statistics about the sync operation
    """

    logger.info("Starting sync for new articles...")
    stats = fetch_all_articles_until()
    logger.info("Sync complete.")
    return stats


# TO FILL FOR FIRST TIME HISTORICAL ARTICLES
def backfill_articles(target_timestamp: int):
    """
    Backfill articles from the oldest article in DB back to a target timestamp
    
    Args:
        target_timestamp (int): Stop when reaching this timestamp
    
    Returns:
        dict: Statistics about the backfill operation
    """

    logger.info("Starting backfill for articles...")
    logger.info(f"Starting backfill from now to {datetime.fromtimestamp(target_timestamp)}")
    
    return fetch_all_articles_until(target_timestamp=target_timestamp)



# IF Duplicate occurred remove by this
'''
from django.db.models import Count, Min
from .models import NewsArticle

def remove_duplicate_articles():
    """
    Remove duplicate articles, keeping only the first one (oldest by created_at)
    """
    # Find duplicates
    duplicates = (
        NewsArticle.objects
        .values('published_on', 'title')
        .annotate(
            count=Count('id'),
            min_id=Min('id')  # Keep the one with smallest ID
        )
        .filter(count__gt=1)
    )
    
    deleted_count = 0
    
    for dup in duplicates:
        # Get all articles with this published_on and title
        articles = NewsArticle.objects.filter(
            published_on=dup['published_on'],
            title=dup['title']
        ).order_by('id')
        
        # Keep the first one, delete the rest
        keep_article = articles.first()
        duplicates_to_delete = articles.exclude(id=keep_article.id)
        
        count = duplicates_to_delete.count()
        duplicates_to_delete.delete()
        deleted_count += count
        
        print(f"Kept article {keep_article.id}, deleted {count} duplicates")
    
    print(f"\nTotal duplicates removed: {deleted_count}")
    return deleted_count
'''