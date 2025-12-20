import logging
from celery import shared_task
from django.utils import timezone
from django.db.models import Sum , F, ExpressionWrapper, IntegerField
from user.models import User
from .models import Order, DistributorOrder, CacheOrder

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

        # Update distributor balance: subtract total amount of distributor orders
        total_amount = sum(item['total_amount'] for item in grouped_orders)
        User.objects.filter(user_id=distributor.user_id).update(
            balance=F('balance') - total_amount
        )

        logger.info(f"📝 Created {count} DistributorOrder entries for distributor {distributor.user_id}")
        logger.info(f"💰 Updated balance for distributor {distributor.user_id}: -{total_amount}")

    logger.info(f"✅ Completed: Total {total_created} DistributorOrder entries created.")

@shared_task
def auto_order_create():
    """
    Monthly scheduled task to automatically create orders for customers.
    Creates 3-month bulk orders for customers who:
    - Have a cache_order
    - Are not paused (is_pause == False)
    - Don't have orders from next month onwards
    """
    from datetime import date, timedelta
    from calendar import monthrange
    from .models import CacheOrder, Order
    
    logger.info("Starting auto_order_create task")
    
    today = date.today()
    # Calculate first day of next month
    if today.month == 12:
        next_month_start = date(today.year + 1, 1, 1)
    else:
        next_month_start = date(today.year, today.month + 1, 1)
    
    # Get eligible customers: have cache_order, not paused
    cache_orders = CacheOrder.objects.filter(
        customer__is_pause=False
    ).select_related('customer', 'customer__delivery_staff')
    
    if not cache_orders.exists():
        logger.info("No eligible customers found with cache orders")
        return
    
    total_orders_created = 0
    customers_processed = 0
    
    for cache_order in cache_orders:
        customer = cache_order.customer
        
        # Check if customer already has orders from next month onwards
        existing_future_orders = Order.objects.filter(
            customer=customer,
            date__gte=next_month_start
        ).exists()
        
        if existing_future_orders:
            logger.info(f"Skipping customer {customer.user_id} - already has future orders")
            continue
        
        # Create 3 months of orders based on cache_order
        product = cache_order.product
        base_quantity = cache_order.quantity
        order_type = cache_order.order_type
        delivery_staff = customer.delivery_staff
        
        orders_to_create = []
        start_date = next_month_start
        
        # Create orders for 3 months
        for month_offset in range(3):
            month_num = start_date.month + month_offset
            year = start_date.year + (month_num - 1) // 12
            month = ((month_num - 1) % 12) + 1
            
            last_day = monthrange(year, month)[1]
            start_day = start_date.day if month_offset == 0 else 1
            
            for day in range(start_day, last_day + 1):
                order_date = date(year, month, day)
                
                # Use 0-based index within month for patterns
                idx = day - 1
                
                if order_type == 'every_day':
                    quantity = base_quantity
                elif order_type == 'alternate_day':
                    # Keep 1st, 3rd, 5th... (idx 0, 2, 4 => even idx)
                    if idx % 2 != 0:
                        continue
                    quantity = base_quantity
                elif order_type == 'one_two_cycle':
                    # Alternate 1 and 2 quantities each day
                    quantity = 2 if idx % 2 != 0 else 1
                else:
                    # Unknown type, skip
                    logger.warning(f"⚠️ Unknown order_type '{order_type}' for customer {customer.user_id}")
                    continue
                
                orders_to_create.append(
                    Order(
                        customer=customer,
                        delivery_staff=delivery_staff,
                        product=product,
                        quantity=quantity,
                        total_price=product.price * quantity,
                        date=order_date
                    )
                )
        
        # Bulk create all orders for this customer
        if orders_to_create:
            Order.objects.bulk_create(orders_to_create)
            total_orders_created += len(orders_to_create)
            customers_processed += 1
            logger.info(f"✅ Created {len(orders_to_create)} orders for customer {customer.user_id}")
    
    logger.info(f"🎉 Auto order creation completed: {total_orders_created} orders created for {customers_processed} customers")