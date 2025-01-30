from django import forms

from django.core.exceptions import ValidationError


AFPS = [("AFP Capital","AFP Capital"), ("AFP Cuprum","AFP Cuprum"), 
        ("AFP Habitat","AFP Habitat"), ("AFP Modelo","AFP Modelo"), 
        ("AFP Planvital","AFP Planvital"), ("AFP Provida","AFP Provida"), 
        ("AFP Uno","AFP Uno")]

MULTIFONDOS = [("A","A"),("B","B"),("C","C"),("D","D"),("E","E")]


def validar_renta (value):
    if value < 400000:
        raise ValidationError("La renta ingresada debe ser superior a 400.000")
    
def validar_ahorro (value):
    if value < 1000000:
        raise ValidationError("El ahorro debe ser superior a 1.000.000")


class Cal_Rentabi_Forms(forms.Form):

    Renta_Mensual = forms.IntegerField(help_text="Ingresa el monto sin puntos",
                                       validators=[validar_renta])
    Ahorro_Estimado = forms.IntegerField(help_text="Ingresa el monto sin puntos",  
                                         validators=[validar_ahorro])
    AFP = forms.TypedChoiceField(choices= AFPS)
    Multifondo= forms.TypedChoiceField(choices=MULTIFONDOS)
        