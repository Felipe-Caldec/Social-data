# Generated by Django 4.2.18 on 2025-03-17 21:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('educacion', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resultados_simce_idps',
            name='cod_grupo',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='resultados_simce_idps',
            name='prom',
            field=models.IntegerField(null=True),
        ),
    ]
