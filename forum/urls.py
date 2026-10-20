from django.urls import path

from . import views
from .views_busqueda import thread_list, thread_suggest
from .views_social import accept_solution, toggle_follow

app_name = "forum"

urlpatterns = [
    path("threads/", thread_list, name="thread_list"),
    path("threads/suggest/", thread_suggest, name="thread_suggest"),
    path("threads/<int:pk>/", views.thread_detail, name="thread_detail"),
    path("threads/<int:pk>/vote/", views.vote_thread, name="vote_thread"),
    path("replies/<int:pk>/vote/", views.vote_reply, name="vote_reply"),
    path("replies/<int:pk>/accept/", accept_solution, name="accept_solution"),
    path("users/<str:username>/follow/", toggle_follow, name="toggle_follow"),
    path("notifications/", views.notification_list, name="notifications"),
    path(
        "notifications/<int:pk>/read/",
        views.notification_mark_read,
        name="notification_mark_read",
    ),
    path("threads/<int:pk>/report/", views.report_thread, name="report_thread"),
    path("replies/<int:pk>/report/", views.report_reply, name="report_reply"),
    path("threads/<int:pk>/reply/", views.reply_create, name="reply_create"),
    path("threads/<int:pk>/merge/", views.thread_merge, name="thread_merge"),
]