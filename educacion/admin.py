from django.contrib import admin
from .models import matricula_parvulo, matricula_basica, matricula_media
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save


class MatriculaParvuloResource(resources.ModelResource):
    class Meta:
        model = matricula_parvulo
        skip_unchanged = True  # Evita reimportar registros sin cambios
        use_bulk = False  # Inserción masiva para mayor eficiencia, en TRUE duplica importacion
        # chunk_size = 500 duplica importacion

    def before_import(self, dataset, **kwargs):
        existing_records = set(matricula_parvulo.objects.values_list("mrun", "agno"))
        new_records = set((row["mrun"], row["agno"]) for row in dataset.dict)

        if new_records & existing_records:
            raise ValidationError("Algunos registros ya existen en la base de datos. Revisa el archivo antes de importar.")

        

    def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):
        print(f"Dry Run: {dry_run}")  # Para verificar si está en ejecución real
        if not dry_run:  # Solo ejecuta en importación real
            for row in dataset.dict:  # Itera sobre cada fila del dataset
                print("Fila procesada:", row)  # Verifica la fila antes de insertarla

            


@admin.register(matricula_parvulo)
class MatriculaParvuloAdmin(ImportExportModelAdmin):
    resource_class = MatriculaParvuloResource
    list_display = ('agno', 'mrun', 'gen_alu', 'nom_reg_estab','nom_com_estab')
    list_filter = ('agno', 'cod_reg_estab')

    def get_import_formats(self):
        formats = super().get_import_formats()
        for fmt in formats:
            fmt.can_preview = False  # Desactiva la previsualización
        return formats


############## EDUCACION BASICA ##################################

    
class MatriculaBasicaResource(resources.ModelResource):
    class Meta:
        model = matricula_basica
        skip_unchanged = True  # Evita reimportar registros sin cambios
        use_bulk = False  # Inserción masiva para mayor eficiencia, en TRUE duplica importacion
        # chunk_size = 500 duplica importacion

    def before_import(self, dataset, **kwargs):
        existing_records = set(matricula_basica.objects.values_list("MRUN", "AGNO"))
        new_records = set((row["MRUN"], row["AGNO"]) for row in dataset.dict)
        post_save.disconnect(sender=matricula_basica)

        if new_records & existing_records:
            raise ValidationError("Algunos registros ya existen en la base de datos. Revisa el archivo antes de importar.")

        
            


@admin.register(matricula_basica)
class MatriculaBasicaAdmin(ImportExportModelAdmin):
    resource_class = MatriculaBasicaResource
    list_display = ('AGNO', 'MRUN', 'GEN_ALU', 'NOM_REG_RBD_A', 'NOM_COM_RBD')
    list_filter = ('AGNO', 'COD_REG_RBD')

    def get_import_formats(self):
        formats = super().get_import_formats()
        for format_instance in formats:
            if hasattr(format_instance, "can_preview"):
                format_instance.can_preview = False  # Desactiva la previsualización
        return formats

    def get_skip_confirmation(self, request, *args, **kwargs):
        """Omite la confirmación antes de la importación."""
        return True
    

############## EDUCACION MEDIA ##################################

    
class MatriculaMediaResource(resources.ModelResource):
    class Meta:
        model = matricula_media
        skip_unchanged = True  # Evita reimportar registros sin cambios
        use_bulk = False  # Inserción masiva para mayor eficiencia, en TRUE duplica importacion
        # chunk_size = 500 duplica importacion

    def before_import(self, dataset, **kwargs):
        existing_records = set(matricula_basica.objects.values_list("MRUN", "AGNO"))
        new_records = set((row["MRUN"], row["AGNO"]) for row in dataset.dict)
        post_save.disconnect(sender=matricula_media)

        if new_records & existing_records:
            raise ValidationError("Algunos registros ya existen en la base de datos. Revisa el archivo antes de importar.")

        
        

@admin.register(matricula_media)
class MatriculaMediaAdmin(ImportExportModelAdmin):
    resource_class = MatriculaMediaResource
    list_display = ('AGNO', 'MRUN', 'GEN_ALU', 'NOM_REG_RBD_A', 'NOM_COM_RBD')
    list_filter = ('AGNO', 'COD_REG_RBD')

    def get_import_formats(self):
        formats = super().get_import_formats()
        for format_instance in formats:
            if hasattr(format_instance, "can_preview"):
                format_instance.can_preview = False  # Desactiva la previsualización
        return formats

    def get_skip_confirmation(self, request, *args, **kwargs):
        """Omite la confirmación antes de la importación."""
        return True