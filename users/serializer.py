from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from rest_framework.generics import get_object_or_404
from rest_framework_simplejwt.serializers import TokenObtainSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken

from shared.utility import check_email_or_phone, send_email, send_phone_code, check_user_type
from .models import User, UserConfirmation, VIA_EMAIL, VIA_PHONE, CODE_VERIFIED, DONE, PHOTO_STEP, NEW


class SignUpSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(read_only=True)

    def __init__(self, *args, **kwargs):
        super(SignUpSerializer, self).__init__(*args, **kwargs)
        self.fields['email_phone_number'] = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'AUTH_TYPE',
            'AUTH_STATUS',
        )

        extra_kwargs = {
            'AUTH_TYPE':{'read_only':True, 'required':False},
            'AUTH_STATUS':{'read_only':True, 'required':False},

        }

    def create(self, validated_data):
        user = super(SignUpSerializer, self).create(validated_data)
        if user.AUTH_TYPE == VIA_EMAIL:
            code = user.create_verify_code(VIA_EMAIL)
            send_email(user.email, code)
        elif user.AUTH_TYPE == VIA_PHONE:
            code = user.create_verify_code(VIA_PHONE)
            send_email(user.phone_number, code)
            #send_phone_code(user.phone_number, code)
        user.save()
        return user

    def validate(self, data):
        super(SignUpSerializer, self).validate(data)
        data = self.auth_validate(data)
        return data

    @staticmethod
    def auth_validate(data):
        user_input = str(data.get('email_phone_number')).lower()
        input_type = check_email_or_phone(user_input)
        if input_type == 'email':
            data = {
                'email': user_input,
                'AUTH_TYPE': VIA_EMAIL
            }
        elif input_type == 'phone':
            data = {
                "phone_number": user_input,
                "AUTH_TYPE": VIA_PHONE
            }
        else:
            data = {
                'success':False,
                'message': "You must send email or phone number"
            }
            raise ValidationError(data)
        return data

    def validate_email_phone_number(self, value):
        value = value.lower()
        if value and User.objects.filter(email=value).exists():
            data = {
                "success": False,
                "message": "This email is already used and exists"
            }
            raise ValidationError(data)
        elif value and User.objects.filter(phone_number=value).exists():
            data = {
                "success": False,
                "message": "This phone number is already used and exists"
            }
            raise ValidationError(data)
        return value

    def to_representation(self, instance):
        data = super(SignUpSerializer, self).to_representation(instance)
        data.update(instance.token())
        return data

class ChangeUserInformation(serializers.Serializer):
    first_name = serializers.CharField(required=True, write_only=True)
    last_name = serializers.CharField(required=True, write_only=True)
    username = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        password = data.get('password', None)
        confirm_password = data.get('confirm_password', None)
        if password != confirm_password:
            raise ValidationError({
                'message': 'Passwords do not match'
            })
        if password:
            validate_password(password)
            validate_password(confirm_password)
        return data

    def validate_username(self, username):
        if len(username) < 3 or len(username) > 30:
            raise ValidationError({
                'message': 'Username must be between 3 and 30 characters'
            })
        if username.isdigit():
            raise ValidationError({
                'message': 'Username must only contain numbers'
            })

    def validate_first_name(self, first_name):
        if len(first_name) < 3 or len(first_name) > 30:
            raise ValidationError({
                'message': 'First name must be between 3 and 30 characters'
            })
        if first_name.isdigit():
            raise ValidationError({
                'message': 'Firs name cannot be numeric'
            })
        if first_name.isalpha():
            raise ValidationError({
                'message': 'First name must only contain letters'
            })


    def validate_last_name(self, last_name):

        if len(last_name) < 3 or len(last_name) > 30:
            raise ValidationError({
                'message': 'Last name must be between 3 and 30 characters'
            })

        if last_name.isdigit():
            raise ValidationError({
                'message': 'Last name cannot be numeric'
            })

        if last_name.isalpha():
            raise ValidationError({
                'message': 'Last name must only contain letters'
            })

    def update(self, instance, validated_data):

        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.username = validated_data.get('username', instance.username)
        instance.password = validated_data.get('password', instance.password)

        if validated_data.get('password'):
            instance.set_password(validated_data.get('password'))

        if instance.AUTH_STATUS == CODE_VERIFIED:
            instance.AUTH_STATUS = DONE

        instance.save()
        return instance


