import re

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Notification, Reply, ReplyVote, Thread


MENTION_PATTERN = re.compile(r"(?<![\w@])@([\w.+-]+)")


def notify_mentions(instance, thread, reply=None, exclude_ids=()):
    names = {
        match.casefold()
        for match in MENTION_PATTERN.findall(instance.content)
    }

    if not names:
        return

    query = Q()
    for name in names:
        query |= Q(username__iexact=name)

    database = instance._state.db
    excluded = set(exclude_ids)
    excluded.add(instance.author_id)

    recipients = (
        get_user_model().objects.using(database)
        .filter(query, is_active=True)
        .exclude(pk__in=excluded)
        .distinct()
    )

    for recipient in recipients:
        Notification.objects.using(database).create(
            recipient=recipient,
            actor_id=instance.author_id,
            thread=thread,
            reply=reply,
            kind=Notification.Kind.MENTION,
        )


@receiver(
    post_save,
    sender=Thread,
    dispatch_uid="forum.notify_thread_mentions",
)
def notify_thread_mentions(
    sender, instance, created, raw=False, **kwargs
):
    if raw or not created:
        return

    notify_mentions(instance, thread=instance)


@receiver(
    post_save,
    sender=Reply,
    dispatch_uid="forum.notify_thread_reply",
)
def notify_thread_reply(
    sender, instance, created, raw=False, **kwargs
):
    if raw or not created:
        return

    thread = instance.thread

    if instance.author_id != thread.author_id:
        Notification.objects.using(instance._state.db).create(
            recipient_id=thread.author_id,
            actor_id=instance.author_id,
            thread=thread,
            reply=instance,
            kind=Notification.Kind.REPLY,
        )

    notify_mentions(
        instance,
        thread=thread,
        reply=instance,
        exclude_ids=(thread.author_id,),
    )


@receiver(
    pre_save,
    sender=ReplyVote,
    dispatch_uid="forum.remember_reply_vote",
)
def remember_reply_vote(
    sender, instance, raw=False, using=None, **kwargs
):
    if raw:
        return

    instance._previous_value = None

    if instance.pk:
        instance._previous_value = (
            sender.objects.using(using)
            .filter(pk=instance.pk)
            .values_list("value", flat=True)
            .first()
        )


@receiver(
    post_save,
    sender=ReplyVote,
    dispatch_uid="forum.notify_positive_reply_vote",
)
def notify_positive_reply_vote(
    sender, instance, raw=False, using=None, **kwargs
):
    if raw:
        return

    if instance.value != ReplyVote.Value.UP:
        return

    if getattr(instance, "_previous_value", None) == ReplyVote.Value.UP:
        return

    reply = instance.reply

    if instance.user_id == reply.author_id:
        return

    Notification.objects.using(using).create(
        recipient_id=reply.author_id,
        actor_id=instance.user_id,
        thread_id=reply.thread_id,
        reply_id=reply.pk,
        kind=Notification.Kind.VOTE,
    )


@receiver(
    post_save,
    sender=Notification,
    dispatch_uid="forum.publish_notification",
)
def publish_notification(
    sender, instance, created, raw=False, using=None, **kwargs
):
    if raw or not created:
        return

    recipient_id = instance.recipient_id
    notification_id = instance.pk

    def send_event():
        channel_layer = get_channel_layer()

        if channel_layer is None:
            return

        async_to_sync(channel_layer.group_send)(
            f"notifications.user.{recipient_id}",
            {
                "type": "notification.created",
                "notification_id": notification_id,
            },
        )

    transaction.on_commit(send_event, using=using)