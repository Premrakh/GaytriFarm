from django.core.management.base import BaseCommand
from dairy.tasks import create_daily_distributor_orders


class Command(BaseCommand):
    help = 'Create daily distributor orders based on customer orders'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting daily distributor order creation...'))
        
        try:
            create_daily_distributor_orders()
            self.stdout.write(self.style.SUCCESS('✅ Daily distributor orders created successfully!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creating distributor orders: {str(e)}'))
            raise
