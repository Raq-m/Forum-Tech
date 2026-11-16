from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("", views.inbox, name="inbox"),
    path("nuevo/<int:user_id>/", views.start_conversation, name="start"),
    path("<int:conversation_id>/", views.conversation_detail, name="detail"),
]