from http import HTTPStatus

from django.core.mail import send_mail
from django.db import IntegrityError
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django.utils import crypto
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, serializers, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from api_yamdb.settings import EMAIL_NOREPLY
from reviews.models import (
    MAX_CONFCODE_LENGTH, Category, Genre, Review, Title, YaMDBUser
)
from reviews.validators import SELF_ENDPOINT

from .filters import TitlesFilter
from .permissions import (
    IsAdminOnly, IsAdminOrReadOnly, IsAuthorIsAdminIsModeratorOrReadOnly
)
from .serializers import (
    CategorySerializer, CommentSerializer, GenreSerializer,
    ReviewSerializer, SingupSerializer, TitleRecordSerializer,
    TitleReadSerializer, TokenSerialiser, YaMDBUserSerializer
)


ENAIL_CODE_SUBJECT = 'YaMDB: код подтвержжения в системе'
ENAIL_CODE_MESSAGE = 'Ваш код для входа: {code}'
ACCESS_CODE_ERROR = 'Невереный код подтверждения'
EMAIL_EXISTS = 'Пользователь с почтой {email} уже существует.'
USERNAME_EXISTS = 'Пользователь с юзернеймом {username} уже существует.'


class YaMDBUserViewSet(viewsets.ModelViewSet):
    queryset = YaMDBUser.objects.all()
    serializer_class = YaMDBUserSerializer
    lookup_field = 'username'
    filter_backends = [filters.SearchFilter]
    search_fields = ['username']
    permission_classes = (IsAdminOnly,)
    http_method_names = [
        'get', 'post', 'patch', 'delete', 'options',
    ]

    @action(detail=False,
            methods=('get', 'patch'),
            url_path=SELF_ENDPOINT,
            permission_classes=(IsAuthenticated,)
            )
    def self_endpoint(self, request):
        if request.method != 'PATCH':
            serializer = YaMDBUserSerializer(request.user)
            return Response(serializer.data, status=HTTPStatus.OK)
        serializer = YaMDBUserSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(
            role=request.user.role
        )
        return Response(serializer.data, status=HTTPStatus.OK)


@api_view(('POST',))
@permission_classes((AllowAny,))
def signup(request):
    serializer = SingupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email']
    username = serializer.validated_data['username']
    try:
        user, _ = YaMDBUser.objects.get_or_create(
            username=username,
            email=email,
        )
    except IntegrityError:
        error_message = {
            'username': [USERNAME_EXISTS.format(username=username)]
        } if YaMDBUser.objects.filter(username=username).exists() else {
            'email': [EMAIL_EXISTS.format(email=email)]
        }
        raise serializers.ValidationError(error_message)
    user.confirmation_code = crypto.get_random_string(MAX_CONFCODE_LENGTH)
    user.save()
    send_mail(
        subject=ENAIL_CODE_SUBJECT,
        message=ENAIL_CODE_MESSAGE.format(code=user.confirmation_code),
        from_email=EMAIL_NOREPLY,
        recipient_list=(email,),
        fail_silently=True,
    )
    return Response(
        {'email': email, 'username': username},
        status=HTTPStatus.OK
    )


@api_view(('POST',))
@permission_classes((AllowAny,))
def get_token(request):
    serializer = TokenSerialiser(data=request.data)
    serializer.is_valid(raise_exception=True)
    username = serializer.validated_data['username']
    confirmation_code = serializer.validated_data['confirmation_code']
    user = get_object_or_404(
        YaMDBUser,
        username=username
    )
    user_confirmation_code = user.confirmation_code
    if user_confirmation_code != '':
        user.confirmation_code = ''
        user.save()
        if user_confirmation_code == confirmation_code:
            return Response(
                data={'token': str(AccessToken.for_user(user))},
                status=HTTPStatus.OK
            )
        raise serializers.ValidationError({'error': ACCESS_CODE_ERROR})


class ListCreateDestroyGenericViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    filter_backends = [filters.SearchFilter]
    search_fields = ('name',)
    lookup_field = 'slug'
    permission_classes = (IsAdminOrReadOnly,)


class CategoryViewSet(ListCreateDestroyGenericViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all().annotate(
        rating=Avg('reviews__score')
    ).order_by(*Title._meta.ordering)
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitlesFilter
    http_method_names = [
        'get', 'post', 'patch', 'delete', 'options',
    ]

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return TitleReadSerializer
        return TitleRecordSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (IsAuthorIsAdminIsModeratorOrReadOnly,)
    http_method_names = [
        'get', 'post', 'patch', 'delete', 'options',
    ]

    def get_title(self):
        return get_object_or_404(Title, id=self.kwargs['title_id'])

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, title=self.get_title())

    def get_queryset(self):
        return self.get_title().reviews.all()


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (IsAuthorIsAdminIsModeratorOrReadOnly,)
    http_method_names = [
        'get', 'post', 'patch', 'delete', 'options',
    ]

    def get_review(self):
        return get_object_or_404(Review, id=self.kwargs['review_id'])

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, review=self.get_review())

    def get_queryset(self):
        return self.get_review().comments.all()


class GenreViewSet(ListCreateDestroyGenericViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
