from celery import shared_task
from .utils import sync_new_articles
from trade.utils import send_health_check_message


@shared_task
def update_news():

    stats = sync_new_articles()
    if stats['stopped_reason'] == 'error':
        send_health_check_message("ERORR: News update encountered an error." + str(stats))
