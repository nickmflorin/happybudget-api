from rest_framework import serializers

from greenbudget.app.user.models import User
from greenbudget.app.user.serializers import SimpleUserSerializer

from .models import Comment


class CommentReplySerializer(serializers.ModelSerializer):
    text = serializers.CharField(allow_null=False, allow_blank=False)

    class Meta:
        model = Comment
        fields = ('text', )


class CommentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    text = serializers.CharField(allow_null=False, allow_blank=False)
    content_object_type = serializers.ChoiceField(
        read_only=True,
        choices=["budget", "account", "subaccount"]
    )
    object_id = serializers.IntegerField(read_only=True)
    likes = serializers.PrimaryKeyRelatedField(
        required=False,
        many=True,
        queryset=User.objects.active()
    )
    user = SimpleUserSerializer(read_only=True)
    comments = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Comment
        fields = (
            'id', 'created_at', 'updated_at', 'text', 'object_id', 'likes',
            'content_object_type', 'user', 'comments')
        response = {
            'likes': (SimpleUserSerializer, {'many': True}),
        }

    def get_comments(self, instance):
        return self.__class__(instance.comments.all(), many=True).data