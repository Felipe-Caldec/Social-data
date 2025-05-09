# Generated by Django 4.2.18 on 2025-03-31 12:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('educacion', '0007_rename_nom_reg_rbd_dotacion_docente_nom_reg_rbd_a_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='rendimiento_academico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('AGNO', models.IntegerField()),
                ('RBD', models.IntegerField(null=True)),
                ('NOM_RBD', models.CharField(null=True)),
                ('COD_REG_RBD', models.IntegerField(null=True)),
                ('COD_PRO_RBD', models.IntegerField(null=True)),
                ('COD_COM_RBD', models.IntegerField(null=True)),
                ('NOM_COM_RBD', models.CharField(null=True)),
                ('COD_DEPE2', models.IntegerField(null=True)),
                ('COD_DEPE', models.IntegerField(null=True)),
                ('RURAL_RBD', models.IntegerField(null=True)),
                ('GEN_ALU', models.IntegerField(null=True)),
                ('MRUN', models.IntegerField(null=True)),
                ('EDAD_ALU', models.IntegerField(null=True)),
                ('NOM_COM_ALU', models.CharField(null=True)),
                ('COD_JOR', models.IntegerField(null=True)),
                ('PROM_GRAL', models.IntegerField(null=True)),
                ('ASISTENCIA', models.IntegerField(null=True)),
                ('SIT_FIN_R', models.IntegerField(null=True)),
            ],
        ),
    ]
