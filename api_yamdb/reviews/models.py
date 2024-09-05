from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from .validators import validate_username, year_validator


USER_ROLE = 'user'
MODERATOR_ROLE = 'moderator'
ADMIN_ROLE = 'admin'
ROLES = (
    (USER_ROLE, 'пользователь'),
    (MODERATOR_ROLE, 'модератор'),
    (ADMIN_ROLE, 'администратор'),
)
MAX_USERNAME_LENGTH = 150
MAX_CONFCODE_LENGTH = 16
MAX_EMAILFIELD_LENGTH = 254
MIN_SCORE = 1
MAX_SCORE = 10


class SlugNameFieldsBaseModel(models.Model):
    name = models.CharField(
        'Название',
        max_length=256,
        help_text='Введите название'
    )
    slug = models.SlugField(
        'Слаг',
        max_length=50,
        unique=True,
        help_text='Введите уникальный слаг'
    )

    class Meta:
        abstract = True
        ordering = ('name',)

    def __str__(self):
        return self.name[:30]


class YaMDBUser(AbstractUser):
    username = models.CharField(
        verbose_name='Юзернейм',
        max_length=MAX_USERNAME_LENGTH,
        unique=True,
        help_text='Введите юзернейм',
        validators=(
            validate_username,
        ),
    )
    email = models.EmailField(
        verbose_name='Электронная почта',
        max_length=MAX_EMAILFIELD_LENGTH,
        blank=False,
        null=False,
        unique=True,
        help_text='Введите почту'
    )
    role = models.CharField(
        verbose_name='Роль в системе',
        max_length=max(len(role) for role, _ in ROLES),
        choices=ROLES,
        default=USER_ROLE,
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=MAX_USERNAME_LENGTH,
        blank=True,
        null=True,
        help_text='Введите имя'
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=MAX_USERNAME_LENGTH,
        blank=True,
        null=True,
        help_text='Введите фамилию'
    )
    confirmation_code = models.CharField(
        verbose_name='Код поддтверждения',
        max_length=MAX_CONFCODE_LENGTH,
        blank=True,
        null=True,
        help_text='Введите код подтверждения',
    )
    bio = models.TextField(
        verbose_name='Биография',
        blank=True,
        null=True,
        help_text='Введите краткую биографию или описание'
    )

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ("email",)

    @property
    def is_admin(self):
        return self.role == ADMIN_ROLE or self.is_staff

    @property
    def is_moderator(self):
        return self.role == MODERATOR_ROLE

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)


class Category(SlugNameFieldsBaseModel):
    class Meta(SlugNameFieldsBaseModel.Meta):
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'


class Title(models.Model):
    name = models.CharField(
        'Название произведения',
        max_length=256,
        help_text='Введите название произведения'
    )
    year = models.IntegerField(
        'Год',
        validators=(year_validator,),
        help_text='Год создания произведения'
    )
    description = models.TextField(
        'Описание',
        blank=True,
        null=True,
        help_text='Описание произведения'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True
    )
    genre = models.ManyToManyField('Genre')

    class Meta:
        verbose_name = 'произведение'
        verbose_name_plural = 'Произведения'
        ordering = ('year', 'name')
        default_related_name = 'titles'

    def __str__(self):
        return self.name[:30]


class TextAuthorFieldsBaseModel(models.Model):
    text = models.TextField()
    author = models.ForeignKey(
        YaMDBUser,
        on_delete=models.CASCADE
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        abstract = True
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:24]


class Review(TextAuthorFieldsBaseModel):
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE
    )
    score = models.PositiveIntegerField(
        validators=[
            MinValueValidator(
                MIN_SCORE,
                message=f'Оценка не может быть меньше {MIN_SCORE}'
            ),
            MaxValueValidator(
                MAX_SCORE,
                message=f'Оценка не может быть больше {MAX_SCORE}'
            ),
        ]
    )

    class Meta(TextAuthorFieldsBaseModel.Meta):
        verbose_name = 'отзыв'
        verbose_name_plural = 'Отзывы'
        default_related_name = 'reviews'
        constraints = [
            models.UniqueConstraint(
                fields=('author', 'title'),
                name='unique_author_title'
            )
        ]


class Comment(TextAuthorFieldsBaseModel):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
    )

    class Meta(TextAuthorFieldsBaseModel.Meta):
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        default_related_name = 'comments'


class Genre(SlugNameFieldsBaseModel):
    class Meta(SlugNameFieldsBaseModel.Meta):
        verbose_name = 'жанр'
        verbose_name_plural = 'Жанры'
