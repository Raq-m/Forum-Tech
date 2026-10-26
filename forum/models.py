from django.conf import settings
from django.db import models


class Thread(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="threads",
    )
    views_count = models.PositiveBigIntegerField(default=0)
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_deleted = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    merged_into = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="merged_threads",
        editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField(
        "Tag",
        blank=True,
        related_name="threads",
    )
    accepted_reply = models.ForeignKey(
        "Reply",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        editable=False,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_deleted", "-created_at"], name="thread_visible_date_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(merged_into=models.F("pk")),
                name="thread_cannot_merge_into_itself",
            ),
        ]

    def __str__(self):
        return self.title


class Reply(models.Model):
    thread = models.ForeignKey(
        Thread,
        on_delete=models.CASCADE,
        related_name="replies",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="replies",
    )
    content = models.TextField()
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Respuesta {self.pk} en {self.thread.title}"


class ReplyVote(models.Model):
    class Value(models.IntegerChoices):
        UP = 1, "Positivo"
        DOWN = -1, "Negativo"

    reply = models.ForeignKey(
        Reply,
        on_delete=models.CASCADE,
        related_name="votes",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reply_votes",
    )
    value = models.SmallIntegerField(choices=Value.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["reply", "user"],
                name="unique_reply_vote_per_user",
            ),
            models.CheckConstraint(
                condition=models.Q(value__in=[-1, 1]),
                name="reply_vote_value_valid",
            ),
        ]

    def __str__(self):
        return f"{self.user} - respuesta {self.reply_id} - {self.value}"


class ThreadVote(models.Model):
    class Value(models.IntegerChoices):
        UP = 1, "Positivo"
        DOWN = -1, "Negativo"

    thread = models.ForeignKey(
        Thread,
        on_delete=models.CASCADE,
        related_name="votes",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="thread_votes",
    )
    value = models.SmallIntegerField(choices=Value.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["thread", "user"],
                name="unique_thread_vote_per_user",
            ),
            models.CheckConstraint(
                condition=models.Q(value__in=[-1, 1]),
                name="thread_vote_value_valid",
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.thread} - {self.value}"


class Notification(models.Model):
    class Kind(models.TextChoices):
        REPLY = "reply", "Nueva respuesta"
        MENTION = "mention", "Mencion"
        VOTE = "vote", "Voto"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_notifications",
    )
    thread = models.ForeignKey(
        Thread,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    reply = models.ForeignKey(
        Reply,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    kind = models.CharField(
        max_length=20,
        choices=Kind.choices,
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
        ]

    def __str__(self):
        return f"{self.kind} para {self.recipient}"


class Report(models.Model):
    class Reason(models.TextChoices):
        SPAM = "spam", "Spam"
        INAPPROPRIATE = "inappropriate", "Conducta inapropiada"
        DUPLICATE = "duplicate", "Contenido duplicado"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        REVIEWED = "reviewed", "Revisado"
        DISMISSED = "dismissed", "Descartado"

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports",
    )
    thread = models.ForeignKey(
        Thread,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reports",
    )
    reply = models.ForeignKey(
        Reply,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reports",
    )
    reason = models.CharField(
        max_length=20,
        choices=Reason.choices,
    )
    description = models.TextField(
        max_length=2000,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(
                        thread__isnull=False,
                        reply__isnull=True,
                    )
                    | models.Q(
                        thread__isnull=True,
                        reply__isnull=False,
                    )
                ),
                name="report_exactly_one_target",
            ),
            models.UniqueConstraint(
                fields=["reporter", "thread"],
                condition=models.Q(thread__isnull=False),
                name="unique_report_per_user_thread",
            ),
            models.UniqueConstraint(
                fields=["reporter", "reply"],
                condition=models.Q(reply__isnull=False),
                name="unique_report_per_user_reply",
            ),
        ]

    def __str__(self):
        return f"Reporte {self.pk} - {self.get_reason_display()}"


class Tag(models.Model):
    name = models.CharField(max_length=30, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"#{self.name}"

    @classmethod
    def desde_texto(cls, texto):
        """'#Python, django' -> [Tag('python'), Tag('django')]"""
        nombres = {
            palabra.strip().lstrip("#").lower()
            for palabra in (texto or "").replace(",", " ").split()
        }
        return [
            cls.objects.get_or_create(name=nombre)[0]
            for nombre in sorted(nombres)
            if nombre and len(nombre) <= 30
        ]


class UserFollow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="follows_given",
    )
    followed = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="follows_received",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "followed"],
                name="unique_follow_per_pair",
            ),
            models.CheckConstraint(
                condition=~models.Q(follower=models.F("followed")),
                name="cannot_follow_yourself",
            ),
        ]

    def __str__(self):
        return f"{self.follower} sigue a {self.followed}"