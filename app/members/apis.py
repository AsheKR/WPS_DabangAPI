import requests

from rest_framework import permissions, status, generics
from rest_framework.permissions import AllowAny

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.utils import json
from rest_framework.views import APIView
from rest_framework_jwt.settings import api_settings

from members.models import SocialLogin
from members.permissions import IsOwnerOrReadOnly
from members.serializers import UserSerializer, UserProfileSerializer, SignUpViewSerializer
from django.contrib.auth.models import User

from members.serializers import UserSerializer, SignUpViewSerializer

User = get_user_model()

JWT_PAYLOAD_HANDLER = api_settings.JWT_PAYLOAD_HANDLER
JWT_ENCODE_HANDLER = api_settings.JWT_ENCODE_HANDLER

"""
 소셜로그인 라이브러리 사용할 예정
"""


class SignUpView(APIView):
    def post(self, request):
        serializer = SignUpViewSerializer(data=request.data)
        if serializer.is_valid():
            username = request.POST.get('username')
            password = request.POST.get('password')
            email = request.POST.get('email')
            User.objects.create_user(
                username=username,
                password=password,
                email=email,
            )
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class KakaoJwtTokenView(APIView):
    def post(self, request):
        access_token = request.POST.get('access_token')
        url = 'https://kapi.kakao.com/v2/user/me'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-type': 'application/x-www-form-urlencoded;charset=utf-8'
        }
        kakao_response = requests.post(url, headers=headers)

        user_data = kakao_response.json()
        kakao_id = user_data['id']
        user_username = user_data['properties']['nickname']
        user_first_name = user_username[1:]
        user_last_name = user_username[0]
        try:
            user = User.objects.get(username=kakao_id)
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=kakao_id,
                first_name=user_first_name,
                last_name=user_last_name,

            )
        payload = JWT_PAYLOAD_HANDLER(user)
        jwt_token = JWT_ENCODE_HANDLER(payload)

        kakao = SocialLogin.objects.filter(type='kakao')[0]
        user.social.add(kakao)
        data = {
            'token': jwt_token,
            'user': UserSerializer(user).data,
        }

        return Response(data)


class FacebookJwtToken(APIView):
    api_base = 'https://graph.facebook.com/v3.2'
    api_get_access_token = f'{api_base}/oauth/access_token'
    api_me = f'{api_base}/me'

    def post(self, request):
        access_token = request.POST.get('access_token')
        params = {
            'access_token': access_token,
            'fields': ','.join([
                'id',
                'first_name',
                'last_name',
                'picture.type(large)',
            ])
        }
        response = requests.get(self.api_me, params)
        data = response.json()

        facebook_id = data['id']
        first_name = data['first_name']
        last_name = data['last_name']

        try:
            user = User.objects.get(username=facebook_id)
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=facebook_id,
                first_name=first_name,
                last_name=last_name,
            )
        payload = JWT_PAYLOAD_HANDLER(user)
        jwt_token = JWT_ENCODE_HANDLER(payload)
        facebook = SocialLogin.objects.filter(type='facebook')[0]
        user.social.add(facebook)
        data = {
            'token': jwt_token,
            'user': UserSerializer(user).data,
        }
        return Response(data)


class SignUpView(generics.CreateAPIView):
    serializer_class = SignUpViewSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = SignUpViewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            username = serializer.validated_data['username']
            # username = request.data.get('username')    request.POST => X
            password = serializer.validated_data['password']
            # password = request.data.get('password')    request.POST => X
            email = serializer.validated_data['email']
            # email = request.data.get('email')    request.POST => X
            User.objects.create_user(
                username=username,
                password=password,
                email=email,
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#
# class UpdateUser(APIView):
#     authentication_classes =
#
#     def patch(self, request):
#         serializer = SignUpViewSerializer(data=request.data)
#         if serializer.is_valid():
#             return

