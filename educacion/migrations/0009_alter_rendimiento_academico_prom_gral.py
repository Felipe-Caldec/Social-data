# Generated by Django 4.2.18 on 2025-03-31 15:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('educacion', '0008_rendimiento_academico'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rendimiento_academico',
            name='PROM_GRAL',
            field=models.DecimalField(decimal_places=2, max_digits=3, null=True),
        ),
    ]