class ChangeUserPhotoSerializer(serializers.Serializer):
    photo = serializers.ImageField()
    def update(self, instance, validated_data):
        photo = validated_data.get('photo', None)

        if photo:
            instance.photo = photo
            instance.AUTH_STATUS = PHOTO_STEP
            instance.save()
        return instance


class LoginSerializer(TokenObtainSerializer):

    def __init__(self, *args, **kwargs):
        super(LoginSerializer, self).__init__(*args, **kwargs)
        self.fields['userinput'] = serializers.CharField(required=True)
        self.fields['username'] = serializers.CharField(required=False, read_only=True)

    def auth_validate(self, data):

        user_input = data.get('userinput')
        if check_user_type(user_input) == 'username':
            username = user_input
        elif check_user_type(user_input) == 'email':
            user = self.get_user(email__iexact=user_input)
            username = user.username
        elif check_user_type(user_input) == 'phone':
            user = self.get_user(phone_number=user_input)
            username = user.username
        else:
            data = {
                'success': True,
                'message': "You must send email, phone number or username"
            }
            raise ValidationError(data)

        authentication_kwargs = {
            self.username_field: username,
            'password': data['password']
        }

        current_user = User.objects.filter(username__iexact=username).first()
        if current_user.auth_status == NEW or current_user.auth_status == CODE_VERIFIED and current_user is not None:
            raise ValidationError({
                'success': False,
                'message': "You did not completed registration yet"
            })

        user = authenticate(**authentication_kwargs)
        if user is not None:
            self.user = user
        else:
            raise ValidationError({
                'success': False,
                'message': "Login or password is incorrect"
            })

    def validate(self, data):
        self.auth_validate(data)
        if self.user.AUTH_STATUS not in [DONE, PHOTO_STEP]:
            raise PermissionDenied('You do not have permission to perform this action')
        data = self.user.token()
        data['auth_status'] = self.user.auth_status
        return data

    def get_user(self, **kwargs):
        users = User.objects.filter(**kwargs)
        if not users.exists():
            raise ValidationError({
                'message': "No active account found"
            })

        return users.first()

class LoginRefreshSerializer(TokenRefreshSerializer):

    def validate(self,attrs):
        data = super().validate(attrs)
        access_token_instance = AccessToken(data['access'])
        user_id = access_token_instance['']
        user = get_object_or_404(User, id=user_id)
        update_last_login(None, user)
        return data

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class ForgotPasswordSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email_or_phone = attrs.get('email_or_phone', None)
        if email_or_phone is None:
            raise ValidationError({
                'success': False,
                'message': "You must enter phone number or email"
            })

        user = User.objects.filter(Q(phone_number=email_or_phone)|Q(email=email_or_phone)).first()
        if not user.exists():
            raise NotFound(detail='User does not exist')

        attrs['user'] = user.first()

class ResetPasswordSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=True)
    password = serializers.CharField(write_only=True, required=True,min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=True,min_length=8)

    class Meta:
        model = User
        fields = ('id', 'password', 'confirm_password')

    def validate(self, data):
        password = data.get('password', None)
        confirm_password = data.get('confirm_password', None)
        if password != confirm_password:
            raise ValidationError({
                'success': False,
                'message': "Passwords do not match"
            })
        if password:
            validate_password(password)
        return data

    def update(self , instance, validated_data):
        password = validated_data.pop('password')
        instance.set_password(password)
        return super(ResetPasswordSerizalizer, self).update(instance, validated_data)