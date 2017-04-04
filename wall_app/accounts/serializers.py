from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from accounts.models import SiteUser


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=15,
        min_length=5,
        required=True
    )
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    email = serializers.EmailField(required=True)
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    about = serializers.CharField(max_length=250)
    profile_pic = serializers.URLField(
        max_length=200,
        min_length=None,
        allow_blank=False
    )

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError(
                _("The two passwords didn't match"))
        return data

    def save(self):
        user = User.objects.create(
            username=self.validated_data['username'],
            first_name=self.validated_data['first_name'],
            last_name=self.validated_data['last_name'],
            email=self.validated_data['email'],
            password=self.validated_data['password1'],
        )
        site_user = SiteUser.objects.create(
            user=user,
            profile_pic=self.validated_data['profile_pic'],
            about=self.validated_data['about']
        )
        return site_user
