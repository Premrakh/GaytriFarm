from django.core.management.base import BaseCommand
from dairy.tasks import auto_order_create


class Command(BaseCommand):
    help = 'Automatically create 3-month bulk orders for customers with cache orders'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting automatic order creation...'))
        
        try:
            auto_order_create()
            self.stdout.write(self.style.SUCCESS('✅ Automatic orders created successfully!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creating automatic orders: {str(e)}'))
            raise
