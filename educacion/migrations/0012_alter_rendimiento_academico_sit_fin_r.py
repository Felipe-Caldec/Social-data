# Generated by Django 4.2.18 on 2025-04-10 19:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('educacion', '0011_alter_rendimiento_academico_prom_gral'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rendimiento_academico',
            name='SIT_FIN_R',
            field=models.CharField(null=True),
        ),
    ]
