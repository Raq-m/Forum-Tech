from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    HelloAPIView, PopularThreadsAPIView, StatsAPIView, TagViewSet,
    ThreadViewSet, ThreadVoteViewSet,
)

app_name = "api"
router = DefaultRouter()
router.register("threads", ThreadViewSet, basename="thread")
router.register("tags", TagViewSet, basename="tag")
router.register("votes", ThreadVoteViewSet, basename="vote")

urlpatterns = [
    path("hello/", HelloAPIView.as_view(), name="hello"),
    path("stats/", StatsAPIView.as_view(), name="stats"),
    path("threads/popular/", PopularThreadsAPIView.as_view(), name="popular-threads"),
] + router.urls
