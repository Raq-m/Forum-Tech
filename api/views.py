from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from forum.models import Tag, Thread, ThreadVote
from forum.search import hilos_visibles
from forum.services import archive_thread, record_thread_vote
from forum.statistics import resumen_foro
from .filters import ThreadFilter
from .permissions import IsActiveAuthorOrReadOnly, IsNotSuspended
from .serializers import (
    MessageSerializer, StatsSerializer, TagSerializer, ThreadSerializer,
    ThreadVoteSerializer, VoteInputSerializer, VoteResultSerializer,
)


def visible_threads():
    return hilos_visibles().prefetch_related("tags")


class HelloAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=MessageSerializer)
    def get(self, request):
        return Response({"message": "Forum Tech API v1"})


class ThreadViewSet(viewsets.ModelViewSet):
    serializer_class = ThreadSerializer
    permission_classes = [IsActiveAuthorOrReadOnly]
    filterset_class = ThreadFilter
    search_fields = ["title", "content", "tags__name"]
    ordering_fields = ["created_at", "views_count", "puntuacion", "num_respuestas"]
    ordering = ["-created_at", "-pk"]

    def get_queryset(self):
        return visible_threads()

    def perform_create(self, serializer):
        with transaction.atomic():
            serializer.save(author=self.request.user)
            serializer.instance = visible_threads().get(pk=serializer.instance.pk)

    def perform_update(self, serializer):
        with transaction.atomic():
            current = get_object_or_404(
                Thread.objects.select_for_update(), pk=serializer.instance.pk,
                is_deleted=False, merged_into__isnull=True,
            )
            self.check_object_permissions(self.request, current)
            serializer.instance = current
            serializer.save()
            serializer.instance = visible_threads().get(pk=current.pk)

    def perform_destroy(self, instance):
        try:
            archive_thread(instance.pk, self.request.user)
        except DjangoValidationError as error:
            raise ValidationError(error.messages) from error

    def paginated_threads(self, queryset):
        page = self.paginate_queryset(self.filter_queryset(queryset))
        return self.get_paginated_response(self.get_serializer(page, many=True).data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def mine(self, request):
        return self.paginated_threads(self.get_queryset().filter(author=request.user))

    @extend_schema(responses=ThreadSerializer(many=True))
    @action(detail=True, methods=["get"])
    def similar(self, request, pk=None):
        thread = self.get_object()
        return self.paginated_threads(
            self.get_queryset().filter(tags__in=thread.tags.all()).exclude(pk=thread.pk).distinct()
        )

    @extend_schema(request=VoteInputSerializer, responses=VoteResultSerializer)
    @action(
        detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsNotSuspended],
        serializer_class=VoteInputSerializer,
    )
    def vote(self, request, pk=None):
        thread = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = record_thread_vote(thread, request.user, int(serializer.validated_data["value"]))
        except DjangoValidationError as error:
            raise ValidationError(error.messages) from error
        return Response(result)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all().order_by("name", "pk")
    serializer_class = TagSerializer
    search_fields = ["name"]
    ordering_fields = ["name"]


class ThreadVoteViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ThreadVoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = []

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ThreadVote.objects.none()
        return (
            ThreadVote.objects.filter(
                user=self.request.user, thread__is_deleted=False, thread__merged_into__isnull=True,
            )
            .prefetch_related(Prefetch("thread", queryset=visible_threads()))
            .order_by("-created_at", "-pk")
        )


class PopularThreadsAPIView(ListAPIView):
    serializer_class = ThreadSerializer
    filter_backends = []

    def get_queryset(self):
        return visible_threads().order_by("-puntuacion", "-views_count", "-pk")[:20]


class StatsAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=StatsSerializer)
    def get(self, request):
        return Response(resumen_foro())
