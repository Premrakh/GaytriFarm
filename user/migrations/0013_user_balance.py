# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0012_userbill'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='balance',
            field=models.IntegerField(default=0, help_text='Customer balance: payments - delivered orders'),
        ),
    ]

