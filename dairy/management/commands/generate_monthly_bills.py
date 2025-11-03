from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import models
from django.core.mail import EmailMessage
from django.conf import settings
from user.models import User
from dairy.models import Order, UserBill
from dairy.pdf_generator import generate_bill_pdf


class Command(BaseCommand):
    help = 'Generate monthly bills for all customers, create PDFs, and send via email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-email',
            action='store_true',
            help='Skip sending emails',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        target_month = now.month - 1 if now.month > 1 else 12
        target_year = now.year if now.month > 1 else now.year - 1
            
        self.stdout.write(
            self.style.SUCCESS(
                f'Starting bill generation for {target_month}/{target_year}'
            )
        )
        
        # Get all customers
        customers = User.objects.filter(role=User.CUSTOMER,role_accepted=True)
        
        self.stdout.write(f'Found {customers.count()} customers with role_accepted=True')
        
        bills_created = 0
        bills_updated = 0
        emails_sent = 0
        errors = []
        
        for customer in customers:
            try:
                # Get all delivered orders for this customer in the target month
                orders = Order.objects.filter(
                    customer=customer,
                    status=Order.DELIVERED,
                    date__month=target_month,
                    date__year=target_year
                ).select_related('product').values(
                    'product__id',
                    'product__name',
                    'product__price'
                ).annotate(
                    total_quantity=models.Sum('quantity'),
                    total_amount=models.Sum('total_price')
                )
                # Skip if no orders
                if not orders:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠ No orders for {customer.user_name} in {target_month}/{target_year} - skipping'
                        )
                    )
                    continue
                
                self.stdout.write(f'Found {len(orders)} product(s) for {customer.user_name}')
                
                # Calculate totals
                grand_total = sum(order['total_amount'] for order in orders)
                total_items = sum(order['total_quantity'] for order in orders)
                
                # Build product-wise breakdown
                product_breakdown = [
                    {
                        "product_id": order['product__id'],
                        "product_name": order['product__name'],
                        "unit_price": order['product__price'],
                        "quantity": order['total_quantity'],
                        "total_amount": order['total_amount']
                    }
                    for order in orders
                ]
                
                # Create bill data structure
                bill_data = {
                    "customer_id": str(customer.user_id),
                    "customer_name": customer.user_name,
                    "billing_period": {
                        "month": target_month,
                        "year": target_year,
                        "month_name": timezone.datetime(target_year, target_month, 1).strftime('%B')
                    },
                    "total_items": total_items,
                    "total_amount": grand_total,
                    "product_breakdown": product_breakdown,
                    "generated_at": timezone.now().isoformat()
                }
                
                # Generate PDF
                self.stdout.write(f'Generating PDF for {customer.user_name}...')
                pdf_content = generate_bill_pdf(bill_data)
                pdf_filename = f"bill_{customer.user_name}_{target_month}_{target_year}.pdf"
                
                # Create or update UserBill record
                user_bill, created = UserBill.objects.get_or_create(
                    user=customer,
                    defaults={
                        'total_product': total_items,
                        'total_amount': grand_total,
                    }
                )
                
                if not created:
                    # Update existing bill
                    user_bill.total_product = total_items
                    user_bill.total_amount = grand_total
                    user_bill.save()
                
                # Save PDF file
                user_bill.pdf_file.save(pdf_filename, pdf_content, save=True)
                
                if created:
                    bills_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created bill for {customer.user_name}')
                    )
                else:
                    bills_updated += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Updated bill for {customer.user_name}')
                    )
                
                
                
            except Exception as e:
                error_msg = f"Bill generation failed for {customer.user_name}: {str(e)}"
                errors.append(error_msg)
                self.stdout.write(self.style.ERROR(f'✗ {error_msg}'))
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('BILL GENERATION SUMMARY'))
        self.stdout.write('='*50)
        self.stdout.write(f'Period: {target_month}/{target_year}')
        self.stdout.write(f'Bills Created: {bills_created}')
        self.stdout.write(f'Bills Updated: {bills_updated}')
        self.stdout.write(f'Total Bills: {bills_created + bills_updated}')

        if errors:
            self.stdout.write(self.style.ERROR(f'\nErrors: {len(errors)}'))
            for error in errors:
                self.stdout.write(self.style.ERROR(f'  - {error}'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ All bills generated successfully!'))
        
        self.stdout.write('='*50 + '\n')
