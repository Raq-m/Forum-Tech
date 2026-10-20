from django.urls import path

from . import views

app_name = "forum"

urlpatterns = [
    path(
        "threads/<int:pk>/",
        views.thread_detail,
        name="thread_detail",
    ),
    path(
        "threads/<int:pk>/vote/",
        views.vote_thread,
        name="vote_thread",
    ),
    path(
        "replies/<int:pk>/vote/",
        views.vote_reply,
        name="vote_reply",
    ),
        path(
        "notifications/",
        views.notification_list,
        name="notifications",
    ),
    path(
        "notifications/<int:pk>/read/",
        views.notification_mark_read,
        name="notification_mark_read",
    ),
        path(
        "threads/<int:pk>/report/",
        views.report_thread,
        name="report_thread",
    ),
    path(
        "replies/<int:pk>/report/",
        views.report_reply,
        name="report_reply",
    ),
        path(
        "threads/<int:pk>/reply/",
        views.reply_create,
        name="reply_create",
    ),
        path(
        "threads/<int:pk>/merge/",
        views.thread_merge,
        name="thread_merge",
    ),
]