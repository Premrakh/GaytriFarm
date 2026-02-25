from datetime import date, timedelta
from calendar import monthrange
from .models import Order


def create_bulk_orders(customer, product, base_quantity, order_type,start_date):
    """
    Create bulk orders for a customer for the next 3 months based on order type.
    
    Args:
        customer: User instance (customer)
        product: Product instance
        base_quantity: Base quantity for orders
        order_type: Type of order ('every_day', 'alternate_day', 'one_two_cycle')
    
    Returns:
        int: Number of orders created
    """
    delivery_staff = getattr(customer, "delivery_staff", None)
    today = date.today()
    # start_date = today + timedelta(days=1)  # start from tomorrow
    orders_to_create = []
    is_order_alternate = True
    cycle_order_count = 1
    # create orders for upcoming 3 months: remainder of this month (from tomorrow) + next 2 months
    for month_offset in range(3):
        # compute year and month for this offset
        month_num = start_date.month + month_offset
        year = start_date.year + (month_num - 1) // 12
        month = ((month_num - 1) % 12) + 1

        last_day = monthrange(year, month)[1]
        # determine starting day for the first month (start_date.day), else 1
        start_day = start_date.day if month_offset == 0 else 1

        for day in range(start_day, last_day + 1):
            order_date = date(year, month, day)
            # skip any past dates just in case
            if order_date <= today:
                continue

            # Use 0-based index within month for patterns
            idx = day - 1

            if order_type == 'every_day':
                quantity = base_quantity
            elif order_type == 'alternate_day' and is_order_alternate:
                quantity = base_quantity
                is_order_alternate = not is_order_alternate

            elif order_type == 'one_two_cycle':
                quantity = cycle_order_count
                cycle_order_count = 2 if cycle_order_count == 1 else 1

            else:
                is_order_alternate = not is_order_alternate
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

    # Bulk create all orders
    if orders_to_create:
        Order.objects.bulk_create(orders_to_create)

    # Unpause customer if they were paused
    if customer.is_pause:
        customer.is_pause = False
        customer.save(update_fields=["is_pause"])
    
    return len(orders_to_create)
