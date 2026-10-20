from django import forms

from .models import Reply, Report, Thread
from .validators import validate_forum_content


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["reason", "description"]
        labels = {
            "reason": "Motivo del reporte",
            "description": "Detalles adicionales",
        }
        widgets = {
            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "maxlength": 2000,
                    "placeholder": "Explica brevemente el problema.",
                },
            ),
        }


class ReplyForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ["content"]
        labels = {
            "content": "Tu respuesta",
        }
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Escribe tu respuesta.",
                },
            ),
        }

    def clean_content(self):
        content = self.cleaned_data["content"]
        validate_forum_content(content)
        return content


class MergeThreadForm(forms.Form):
    target = forms.ModelChoiceField(
        queryset=Thread.objects.none(),
        label="Hilo de destino",
        empty_label="Selecciona el destino",
    )
    confirm = forms.BooleanField(
        label="Confirmo que quiero mover las respuestas al destino",
        required=True,
    )

    def __init__(self, *args, source, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["target"].queryset = (
            Thread.objects
            .filter(
                is_deleted=False,
                is_locked=False,
                merged_into__isnull=True,
            )
            .exclude(pk=source.pk)
            .order_by("title", "pk")
        )
        # Valores de demostracion para comprobar el filtro.
FORUM_BLOCKED_WORDS = [
    "spamdemostracion",
]

FORUM_BLOCKED_DOMAINS = [
    "spam.example",
]