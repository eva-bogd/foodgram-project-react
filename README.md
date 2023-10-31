[![Built with Django REST framework](https://img.shields.io/badge/Built_with-Django_REST_framework-green.svg)](https://www.django-rest-framework.org/)
![example workflow](https://github.com/Eva-48k/yamdb_final/actions/workflows/yamdb_workflow.yml/badge.svg)

## Foodgram

**Foodgram** - это удобный помощник в планировании вашего рациона и осуществлении кулинарных фантазий. Здесь вы можете публиковать свои рецепты, изучать кулинарные шедевры других пользователей, сохранять избранные блюда и легко создавать списки продуктов для их приготовления.
Бэкенд для **Foodgram** написан на фреймворке Django REST framework.

### Установка и запуск:

1. Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:Eva-48k/foodgram-project-react.git
```

```
cd foodgram-project-react
```

2. Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

```
source env/bin/activate
```

```
python3 -m pip install --upgrade pip
```

3. Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

4. Выполнить миграции:

```
python3 manage.py migrate
```

5. Запустить проект:

```
python3 manage.py runserver
```
