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

class matricula_basica (models.Model):

    AGNO = models.IntegerField()
    RBD = models.IntegerField(null=True)
    NOM_RBD = models.CharField(null=True)
    COD_REG_RBD = models.IntegerField(null=True)
    NOM_REG_RBD_A = models.CharField(null=True)
    COD_PRO_RBD = models.IntegerField(null=True)
    COD_COM_RBD = models.IntegerField(null=True)
    NOM_COM_RBD = models.CharField(null=True)
    COD_DEPROV_RBD = models.IntegerField(null=True)
    NOM_DEPROV_RBD = models.CharField(null=True)
    COD_DEPE2 = models.IntegerField(null=True)
    RURAL_RBD = models.IntegerField(null=True)
    COD_ENSE2 = models.IntegerField(null=True)
    COD_GRADO2 = models.IntegerField(null=True)
    MRUN = models.IntegerField(null=True)
    GEN_ALU = models.IntegerField(null=True)
    EDAD_ALU = models.IntegerField(null=True)
    COD_COM_ALU = models.IntegerField(null=True)
    NOM_COM_ALU = models.CharField(null=True)
    ENS = models.IntegerField(null=True)
    

class matricula_media (models.Model):

    
    AGNO = models.IntegerField()
    RBD = models.IntegerField(null=True)
    NOM_RBD = models.CharField(null=True)
    COD_REG_RBD = models.IntegerField(null=True)
    NOM_REG_RBD_A = models.CharField(null=True)
    COD_PRO_RBD = models.IntegerField(null=True)
    COD_COM_RBD = models.IntegerField(null=True)
    NOM_COM_RBD = models.CharField(null=True)
    COD_DEPROV_RBD = models.IntegerField(null=True)
    NOM_DEPROV_RBD = models.CharField(null=True)
    COD_DEPE2 = models.IntegerField(null=True)
    RURAL_RBD = models.IntegerField(null=True)
    COD_ENSE2 = models.IntegerField(null=True)
    COD_GRADO2 = models.IntegerField(null=True)
    MRUN = models.IntegerField(null=True)
    GEN_ALU = models.IntegerField(null=True)
    EDAD_ALU = models.IntegerField(null=True)
    COD_COM_ALU = models.IntegerField(null=True)
    NOM_COM_ALU = models.CharField(null=True)
    ENS = models.IntegerField(null=True)
    