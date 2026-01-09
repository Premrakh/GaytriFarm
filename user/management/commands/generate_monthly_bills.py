from django.core.management.base import BaseCommand
from user.tasks import generate_monthly_bills_task


class Command(BaseCommand):
    help = 'Generate monthly bills for customers and distributors'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting monthly bill generation...'))
        
        try:
            generate_monthly_bills_task()
            self.stdout.write(self.style.SUCCESS('✅ Monthly bills generated successfully!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error generating bills: {str(e)}'))
            raise
