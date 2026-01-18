from django.core.management.base import BaseCommand

from user.tasks import generate_monthly_bills_task
from dairy.tasks import auto_order_create, create_daily_distributor_orders
from django.core.cache import cache
from gaytri_farm_app.utils import ist_timezone

def run_once(key, ttl=86400):  # 24 hours
    if cache.get(key):
        return False
    cache.set(key, True, ttl)
    return True


class Command(BaseCommand):
    help = "Daily cron runner (05:00 IST)"

    def handle(self, *args, **kwargs):
        now = ist_timezone()

        day = now.day

        # 🔹 Runs EVERY DAY at ~05:00 IST
        if run_once(f"daily_orders_{now.date()}"):
            create_daily_distributor_orders()

        # 🔹 Runs ONLY on 25th
        if day == 25 and run_once("auto_order_create_25"):
            auto_order_create()

        # 🔹 Runs ONLY on 1st
        if day == 1 and run_once("monthly_bills_1"):
            generate_monthly_bills_task()
