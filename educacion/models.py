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

class resultados_simce(models.Model):

    agno= models.IntegerField()
    grado = models.CharField()
    cod_reg = models.IntegerField()
    nom_reg = models.CharField()
    prom_lect_reg = models.IntegerField()
    prom_mate_reg = models.IntegerField()
    dif_lect_reg = models.IntegerField()
    dif_mate_reg = models.IntegerField()
    sigdif_lect_reg = models.IntegerField()
    sigdif_mate_reg = models.IntegerField()

class resultados_simce_idps(models.Model):

    rbd = models.IntegerField()
    agno = models.IntegerField()
    grado = models.IntegerField()
    ind = models.CharField()
    dim = models.CharField()
    prom = models.IntegerField(null=True)
    nom_rbd = models.CharField()
    cod_reg_rbd = models.IntegerField()
    nom_reg_rbd = models.CharField()
    cod_pro_rbd = models.IntegerField()
    nom_pro_rbd = models.CharField()
    cod_com_rbd = models.IntegerField()
    nom_com_rbd = models.CharField()
    nom_deprov_rbd = models.CharField()
    cod_depe2 = models.IntegerField()
    cod_grupo = models.IntegerField(null=True)
    cod_rural_rbd = models.IntegerField()