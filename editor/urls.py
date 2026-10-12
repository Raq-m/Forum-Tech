from django.urls import path

from . import views

app_name = "editor"

urlpatterns = [
    path("probar/", views.probar_editor, name="probar"),
    path("vista-previa/", views.vista_previa, name="vista_previa"),
    path("subir-imagen/", views.subir_imagen, name="subir_imagen"),
    path("previsualizar-enlace/", views.previsualizar_enlace, name="previsualizar_enlace"),
]