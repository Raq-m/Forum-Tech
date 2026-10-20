from django.contrib import admin

from .models import Reply, Report, Thread


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "reporter",
        "thread",
        "reply",
        "reason",
        "status",
        "created_at",
    )
    list_filter = ("status", "reason", "created_at")
    search_fields = (
        "reporter__username",
        "thread__title",
        "reply__content",
        "description",
    )
    list_select_related = ("reporter", "thread", "reply")
    readonly_fields = (
        "reporter",
        "thread",
        "reply",
        "reason",
        "description",
        "created_at",
    )
    fields = (
        "reporter",
        "thread",
        "reply",
        "reason",
        "description",
        "status",
        "created_at",
    )
    actions = ("mark_reviewed", "mark_dismissed")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.action(
        description="Marcar reportes como revisados",
        permissions=["change"],
    )
    def mark_reviewed(self, request, queryset):
        updated = queryset.update(status=Report.Status.REVIEWED)
        self.message_user(
            request,
            f"Reportes marcados como revisados: {updated}",
        )

    @admin.action(
        description="Descartar reportes",
        permissions=["change"],
    )
    def mark_dismissed(self, request, queryset):
        updated = queryset.update(status=Report.Status.DISMISSED)
        self.message_user(
            request,
            f"Reportes descartados: {updated}",
        )


class SoftDeleteAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.action(
        description="Ocultar publicaciones seleccionadas",
        permissions=["change"],
    )
    def hide_publications(self, request, queryset):
        updated = queryset.filter(
            is_deleted=False,
        ).update(is_deleted=True)

        self.message_user(
            request,
            f"Publicaciones ocultadas: {updated}",
        )

    @admin.action(
        description="Restaurar publicaciones seleccionadas",
        permissions=["change"],
    )
    def restore_publications(self, request, queryset):
        updated = queryset.filter(
            is_deleted=True,
        ).update(is_deleted=False)

        self.message_user(
            request,
            f"Publicaciones restauradas: {updated}",
        )


@admin.register(Thread)
class ThreadAdmin(SoftDeleteAdmin):
    list_display = (
        "title",
        "author",
        "is_locked",
        "is_deleted",
        "created_at",
    )
    list_filter = ("is_locked", "is_deleted")
    search_fields = ("title", "author__username")
    list_select_related = ("author",)
    readonly_fields = (
        "author",
        "title",
        "content",
        "created_at",
        "updated_at",
    )
    fields = (
        "author",
        "title",
        "content",
        "is_locked",
        "is_deleted",
        "created_at",
        "updated_at",
    )
    actions = (
        "lock_threads",
        "unlock_threads",
        "hide_publications",
        "restore_publications",
    )

    @admin.action(
        description="Bloquear hilos seleccionados",
        permissions=["change"],
    )
    def lock_threads(self, request, queryset):
        updated = queryset.filter(
            is_locked=False,
        ).update(is_locked=True)

        self.message_user(request, f"Hilos bloqueados: {updated}")

    @admin.action(
        description="Desbloquear hilos seleccionados",
        permissions=["change"],
    )
    def unlock_threads(self, request, queryset):
        updated = queryset.filter(
            is_locked=True,
        ).update(is_locked=False)

        self.message_user(request, f"Hilos desbloqueados: {updated}")


@admin.register(Reply)
class ReplyAdmin(SoftDeleteAdmin):
    list_display = (
        "id",
        "thread",
        "author",
        "is_deleted",
        "created_at",
    )
    list_filter = ("is_deleted",)
    search_fields = (
        "content",
        "author__username",
        "thread__title",
    )
    list_select_related = ("author", "thread")
    readonly_fields = (
        "thread",
        "author",
        "content",
        "created_at",
        "updated_at",
    )
    fields = (
        "thread",
        "author",
        "content",
        "is_deleted",
        "created_at",
        "updated_at",
    )
    actions = (
        "hide_publications",
        "restore_publications",
    )