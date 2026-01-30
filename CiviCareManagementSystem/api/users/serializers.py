from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from users.models import User

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'avatar', 'first_name', 'last_name', 'is_staff', 'date_joined']
        read_only_fields = ['id', 'username', 'email', 'is_staff', 'date_joined']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'email', 
            'phone', 'avatar', 'date_of_birth', 'role',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'},
        validators=[validate_password]
    )
    confirm_password = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'username', 'full_name', 'email', 'phone', 
            'role', 'date_of_birth', 'avatar', 
            'password', 'confirm_password'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'full_name': {'required': True},
        }

    def validate(self, data):
        # Check if passwords match
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Check if email already exists
        if User.objects.filter(email=data.get('email', '')).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
        
        # Check if username already exists
        if User.objects.filter(username=data.get('username', '')).exists():
            raise serializers.ValidationError({"username": "A user with this username already exists."})
        
        return data

    def validate_email(self, value):
        value = value.lower().strip()  # Normalize email
        return value

    def create(self, validated_data):
        validated_data.pop('confirm_password')  # Remove confirm_password field
        password = validated_data.pop('password')
        
        try:
            user = User.objects.create_user(
                **validated_data,
                password=password
            )
            return user
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'}
    )

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            raise serializers.ValidationError("Must include 'username' and 'password'.")
        
        # Allow login with email as well
        user = None
        if '@' in username:  # If it looks like an email
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(
                    self.context.get('request'),
                    username=user_obj.username,
                    password=password
                )
            except User.DoesNotExist:
                pass
        else:
            user = authenticate(
                self.context.get('request'),
                username=username,
                password=password
            )
        
        if not user:
            raise serializers.ValidationError("Invalid username/email or password.")
        
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return {
            'user': user,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)
    
    def validate(self, attrs):
        refresh_token = attrs['refresh']
        
        try:
            refresh = RefreshToken(refresh_token)
            user_id = refresh['user_id']
            
            user = User.objects.get(id=user_id)
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            
            # Blacklist the old refresh token
            try:
                refresh.blacklist()
            except Exception:
                # Token might already be blacklisted or SimpleJWT might not have blacklist app
                pass
            
            # Generate new tokens
            new_refresh = RefreshToken.for_user(user)
            
            attrs['refresh'] = str(new_refresh)
            attrs['access'] = str(new_refresh.access_token)
            attrs['user'] = user
            
            return attrs
            
        except TokenError as e:
            raise serializers.ValidationError({'refresh': str(e)})
        except User.DoesNotExist:
            raise serializers.ValidationError('User not found.')
        except Exception as e:
            raise serializers.ValidationError(f'Invalid token: {str(e)}')

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True, 
        write_only=True,
        validators=[validate_password]
    )
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return data