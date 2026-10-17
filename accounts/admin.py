from datetime import timedelta

from django.contrib import admin
from django.utils import timezone

from .models import User


@admin.register(User)
class UserModerationAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "suspended_until",
        "suspension_active",
    )
    search_fields = ("username",)
    readonly_fields = ("username",)
    fields = ("username", "suspended_until")
    actions = ("suspend_one_day", "lift_suspension")

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            is_staff=False,
            is_superuser=False,
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(
        boolean=True,
        description="Suspension activa",
    )
    def suspension_active(self, obj):
        return obj.is_suspended

    @admin.action(
        description="Suspender durante 24 horas desde ahora",
        permissions=["change"],
    )
    def suspend_one_day(self, request, queryset):
        updated = queryset.update(
            suspended_until=timezone.now() + timedelta(days=1),
        )
        self.message_user(
            request,
            f"Usuarios suspendidos: {updated}",
        )

    @admin.action(
        description="Levantar suspension",
        permissions=["change"],
    )
    def lift_suspension(self, request, queryset):
        updated = queryset.update(suspended_until=None)
        self.message_user(
            request,
            f"Suspensiones retiradas: {updated}",
        )
        