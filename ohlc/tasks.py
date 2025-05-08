from celery import shared_task


@shared_task
def fetch_hourly_data():
    print("Fetching hourly data...")  # or call your real data function


@shared_task
def fetch_every_4_hours():
    print("Fetching data every 4 hours...")


@shared_task
def fetch_every_1_mins():
    print(1)
    print("Fetching data every 4 hours...")