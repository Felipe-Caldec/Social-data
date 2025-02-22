from django import forms

class Estudiantes_filtro(forms.Form):

    gen_alu_choices = [
        ('', 'Seleccione Género'),
        (1, "Hombre"),
        (2, "Mujer"),
    ]

    nom_reg_estab_choices = [
        ('', 'Seleccione Región'),
        ('REGIÓN METROPOLITANA DE SANTIAGO', 'REGIÓN METROPOLITANA DE SANTIAGO'),
        ('REGIÓN DE MAGALLANES Y DE LA ANTÁRTICA CHILENA','REGIÓN DE MAGALLANES Y DE LA ANTÁRTICA CHILENA'),
        ('REGIÓN DE ANTOFAGASTA','REGIÓN DE ANTOFAGASTA'),
        ('REGIÓN DE ARICA Y PARINACOTA','REGIÓN DE ARICA Y PARINACOTA'),
        ('REGIÓN DE ATACAMA','REGIÓN DE ATACAMA'),
        ('REGIÓN DE AYSÉN DEL GRAL. CARLOS IBÁÑEZ DEL CAMPO','REGIÓN DE AYSÉN DEL GRAL. CARLOS IBÁÑEZ DEL CAMPO'),
        ('REGIÓN DE COQUIMBO','REGIÓN DE COQUIMBO'),
        ('REGIÓN DE LA ARAUCANÍA','REGIÓN DE LA ARAUCANÍA'),
        ('REGIÓN DE LOS LAGOS','REGIÓN DE LOS LAGOS'),
        ('REGIÓN DE LOS RÍOS','REGIÓN DE LOS RÍOS'),
        ('REGIÓN DE ÑUBLE','REGIÓN DE ÑUBLE'),
        ('REGIÓN DE TARAPACÁ','REGIÓN DE TARAPACÁ'),
        ('REGIÓN DE VALPARAÍSO','REGIÓN DE VALPARAÍSO'),
        ('REGIÓN DEL BIOBÍO','REGIÓN DEL BIOBÍO'),
        ("REGIÓN DEL LIBERTADOR GRAL. BERNARDO O'HIGGINS","REGIÓN DEL LIBERTADOR GRAL. BERNARDO O'HIGGINS"),
        ('REGIÓN DEL MAULE', 'REGIÓN DEL MAULE')
    ]
    

    gen_alu = forms.ChoiceField(choices=gen_alu_choices, required=False, label="Género")
    nom_reg_estab = forms.ChoiceField(choices=nom_reg_estab_choices, required=False, label="Región")