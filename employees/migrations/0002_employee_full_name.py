from django.db import migrations


class Migration(migrations.Migration):

    atomic = False  # required: can't mix DDL and DML in same PostgreSQL transaction

    dependencies = [
        ('employees', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE "Employees" ADD COLUMN full_name VARCHAR(255) NOT NULL DEFAULT \'\'',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="""
                UPDATE "Employees"
                SET full_name = TRIM(REGEXP_REPLACE(
                    first_name || ' ' || COALESCE(NULLIF(middle_name, ''), '') || ' ' || last_name,
                    '\\s+', ' ', 'g'
                ))
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql='ALTER TABLE "Employees" DROP COLUMN first_name',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql='ALTER TABLE "Employees" DROP COLUMN middle_name',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql='ALTER TABLE "Employees" DROP COLUMN last_name',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql='ALTER TABLE "Employees" ALTER COLUMN full_name DROP DEFAULT',
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
