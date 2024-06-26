from django.http import JsonResponse, HttpRequest
from users.models import User, UserChannelGroup
from authentication.serializers import RegisterSerializer, LoginSerializer, OAuth42LoginSerializer, LogoutSerializer
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from authentication.oauth42 import create_oauth_uri
from datetime import datetime
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken
from notification.utils import send_to_websocket
from channels.layers import get_channel_layer
    
def set_cookies(response, user):
    refresh_token = TokenObtainPairSerializer().get_token(user)
    access_token = refresh_token.access_token    
    refresh_token_exp = datetime.fromtimestamp(refresh_token['exp'])
    access_token_exp = datetime.fromtimestamp(access_token['exp'])
    response.set_cookie('access_token', str(access_token), samesite='Strict', httponly=True, secure=True, expires=access_token_exp)
    response.set_cookie('refresh_token', str(refresh_token), samesite='Strict', httponly=True, secure=True, expires=refresh_token_exp, path='/api/refresh-token/')
    return response

def delete_cookies(response):
    response.delete_cookie('access_token', path='/')
    response.delete_cookie('refresh_token', path='/api/refresh-token/')
    print('Cookies deleted')
    return response

class RegisterView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    
    def post(self, request: HttpRequest) -> JsonResponse:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response = JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        return set_cookies(response, user)

class LoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    
    def post(self, request: HttpRequest) -> JsonResponse:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        response = JsonResponse(serializer.data, status=status.HTTP_200_OK)
        return set_cookies(response, user)

class LogoutView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LogoutSerializer
    
    def post(self, request: HttpRequest) -> JsonResponse:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response = JsonResponse({'message': 'Logout successful'}, status=status.HTTP_200_OK)
        response = delete_cookies(response)
        try:
            user = User.objects.get(pk=request.user.id)
            channel_name = UserChannelGroup.objects.get(user=user).main
            send_to_websocket(get_channel_layer(), channel_name, {'type': 'websocket.close'})
        except Exception:
            print('User not found')
        return response

        
class OAuth42UriView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    def get(self, request: HttpRequest) -> JsonResponse:
        uri = create_oauth_uri()
        return JsonResponse({'uri': uri}, status=status.HTTP_200_OK)

class OAuth42LoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = OAuth42LoginSerializer
    
    def post(self, request: HttpRequest) -> JsonResponse:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        response = JsonResponse(serializer.data, status=status.HTTP_200_OK)
        return set_cookies(response, user)

class CustomTokenRefreshView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = TokenRefreshSerializer
    
    def post(self, request: HttpRequest) -> JsonResponse:
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            if not refresh_token:
                return JsonResponse({'error': 'No refresh token found'}, status=status.HTTP_403_FORBIDDEN)
            serializer = self.get_serializer(data={'refresh': refresh_token})
            serializer.is_valid(raise_exception=True)
            response = JsonResponse(serializer.validated_data, status=status.HTTP_200_OK)
            access_token = serializer.validated_data['access']
            access_token_exp = datetime.fromtimestamp(AccessToken(access_token)['exp'])
            response.set_cookie('access_token', str(access_token), samesite='Strict', httponly=True, secure=True, expires=access_token_exp)
            return response
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
