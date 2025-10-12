# serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Role

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'color']

class UserProfileSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    points_of_sale = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'phone', 
            'location', 
            'role', 
            'join_date', 
            'last_login', 
            'status', 
            'avatar',
            'points_of_sale'
        ]

class UserProfileDetailSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'date_joined',
            'is_active',
            'is_staff',
            'is_superuser',
            'profile'
        ]