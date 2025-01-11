from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.parsers import MultiPartParser, FormParser

from rest_framework.generics import CreateAPIView, UpdateAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.utils import swagger_auto_schema
from shared.utility import send_email, check_email_or_phone
from .models import User, CODE_VERIFIED, NEW, VIA_EMAIL, VIA_PHONE
from .serializer import SignUpSerializer, ChangeUserInformation, ChangeUserPhotoSerializer, LoginSerializer, \
    LoginRefreshSerializer, LogoutSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
from drf_yasg import openapi
class CreateUserView(CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = SignUpSerializer

class VerifyAPIView(APIView):
    permission_classes = (IsAuthenticated, )
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'code': openapi.Schema(type=openapi.TYPE_STRING, description="The verification code sent to the user.")
            }
        )
    )
    def post(self, request, *args, **kwargs):
        user = self.request.user
        code = self.request.data.get('code')

        self.check_verify(user, code)
        return Response(
            data={
                "success": True,
                "AUTH_STATUS": user.AUTH_STATUS,
                "access": user.token()['access'],
                "refresh": user.token()['refresh_token']
            }
        )



    @staticmethod
    def check_verify(user, code):
        verifies = user.verify_codes.filter(expiration_time__gte=datetime.now(), code=code, is_confirmed=False)
        if not verifies.exists():
            data = {
                "message": "Your verfication codes is wrong or expired! "
            }

            raise ValidationError(data)
        verifies.update(is_confirmed=True)
        if user.AUTH_STATUS == NEW:
            user.AUTH_STATUS = CODE_VERIFIED
            user.save()

        return True


class GetNewVerification(APIView):
    def get(self,request, *args, **kwargs):
        user = self.request.user
        self.check_verification(user)
        if user.AUTH_TYPE == VIA_EMAIL:
            code = user.create_verify_code(VIA_EMAIL)
            send_email(user.email, code)
        elif user.AUTH_TYPE == VIA_PHONE:
            code = user.create_verify_code(VIA_PHONE)
            send_email(user.phone_number, code)
        else:
            data={
                'message':'Email or Phone number is invalid!'
            }
            raise ValidationError(data)
        return Response(
            {
                "success" : True,
                "message" : "Your verification code has been resent."
            })
    @staticmethod
    def check_verification(user):
        verifies = user.verify_codes.filter(expiration_time__gte=datetime.now(), is_confirmed=False)
        if verifies.exists():
            data = {
                "message": "Your verification code is still valid"
            }
            raise ValidationError(data)


class ChangeUserInformationView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangeUserInformation
    http_method_names = ['put', 'patch']

    def get_object(self):
        return self.request.user

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description="The user's first name."),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description="The user's last name."),
                'username': openapi.Schema(type=openapi.TYPE_STRING, description="The user's username."),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description="The new password for the user."),
                'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, description="Confirmation of the new password."),
            },
            required=['first_name', 'last_name', 'username', 'password', 'confirm_password']
        )
    )
    def update(self, request, *args, **kwargs):
        # Process the update request with the serializer
        super(ChangeUserInformationView, self).update(request, *args, **kwargs)
        data = {
            "success": True,
            "message": "User updated successfully",
            "AUTH_STATUS": self.request.user.AUTH_STATUS,  # Assuming AUTH_STATUS is an existing field
        }
        return Response(data, status=status.HTTP_200_OK)

class ChangeUserPhotoView(APIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser,)

    @swagger_auto_schema(
        operation_summary="Change user's photo",
        operation_description="Allows an authenticated user to update their profile photo by uploading a file.",
        manual_parameters=[
            openapi.Parameter(
                'photo',
                openapi.IN_FORM,
                description="Upload the photo file",
                type=openapi.TYPE_FILE,
                required=True,
            ),
        ],
        responses={
            200: openapi.Response(
                description="User photo updated successfully.",
                examples={
                    "application/json": {
                        "message": "User's photo updated successfully",
                        "photo_url": "http://example.com/media/user_photos/photo.jpg"
                    }
                },
            ),
            400: "Invalid input or file upload failed.",
        },
    )
    def put(self, request, *args, **kwargs):
        # Get the uploaded file from the request
        file = request.FILES.get('photo')  # Expecting 'photo' as the file field name
        if not file:
            return Response({"error": "No photo file provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Update user's photo field (assuming the user model has a 'photo' field)
        user = request.user
        user.photo = file  # Replace 'photo' with your actual user model field for photos
        user.save()

        return Response({
            "message": "User's photo updated successfully",
            "photo_url": request.build_absolute_uri(user.photo.url)
        }, status=status.HTTP_200_OK)

class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

class LoginRefreshView(TokenRefreshView):
    serializer_class = LoginRefreshSerializer

class LogoutView(GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated, ]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        try:
            refresh_token = self.request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            data = {
                'success':True,
                'message':'You have successfully logged out!'
            }
            return Response(data, status=205)
        except TokenError:
            return Response(status=400)

class ForgotPasswordView(APIView):
    permission_classes = (AllowAny, )
    serializer_class = ForgotPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email_or_phone = serializer.validated_data.get('email_or_phone')
        user = serializer.validated_data.get('user')
        if check_email_or_phone(email_or_phone) == 'phone':
            code = user.create_verify_code(VIA_PHONE)
            send_email(email_or_phone, code)
        elif check_email_or_phone(email_or_phone) == 'email':
            code = user.create_verify_code(VIA_EMAIL)
            send_email(email_or_phone, code)
        return Response({
            "sucess": True,
            "message": "Your password has been sent successfully",
            "access": user.token()['access'],
            "refresh_token": user.token()['refresh_token'], #may occur exception from here?
            "user_status" : user.AUTH_STATUS,
        }, status=200)

class ResetPasswordView(UpdateAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = (IsAuthenticated, )
    http_method_names = ['put', 'patch']

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        response = super(ResetPasswordView, self).update(request, *args, **kwargs)
        try:
            user = User.objects.get(id=response.data.get('id'))

        except ObjectDoesNotExist as e:
            raise NotFound(detail="User not found")

        return Response({
            "success" : True,
            "message" : "Password has been reset successfully",
            "access": user.token()['access'],
            "refresh_token": user.token()['refresh_token'],
        })