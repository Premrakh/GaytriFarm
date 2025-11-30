import logging
from celery import shared_task
from django.utils import timezone
from django.db.models import Sum , F, ExpressionWrapper, IntegerField
from user.models import User
from .models import Order,  DistributorOrder

logger = logging.getLogger(__name__)

@shared_task
def create_daily_distributor_orders():
    today = timezone.now().date()
    logger.info(f"➡️ Starting Distributor Order Creation for {today}")

    distributors = User.objects.filter(role=User.DISTRIBUTOR, role_accepted=True)

    if not distributors.exists():
        return

    total_created = 0

    for distributor in distributors:

        grouped_orders = (
            Order.objects
            .filter(
                customer__distributor=distributor,
                date=today
            )
            .values('product_id', 'product__distributor_price')
            .annotate(
                total_qty=Sum('quantity'),
                total_amount=ExpressionWrapper(
                    Sum('quantity') * F('product__distributor_price'),
                    output_field=IntegerField()
                )
            )
        )

        if not grouped_orders.exists():
            logger.info(f"⛔ No user customers today for distributor {distributor.user_id}, skipping.")
            continue

        distributor_orders = [
            DistributorOrder(
                distributor=distributor,
                product_id=item['product_id'],
                quantity=item['total_qty'],
                total_price=item['total_amount']
            )
            for item in grouped_orders
        ]

        DistributorOrder.objects.bulk_create(distributor_orders)
        count = len(distributor_orders)
        total_created += count

        logger.info(f"📝 Created {count} DistributorOrder entries for distributor {distributor.user_id}")

    logger.info(f"✅ Completed: Total {total_created} DistributorOrder entries created.")
