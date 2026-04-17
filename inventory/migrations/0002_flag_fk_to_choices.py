"""
Migration: replace Flag FK on Device/Accessory with DeviceFlag CharField choices.

Steps:
  1. Add flag_char (CharField, nullable) to Device and Accessory.
  2. Data-migrate: map old FK name → choice key.
  3. Remove old flag FK columns.
  4. Rename flag_char → flag.
  5. Delete Flag model.
"""

from django.db import migrations, models


FLAG_NAME_MAP = {
    'available':         'available',
    'assigned':          'assigned',
    'lost':              'lost',
    'retired':           'retired',
    'under maintenance': 'under_maintenance',
}
DEFAULT_FLAG = 'available'


def migrate_flags_forward(apps, schema_editor):
    Device    = apps.get_model('inventory', 'Device')
    Accessory = apps.get_model('inventory', 'Accessory')
    Flag      = apps.get_model('inventory', 'Flag')

    flag_map = {}
    for f in Flag.objects.all():
        flag_map[f.pk] = FLAG_NAME_MAP.get(f.name.lower(), DEFAULT_FLAG)

    for d in Device.objects.all():
        d.flag_char = flag_map.get(d.flag_id, DEFAULT_FLAG)
        d.save(update_fields=['flag_char'])

    for a in Accessory.objects.all():
        a.flag_char = flag_map.get(a.flag_id, DEFAULT_FLAG)
        a.save(update_fields=['flag_char'])


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        # 1. Add temporary CharField columns
        migrations.AddField(
            model_name='device',
            name='flag_char',
            field=models.CharField(max_length=20, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='accessory',
            name='flag_char',
            field=models.CharField(max_length=20, null=True, blank=True),
        ),

        # 2. Data migration
        migrations.RunPython(migrate_flags_forward, migrations.RunPython.noop),

        # 3. Remove old FK columns
        migrations.RemoveField(model_name='device',    name='flag'),
        migrations.RemoveField(model_name='accessory', name='flag'),

        # 4. Rename flag_char → flag (with choices and default)
        migrations.RenameField(model_name='device',    old_name='flag_char', new_name='flag'),
        migrations.RenameField(model_name='accessory', old_name='flag_char', new_name='flag'),

        migrations.AlterField(
            model_name='device',
            name='flag',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('available',         'Available'),
                    ('assigned',          'Assigned'),
                    ('lost',              'Lost'),
                    ('retired',           'Retired'),
                    ('under_maintenance', 'Under Maintenance'),
                ],
                default='available',
            ),
        ),
        migrations.AlterField(
            model_name='accessory',
            name='flag',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('available',         'Available'),
                    ('assigned',          'Assigned'),
                    ('lost',              'Lost'),
                    ('retired',           'Retired'),
                    ('under_maintenance', 'Under Maintenance'),
                ],
                default='available',
            ),
        ),

        # 5. Delete Flag model
        migrations.DeleteModel(name='Flag'),
    ]
