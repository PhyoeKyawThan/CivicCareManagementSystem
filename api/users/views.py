from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib.auth import logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .serializers import (
    UserSerializer, 
    SignupSerializer, 
    LoginSerializer, 
    RefreshTokenSerializer,
    ChangePasswordSerializer
)
from users.models import User

class SignupView(generics.CreateAPIView):
    """
    View for user registration
    """
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens for the newly created user
        refresh = RefreshToken.for_user(user)
        
        # Prepare response data
        response_data = {
            'user': UserSerializer(user, context=self.get_serializer_context()).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'User registered successfully'
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    """
    View for user login
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        user = validated_data['user']
        
        response_data = {
            'user': UserSerializer(user, context={'request': request}).data,
            'tokens': {
                'refresh': validated_data['refresh'],
                'access': validated_data['access'],
            },
            'message': 'Login successful'
        }
        
        return Response(response_data, status=status.HTTP_200_OK)

class LogoutView(APIView):
    """
    View for user logout (blacklist refresh token)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Optionally, you can also add custom logout logic here
            
            return Response({
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class RefreshTokenView(APIView):
    """
    View for refreshing access token
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        
        response_data = {
            'user': UserSerializer(validated_data['user']).data,
            'tokens': {
                'refresh': validated_data['refresh'],
                'access': validated_data['access'],
            },
            'message': 'Token refreshed successfully'
        }
        
        return Response(response_data, status=status.HTTP_200_OK)

class ChangePasswordView(generics.UpdateAPIView):
    """
    View for changing user password
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            # Check old password
            if not user.check_password(serializer.data.get('old_password')):
                return Response(
                    {"old_password": ["Wrong password."]}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Set new password
            user.set_password(serializer.data.get('new_password'))
            user.save()
            
            # Optionally blacklist all tokens for this user
            # Or keep them logged in with the new password
            
            return Response({
                'message': 'Password updated successfully'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(generics.RetrieveUpdateAPIView):
    """
    View for user profile (view and update)
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        # For partial updates (PATCH)
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'user': serializer.data,
            'message': 'Profile updated successfully'
        })

class UserListView(generics.ListAPIView):
    """
    View for listing all users (admin only)
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Only administrators can see all users
        if user.role == 'administrator':
            return User.objects.all()
        # Regular users can only see themselves
        return User.objects.filter(id=user.id)

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View for user details (admin only for other users)
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    lookup_field = 'id'

    def get_object(self):
        user_id = self.kwargs.get('id')
        requesting_user = self.request.user
        
        # Users can only view their own profile, unless they're admin
        if requesting_user.role != 'administrator' and str(requesting_user.id) != user_id:
            self.permission_denied(self.request)
        
        return generics.get_object_or_404(User, id=user_id)

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        requesting_user = self.request.user
        
        # Regular users can only update their own profile
        if requesting_user.role != 'administrator' and user != requesting_user:
            self.permission_denied(request)
        
        # Administrators can change roles, regular users cannot
        if requesting_user.role != 'administrator' and 'role' in request.data:
            return Response(
                {"error": "Only administrators can change user roles"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        requesting_user = self.request.user
        
        # Only administrators can delete users (or users can delete themselves)
        if requesting_user.role != 'administrator' and user != requesting_user:
            self.permission_denied(request)
        
        # Don't allow users to delete administrators
        if user.role == 'administrator' and requesting_user.role != 'administrator':
            return Response(
                {"error": "Cannot delete administrator accounts"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        self.perform_destroy(user)
        return Response(status=status.HTTP_204_NO_CONTENT)

class CurrentUserView(generics.RetrieveAPIView):
    """
    View to get current authenticated user details
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

# If you need a custom JWT view
class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom token refresh view that includes user data in response
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Extract user ID from token
            from rest_framework_simplejwt.tokens import AccessToken
            access_token = response.data.get('access')
            
            if access_token:
                try:
                    token = AccessToken(access_token)
                    user_id = token['user_id']
                    user = User.objects.get(id=user_id)
                    response.data['user'] = UserSerializer(user).data
                except Exception:
                    pass
        
        return response

# Optional: View for password reset (if you implement email functionality)
class RequestPasswordResetView(APIView):
    """
    View for requesting password reset
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response(
                {"email": ["This field is required"]},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
            # Here you would generate a reset token and send email
            # For now, just return success message
            return Response({
                'message': 'If an account exists with this email, a reset link has been sent.'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            # Don't reveal if user exists or not (security)
            return Response({
                'message': 'If an account exists with this email, a reset link has been sent.'
            }, status=status.HTTP_200_OK)