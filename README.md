[![Built with Django REST framework](https://img.shields.io/badge/Built_with-Django_REST_framework-green.svg)](https://www.django-rest-framework.org/)
![example workflow](https://github.com/Eva-48k/yamdb_final/actions/workflows/yamdb_workflow.yml/badge.svg)

## Foodgram

**Foodgram** - это удобный помощник в планировании вашего рациона и осуществлении кулинарных фантазий. Здесь вы можете публиковать свои рецепты, изучать кулинарные шедевры других пользователей, сохранять избранные блюда и легко создавать списки продуктов для их приготовления.
Бэкенд для **Foodgram** написан на фреймворке Django.

### Установка

Чтобы запустить проект **Foodgram** в контейнерах Docker, выполните следующие шаги:

1. Склонируйте репозиторий с помощью команды:

```
git clone git@github.com:Eva-48k/foodgram-project-react.gitt
```

2. В папке проекта infra/ создайте файл .env со следующим содержимым:

```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
SECRET_KEY=secret_key
```

3. Запустите контейнеры Docker::

```
docker-compose up --build
```

4. Создайте базу данных и примените миграции:

```
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

5. Создайте суперпользователя:

```
python manage.py createsuperuser
```

6. Загрузите начальные данные:

```
docker-compose exec web python load_data_to_postgres.py
```

7. Откройте веб-браузер и перейдите по адресу http://84.201.137.218/
