from rest_framework_simplejwt import serializers
from .utils import verify_token


class TokenRefreshSlidingSerializer(serializers.TokenRefreshSlidingSerializer):
    def validate(self, attrs):
        token = verify_token(attrs['token'])
        return {'token': str(token)}
