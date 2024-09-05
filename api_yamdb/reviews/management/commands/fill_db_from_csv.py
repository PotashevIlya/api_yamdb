import csv

from django.core.management.base import BaseCommand

from ...models import (
    Category, Comment, Genre, Review, Title, YaMDBUser
)


COMMAND_HELP = '''fill_db_from_csv - заполняет базу данных из csv-файлов
                   указанной в параметрах директории.
                   По умолчанию все файлы хранятся в директории static/data/.
                '''
DATA_HELP = 'Директория с csv-файлами для заполнения базы данных.'


CSV_PARAMS = (
    (
        YaMDBUser,
        'users.csv',
        None
    ),
    (
        Category,
        'category.csv',
        None
    ),
    (
        Genre,
        'genre.csv',
        None
    ),
    (
        Title,
        'titles.csv',
        (
            (Category, 'category', 'category'),
        )
    ),
    (
        Review,
        'review.csv',
        (
            (YaMDBUser, 'author', 'author'),
            (Title, 'title', 'title_id')
        )
    ),
    (
        Comment,
        'comments.csv',
        (
            (YaMDBUser, 'author', 'author'),
            (Review, 'review', 'review_id')
        )
    )
)


class Command(BaseCommand):
    help = COMMAND_HELP

    def get_model_obj(self, model, id):
        return model.objects.get(id=id)

    def fill_model_table(
        self, model, file_name, related_fields=None, **kwargs
    ):
        with open(
            f'{kwargs["dir"]}{file_name}', 'r', encoding='utf-8'
        ) as file:
            for row in csv.DictReader(file):
                try:
                    if not related_fields:
                        model.objects.get_or_create(**row)
                    else:
                        fields = {}
                        for related_model, field, column in related_fields:
                            fields[field] = self.get_model_obj(
                                related_model, row.pop(column)
                            )
                        model.objects.get_or_create(**fields, **row)
                except Exception:
                    continue

    def add_arguments(self, parser):
        parser.add_argument(
            'dir', type=str, help=DATA_HELP
        )

    def handle(self, *args, **kwargs):
        for model, file_name, related_fields in CSV_PARAMS:
            self.fill_model_table(
                model, file_name, related_fields=related_fields, **kwargs
            )
        with open(
            f'{kwargs["dir"]}genre_title.csv', 'r', encoding='utf-8'
        ) as file:
            for row in csv.DictReader(file):
                try:
                    Genre.objects.get(
                        id=row.pop('genre_id')
                    ).titles.add(Title.objects.get(id=row.pop('title_id')))
                except Exception:
                    continue
