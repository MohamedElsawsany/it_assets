import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assignments', '0001_initial'),
        ('inventory', '0002_device_in_transfer_accessory_in_transfer'),
        ('locations', '0001_initial'),
        ('accounts', '0002_initial'),
    ]

    operations = [
        # Add status + resolved fields to DeviceTransfer
        migrations.AddField(
            model_name='devicetransfer',
            name='status',
            field=models.CharField(
                choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')],
                default='pending',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='devicetransfer',
            name='resolved_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='resolved_device_transfers',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='devicetransfer',
            name='resolved_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        # Update the approve_transfer permission description
        migrations.AlterModelOptions(
            name='devicetransfer',
            options={'permissions': [('approve_transfer', 'Can approve or reject a pending device site transfer')]},
        ),
        # Create AccessoryTransfer model
        migrations.CreateModel(
            name='AccessoryTransfer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transfer_date', models.DateTimeField()),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')],
                    default='pending',
                    max_length=20,
                )),
                ('notes', models.TextField(blank=True, null=True)),
                ('resolved_date', models.DateTimeField(blank=True, null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('accessory', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='transfers',
                    to='inventory.accessory',
                )),
                ('from_site', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='outgoing_accessory_transfers',
                    to='locations.site',
                )),
                ('to_site', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='incoming_accessory_transfers',
                    to='locations.site',
                )),
                ('transferred_by', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='accessory_transfers',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('resolved_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='resolved_accessory_transfers',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'Accessory_Transfers',
            },
        ),
    ]
