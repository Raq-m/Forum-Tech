from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .decorators import suspension_required_clear
from .models import Reply, UserFollow
from .solucion import aceptar_solucion

User = get_user_model()


@login_required
@suspension_required_clear
@require_POST
def accept_solution(request, pk):
    respuesta = get_object_or_404(
        Reply.objects.select_related("thread"),
        pk=pk,
        is_deleted=False,
        thread__is_deleted=False,
        thread__merged_into__isnull=True,
    )
    hilo = respuesta.thread
    try:
 
        aceptar_solucion(hilo, respuesta, request.user)
    except ValidationError:
        return HttpResponseBadRequest("La respuesta no es válida para este hilo.")
    return redirect("forum:thread_detail", pk=hilo.pk)


@login_required
@suspension_required_clear
@require_POST
def toggle_follow(request, username):
    objetivo = get_object_or_404(User, username=username)
    if objetivo == request.user:
        return HttpResponseBadRequest("No puedes seguirte a ti mismo.")

    relacion, creada = UserFollow.objects.get_or_create(
        follower=request.user, followed=objetivo
    )
    if not creada:
        relacion.delete()

    siguiente = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(
        siguiente,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        siguiente = reverse("forum:thread_list")
    return redirect(siguiente)