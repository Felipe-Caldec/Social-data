from django.db import models


class matricula_parvulo (models.Model):

    agno = models.IntegerField()
    mes = models.IntegerField ()
    mrun = models.IntegerField()
    gen_alu = models.IntegerField()
    id_estab = models.IntegerField()
    nom_estab = models.CharField(max_length= 1000)
    cod_reg_estab = models.IntegerField(null=True)
    cod_pro_estab = models.IntegerField(null=True)
    cod_com_estab = models.IntegerField(null=True)
    nom_reg_estab = models.CharField(max_length=500, null=True)
    nom_reg_a_estab = models.CharField(max_length=20,null=True)
    nom_pro_estab = models.CharField(max_length=200,null=True)
    nom_com_estab = models.CharField(max_length=500,null=True)
    cod_deprov_estab = models.IntegerField(null=True)
    nom_deprov_estab = models.CharField(max_length=200, null=True)
    rural_estab = models.IntegerField(null=True)
    dependencia = models.IntegerField(null=True)
    nivel1 = models.IntegerField(null=True)
    cod_ense1_m = models.IntegerField(null=True)
    cod_ense2_m = models.IntegerField(null=True)
