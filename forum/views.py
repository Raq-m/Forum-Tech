from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import IntegerField, Prefetch, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .decorators import suspension_required_clear
from .forms import MergeThreadForm, ReplyForm, ReportForm
from .models import (
    Notification,
    Reply,
    ReplyVote,
    Report,
    Thread,
    ThreadVote,
)
from .services import merge_threads


def save_vote(request, publication, vote_model, relation):
    value = request.POST.get("value")

    if value not in {"1", "-1", "0"}:
        return JsonResponse(
            {"error": "El valor debe ser 1, -1 o 0."},
            status=400,
        )

    value = int(value)
    lookup = {
        relation: publication,
        "user": request.user,
    }

    if value == 0:
        vote_model.objects.filter(**lookup).delete()
    else:
        vote_model.objects.update_or_create(
            **lookup,
            defaults={"value": value},
        )

    score = publication.votes.aggregate(
        total=Sum("value"),
    )["total"] or 0

    return JsonResponse({
        "score": score,
        "user_vote": value,
    })


@login_required
@suspension_required_clear
@require_POST
def vote_thread(request, pk):
    thread = get_object_or_404(
        Thread,
        pk=pk,
        is_deleted=False,
        merged_into__isnull=True,
    )

    return save_vote(request, thread, ThreadVote, "thread")


@login_required
@suspension_required_clear
@require_POST
def vote_reply(request, pk):
    reply = get_object_or_404(
        Reply,
        pk=pk,
        is_deleted=False,
        thread__is_deleted=False,
        thread__merged_into__isnull=True,
    )

    return save_vote(request, reply, ReplyVote, "reply")


def thread_detail(request, pk):
    replies = (
        Reply.objects
        .filter(is_deleted=False)
        .select_related("author")
        .annotate(
            score=Coalesce(
                Sum("votes__value"),
                Value(0),
                output_field=IntegerField(),
            ),
        )
    )

    threads = (
        Thread.objects
        .select_related("author")
        .annotate(
            score=Coalesce(
                Sum("votes__value"),
                Value(0),
                output_field=IntegerField(),
            ),
        )
        .prefetch_related(
            Prefetch("replies", queryset=replies),
        )
    )

    thread = get_object_or_404(
        threads,
        pk=pk,
        is_deleted=False,
    )

    if thread.merged_into_id:
        return redirect(
            "forum:thread_detail",
            pk=thread.merged_into_id,
        )

    return render(
        request,
        "forum/thread_detail.html",
        {"thread": thread},
    )


@login_required
@suspension_required_clear
@require_POST
def reply_create(request, pk):
    with transaction.atomic():
        thread = get_object_or_404(
            Thread.objects.select_for_update(),
            pk=pk,
            is_deleted=False,
            merged_into__isnull=True,
        )

        if thread.is_locked:
            return HttpResponseForbidden(
                "Este hilo esta bloqueado y no admite respuestas."
            )

        form = ReplyForm(request.POST)

        if form.is_valid():
            reply = form.save(commit=False)
            reply.thread = thread
            reply.author = request.user
            reply.save()

            return redirect(
                "forum:thread_detail",
                pk=thread.pk,
            )

    return render(
        request,
        "forum/reply_form.html",
        {
            "form": form,
            "thread": thread,
        },
        status=400,
    )


@login_required
def notification_list(request):
    notifications = (
        Notification.objects
        .filter(recipient=request.user)
        .select_related("actor", "thread", "reply")
    )

    return render(
        request,
        "forum/notifications.html",
        {"notifications": notifications},
    )


@login_required
@require_POST
def notification_mark_read(request, pk):
    notification = get_object_or_404(
        Notification,
        pk=pk,
        recipient=request.user,
    )

    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=["is_read"])

    return redirect("forum:notifications")


def report_publication(request, publication, relation, thread):
    lookup = {
        "reporter": request.user,
        relation: publication,
    }

    existing_report = Report.objects.filter(**lookup).first()

    form = ReportForm(
        request.POST if request.method == "POST" else None,
    )

    if existing_report is None:
        if request.method == "POST" and form.is_valid():
            Report.objects.get_or_create(
                **lookup,
                defaults={
                    "reason": form.cleaned_data["reason"],
                    "description": form.cleaned_data["description"],
                },
            )

            return redirect(
                "forum:thread_detail",
                pk=thread.pk,
            )

    return render(
        request,
        "forum/report_form.html",
        {
            "form": form,
            "thread": thread,
            "existing_report": existing_report,
        },
    )


@login_required
@suspension_required_clear
def report_thread(request, pk):
    thread = get_object_or_404(
        Thread,
        pk=pk,
        is_deleted=False,
        merged_into__isnull=True,
    )

    return report_publication(
        request,
        thread,
        "thread",
        thread,
    )


@login_required
@suspension_required_clear
def report_reply(request, pk):
    reply = get_object_or_404(
        Reply.objects.select_related("thread"),
        pk=pk,
        is_deleted=False,
        thread__is_deleted=False,
        thread__merged_into__isnull=True,
    )

    return report_publication(
        request,
        reply,
        "reply",
        reply.thread,
    )


@login_required
@suspension_required_clear
@permission_required("forum.change_thread", raise_exception=True)
def thread_merge(request, pk):
    source = get_object_or_404(
        Thread,
        pk=pk,
        is_deleted=False,
        merged_into__isnull=True,
    )

    form = MergeThreadForm(
        request.POST if request.method == "POST" else None,
        source=source,
    )

    if request.method == "POST" and form.is_valid():
        target = form.cleaned_data["target"]

        try:
            merge_threads(source.pk, target.pk)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            return redirect(
                "forum:thread_detail",
                pk=target.pk,
            )

    return render(
        request,
        "forum/thread_merge.html",
        {
            "form": form,
            "source": source,
        },
    )