# accounts/serializers.py

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'phone', 'password', 'password_confirm')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs

    def create(self, validated_data):
        # Remove password_confirm from validated_data
        validated_data.pop('password_confirm', None)
        
        # Create user
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data.get('phone', ''),
            password=validated_data['password']
        )
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        return user

class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid email or password.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include email and password.')

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile
    """
    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ('user',)

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user details
    """
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.ReadOnlyField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'phone', 
                 'date_of_birth', 'profile_picture', 'is_verified', 'full_name',  'role' , 
                 'profile', 'created_at', 'updated_at')
        read_only_fields = ('id', 'is_verified', 'created_at', 'updated_at')
    def get_role(self, obj):
        if obj.is_superuser or obj.is_staff:
            return "admin"
        return "user"

    def update(self, instance, validated_data):
        # Handle profile data separately if provided
        profile_data = self.context['request'].data.get('profile', {})
        if profile_data:
            profile_serializer = UserProfileSerializer(
                instance.profile, 
                data=profile_data, 
                partial=True
            )
            if profile_serializer.is_valid():
                profile_serializer.save()

        return super().update(instance, validated_data)

class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing password
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match.")
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value