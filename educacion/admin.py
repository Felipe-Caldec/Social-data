from django.contrib import admin
from .models import matricula_parvulo
from import_export import resources
from import_export.admin import ImportExportModelAdmin

class MatriculaParvuloResource(resources.ModelResource):
    class Meta:
        model = matricula_parvulo
        skip_unchanged = True  # Evita reimportar registros sin cambios
        use_bulk = True  # Inserción masiva para mayor eficiencia
        chunk_size = 500 

    def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):
        if not dry_run:  # Solo ejecuta en importación real
            matriculas = [
                matricula_parvulo(**row) for row in dataset.dict()
            ]
            matricula_parvulo.objects.bulk_create(matriculas, batch_size=500)


@admin.register(matricula_parvulo)
class MatriculaParvuloAdmin(ImportExportModelAdmin):
    resource_class = MatriculaParvuloResource
    list_display = ('agno', 'mrun', 'gen_alu', 'nom_estab', 'id_estab','nom_com_estab')

    def get_import_formats(self):
        formats = super().get_import_formats()
        for fmt in formats:
            fmt.can_preview = False  # Desactiva la previsualización
        return formats
    


