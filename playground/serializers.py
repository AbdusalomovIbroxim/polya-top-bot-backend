from rest_framework import serializers
from .models import SportField

class SportFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = SportField
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'rating') 