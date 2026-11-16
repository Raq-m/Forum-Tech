from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import get_user_model
from .models import Conversation
from .services import get_or_create_conversation, mark_messages_as_read, send_message


@login_required
def inbox(request):
    conversations = (
        Conversation.objects.filter(
            Q(initiator=request.user) | Q(recipient=request.user)
        )
        .select_related("initiator", "recipient")
        .annotate(
            unread_count=Count(
                "messages",
                filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user),
            )
        )
    )

    items = []
    for conversation in conversations:
        if conversation.initiator == request.user:
            other = conversation.recipient
        else:
            other = conversation.initiator
        items.append(
            {
                "conversation": conversation,
                "other": other,
                "unread": conversation.unread_count,
            }
        )

    q = request.GET.get("q", "").strip()
    results = []
    if q:
        results = (
            get_user_model()
            .objects.filter(username__icontains=q, is_active=True)
            .exclude(pk=request.user.pk)[:10]
        )

    return render(
        request,
        "chat/inbox.html",
        {"items": items, "q": q, "results": results},
    )


@login_required
def start_conversation(request, user_id):
    try:
        conversation = get_or_create_conversation(request.user, user_id)
    except ValidationError as e:
        messages.error(request, e.messages[0])
        return redirect("chat:inbox")

    return redirect("chat:detail", conversation_id=conversation.pk)


@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, pk=conversation_id)

    if request.user not in (conversation.initiator, conversation.recipient):
        raise PermissionDenied

    if conversation.initiator == request.user:
        other = conversation.recipient
    else:
        other = conversation.initiator

    if request.method == "POST":
        try:
            send_message(request.user, conversation.pk, request.POST.get("text", ""))
        except ValidationError as e:
            messages.error(request, e.messages[0])
        return redirect("chat:detail", conversation_id=conversation.pk)

    mark_messages_as_read(conversation.pk, request.user)
    chat_messages = conversation.messages.select_related("sender")

    return render(
        request,
        "chat/conversation.html",
        {
            "conversation": conversation,
            "other": other,
            "chat_messages": chat_messages,
        },
    )