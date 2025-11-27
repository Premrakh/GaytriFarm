import logging
from celery import shared_task
from django.utils import timezone
from django.db.models import Sum , F, ExpressionWrapper, IntegerField
from django.core.files.base import ContentFile
from django.db import transaction

from user.models import User
from .models import Order, UserBill, DistributorOrder
from twilio.rest import Client
from .pdf_generator import generate_bill_pdf
import os
from django.conf import settings

logger = logging.getLogger(__name__)

def send_bills_via_whatsapp(link):
    account_sid = 'AC26610f13a08e3b009186451510156c33'
    auth_token = 'ff1a0af8875e113819125a42f03fadfc'
    client = Client(account_sid, auth_token)

    body = (
    "📅 *GayatriFarm - Monthly Bill*\n\n"
    "{{link}}\n\n"
    "⚠️ Note: This link will expire in *24 hours*, so please download your bill before it expires.\n\n"
    "Thank you for staying with us! 💚"
    )

    message = client.messages.create(
    from_='whatsapp:+14155238886',
    # content_sid='HXb5b62575e6e4ff6129ad7c8efe1f983e',
    # content_variables='{"1":"12/1","2":"3pm"}',
    body=body.replace("{{link}}", link),
    to='whatsapp:+918980275047'
    )

@shared_task()
def generate_monthly_bills_task():
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
                .values('quantity',product_name=F("product__name"),unit_price=F("product__price"))
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
            pdf_path = os.path.join("bills", pdf_filename)
            # save this file to the media directory
            with open(pdf_path, "wb") as pdf_file:
                pdf_file.write(pdf_content.read())
            user_bills.append(UserBill(user=customer,total_product=total_items,total_amount=grand_total))

            #send bill link to whatsapp
            normalized_path = pdf_path.replace("\\", "/")
            link = f"{settings.BACKEND_URL}/{normalized_path}"
            send_bills_via_whatsapp(link)
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
            logger.info(f"⛔ No customer orders today for distributor {distributor.user_id}, skipping.")
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
