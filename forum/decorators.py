from functools import wraps

from django.http import HttpResponseForbidden


def suspension_required_clear(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and request.user.is_suspended
        ):
            return HttpResponseForbidden(
                "Tu cuenta esta suspendida temporalmente."
            )

        return view_func(request, *args, **kwargs)

    return wrapped
