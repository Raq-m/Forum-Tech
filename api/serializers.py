from django.contrib.auth import get_user_model
from rest_framework import serializers

from forum.models import Tag, Thread, ThreadVote
from forum.validators import validate_forum_content


class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username"]
        read_only_fields = fields


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]
        read_only_fields = fields


class ThreadSerializer(serializers.ModelSerializer):
    author = PublicUserSerializer(read_only=True)
    tags_detail = TagSerializer(source="tags", many=True, read_only=True)
    puntuacion = serializers.IntegerField(read_only=True)
    num_respuestas = serializers.IntegerField(read_only=True)
    esta_resuelto = serializers.BooleanField(read_only=True)

    class Meta:
        model = Thread
        fields = [
            "id", "author", "title", "content", "tags", "tags_detail",
            "views_count", "puntuacion", "num_respuestas", "esta_resuelto",
            "is_locked", "accepted_reply", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "views_count", "is_locked", "accepted_reply", "created_at", "updated_at",
        ]

    def validate_title(self, value):
        validate_forum_content(value)
        return value

    def validate_content(self, value):
        validate_forum_content(value)
        return value

    def validate(self, attrs):
        # Valida también el estado final de un PATCH parcial.
        title = attrs.get("title", getattr(self.instance, "title", ""))
        content = attrs.get("content", getattr(self.instance, "content", ""))
        validate_forum_content(f"{title}\n{content}")
        return attrs


class VoteInputSerializer(serializers.Serializer):
    value = serializers.ChoiceField(choices=[-1, 0, 1])


class VoteResultSerializer(serializers.Serializer):
    score = serializers.IntegerField()
    user_vote = serializers.IntegerField()


class ThreadVoteSerializer(serializers.ModelSerializer):
    thread = ThreadSerializer(read_only=True)

    class Meta:
        model = ThreadVote
        fields = ["id", "thread", "value", "created_at"]
        read_only_fields = fields


class MessageSerializer(serializers.Serializer):
    message = serializers.CharField()


class StatsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    media_respuestas = serializers.FloatField(allow_null=True)
    minimo_visitas = serializers.IntegerField(allow_null=True)
    maximo_visitas = serializers.IntegerField(allow_null=True)
