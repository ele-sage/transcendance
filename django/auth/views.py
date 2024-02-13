from django.http import JsonResponse, HttpRequest
from users.models import User
from users.serializers import UserSerializerWithToken
from auth.serializers import RegisterSerializer, LoginSerializer, LogoutSerializer
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from auth.oauth42 import create_oauth_uri, get_user_token, get_user_data
from users.utils import generate_username
from django.conf import settings


class RegisterView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    
    def post(self, request: HttpRequest) -> JsonResponse:
        print(request.data)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)

class LoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    
    def post(self, request: HttpRequest) -> JsonResponse:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        return JsonResponse(serializer.data, status=status.HTTP_200_OK)
    
class LogoutView(generics.GenericAPIView):
    serializer_class = LogoutSerializer
    
    def post(self, request: HttpRequest) -> JsonResponse:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return JsonResponse({'message': 'User logged out'}, status=status.HTTP_200_OK)
    
class OAuth42View(generics.GenericAPIView):
    permission_classes = [AllowAny]
    
    def get(self, request: HttpRequest) -> JsonResponse:
        redirect_uri = settings.OAUTH_REDIRECT_URL
        url = create_oauth_uri(redirect_uri)
        return JsonResponse({'url': url}, status=status.HTTP_200_OK)

class OAuth42RedirectedView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    
    def get(self, request: HttpRequest) -> JsonResponse:
        try:
            code = request.GET.get('code')
            redirect_uri = settings.OAUTH_REDIRECT_URL
            token = get_user_token(code, redirect_uri)
            user_data = get_user_data(token)

            if User.objects.filter(email=user_data['email']).exists():
                user = User.objects.get(email=user_data['email'])
                if user.oauth:
                    return JsonResponse(UserSerializerWithToken(user).data, status=status.HTTP_200_OK)
                else:
                    raise JsonResponse({'error': 'Your email address is used by an existing account.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                if User.objects.filter(username=user_data['username']).exists():
                    user_data['username'] = generate_username(user_data['first_name'], user_data['last_name'])
                user = User.objects.create_user(**user_data, oauth=True)
                return JsonResponse(UserSerializerWithToken(user).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# For development purposes only
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
class ResetDatabaseView(generics.DestroyAPIView):
    permission_classes = [AllowAny]
    def delete(self, request: HttpRequest) -> JsonResponse:
        try:
            User.objects.all().delete()
            return JsonResponse({'message': 'Database reset successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)