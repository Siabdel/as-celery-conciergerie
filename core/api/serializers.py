
# core/api/serializers.py
from rest_framework import serializers
from core.models import LandingSection

class LandingSectionSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = LandingSection
        fields = ["id", "title", "subtitle", "description", "icon", "image_url", "order"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None
