# Generated by Django 4.2.18 on 2025-04-01 11:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('educacion', '0010_alter_rendimiento_academico_prom_gral'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rendimiento_academico',
            name='PROM_GRAL',
            field=models.IntegerField(null=True),
        ),
    ]
