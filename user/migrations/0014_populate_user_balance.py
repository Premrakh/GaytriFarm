# Generated manually - Data migration to populate initial balances

from django.db import migrations
from django.db.models import Sum


def populate_balances(apps, schema_editor):
    """
    Calculate and populate balance for all existing users based on:
    balance = payment_amount - delivered_orders_amount
    """
    User = apps.get_model('user', 'User')
    Payment = apps.get_model('user', 'Payment')
    Order = apps.get_model('dairy', 'Order')
    
    for user in User.objects.filter(role='customer'):
        # Calculate total payments
        payment_amount = Payment.objects.filter(user=user).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Calculate total delivered orders
        bill_amount = Order.objects.filter(
            customer=user,
            status='delivered'
        ).aggregate(total=Sum('total_price'))['total'] or 0
        
        # Set balance
        balance = payment_amount - bill_amount
        user.balance = balance
        user.save(update_fields=['balance'])


def reverse_populate_balances(apps, schema_editor):
    """Reset all balances to 0"""
    User = apps.get_model('user', 'User')
    User.objects.all().update(balance=0)


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0013_user_balance'),
        ('dairy', '0009_delete_userbill'),  # Ensure Order model exists
    ]

    operations = [
        migrations.RunPython(populate_balances, reverse_populate_balances),
    ]

