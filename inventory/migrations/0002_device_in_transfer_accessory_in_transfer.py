from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='in_transfer',
            field=models.BooleanField(default=False, help_text='True while a pending site transfer is in progress'),
        ),
        migrations.AddField(
            model_name='accessory',
            name='in_transfer',
            field=models.BooleanField(default=False, help_text='True while a pending site transfer is in progress'),
        ),
    ]
