from rest_framework import serializers

from reviews.models import (
    Category, Comment, Genre,
    MAX_EMAILFIELD_LENGTH, MAX_CONFCODE_LENGTH, MAX_USERNAME_LENGTH,
    MIN_SCORE, MAX_SCORE,
    Review, Title, YaMDBUser
)
from reviews.validators import validate_username, year_validator


class VerifyUsernameMixin():
    def validate_username(self, value):
        return validate_username(value)


class YaMDBUserSerializer(serializers.ModelSerializer, VerifyUsernameMixin):
    class Meta:
        model = YaMDBUser
        fields = (
            'username', 'email', 'first_name', 'last_name', 'bio', 'role',
        )


class SingupSerializer(serializers.Serializer, VerifyUsernameMixin):
    username = serializers.CharField(
        max_length=MAX_USERNAME_LENGTH,
        required=True,
    )
    email = serializers.EmailField(
        max_length=MAX_EMAILFIELD_LENGTH,
        required=True,
    )


class TokenSerialiser(serializers.Serializer, VerifyUsernameMixin):
    username = serializers.CharField(
        max_length=MAX_USERNAME_LENGTH,
        required=True
    )
    confirmation_code = serializers.CharField(
        max_length=MAX_CONFCODE_LENGTH,
        required=True
    )


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('name', 'slug')


class TitleReadSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(many=True, read_only=True)
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'description', 'genre', 'category', 'rating'
        )
        read_only_fields = fields


class TitleRecordSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all()
    )
    genre = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Genre.objects.all(),
        many=True
    )

    class Meta:
        model = Title
        fields = (
            'name', 'year', 'description', 'genre', 'category'
        )

    def to_representation(self, instance):
        return TitleReadSerializer().to_representation(instance)

    def validate_year(self, year):
        return year_validator(year)


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )
    score = serializers.IntegerField(
        min_value=MIN_SCORE,
        max_value=MAX_SCORE,
        error_messages={
            'min_value': f'Оценка не может быть меньше {MIN_SCORE}',
            'max_value': f'Оценка не может быть больше {MAX_SCORE}'
        }
    )

    class Meta:
        model = Review
        fields = ('id', 'text', 'author', 'score', 'pub_date')

    def validate(self, data):
        if not self.context['request'].method == 'POST':
            return data
        author = self.context['request'].user
        title_id = self.context['view'].kwargs['title_id']
        if Review.objects.filter(author=author, title=title_id).exists():
            raise serializers.ValidationError(
                'Нельзя оставить отзыв на одно произведение дважды'
            )
        return data


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')
