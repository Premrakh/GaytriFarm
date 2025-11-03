import logging
from celery import shared_task
from django.utils import timezone
from django.db.models import Sum , F
from django.core.files.base import ContentFile
from django.db import transaction

from user.models import User
from .models import Order
from .models import UserBill
from .pdf_generator import generate_bill_pdf

logger = logging.getLogger(__name__)

@shared_task()
def generate_monthly_bills_task(self):
    """
    Celery task to generate monthly bills for all customers.
    Same logic as the Django management command.
    """
    now = timezone.now()
    target_month = now.month - 1 if now.month > 1 else 12
    target_year = now.year if now.month > 1 else now.year - 1

    logger.info(f"Starting bill generation for {target_month}/{target_year}")

    customers = User.objects.filter(role=User.CUSTOMER, role_accepted=True)
    logger.info(f"Found {customers.count()} customers")
    errors = []
    user_bills = []
    for customer in customers:
        try:
            orders = (
                Order.objects.filter(
                    customer=customer,
                    status=Order.DELIVERED,
                    date__month=target_month,
                    date__year=target_year,
                )
                .select_related("product")
                .values(product_id=F("product__id"),product_name=F("product__name"),unit_price=F("product__price"),)
                .annotate(
                    total_quantity=Sum("quantity"),
                    total_amount=Sum("total_price"),
                )
            )

            product_breakdown = list(orders)
            if not product_breakdown:
                logger.info(f"No delivered orders for {customer.user_name} in {target_month}/{target_year}. Skipping bill generation.")
                continue

            grand_total = sum(order["total_amount"] for order in product_breakdown)
            total_items = sum(order["total_quantity"] for order in product_breakdown)


            bill_data = {
                "customer_id": str(customer.user_id),
                "customer_name": customer.user_name,
                "billing_period": {
                    "month": target_month,
                    "year": target_year,
                    "month_name": timezone.datetime(
                        target_year, target_month, 1
                    ).strftime("%B"),
                },
                "total_items": total_items,
                "total_amount": grand_total,
                "product_breakdown": product_breakdown,
                "generated_at": timezone.now().isoformat(),
            }

            logger.info(f"Generating PDF for {customer.user_name}...")
            pdf_content = generate_bill_pdf(bill_data)
            pdf_filename = f"bill_{customer.user_name}_{target_month}_{target_year}.pdf"

            user_bills.append(UserBill(user=customer,total_product=total_items,total_amount=grand_total))

        except Exception as e:
            error_msg = f"Bill generation failed for {customer.user_name}: {str(e)}"
            errors.append(error_msg)

    UserBill.objects.bulk_create(user_bills)
    logger.info("BILL GENERATION SUMMARY")

    logger.info(f"Period: {target_month}/{target_year}")
    logger.info(f"Bills Created: {len(user_bills)}")

    if errors:
        logger.error(f"Errors: {len(errors)}")
        for error in errors:
            logger.error(f"  - {error}")
    else:
        logger.info("✓ All bills generated successfully!")

