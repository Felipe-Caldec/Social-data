# Generated by Django 5.1.6 on 2025-02-07 19:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('educacion', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='matricula_parvulo',
            name='cod_ense1_m',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='matricula_parvulo',
            name='cod_ense2_m',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='matricula_parvulo',
            name='nom_deprov_estab',
            field=models.CharField(max_length=200, null=True),
        ),
    ]
