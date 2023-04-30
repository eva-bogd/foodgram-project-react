[![Built with Django REST framework](https://img.shields.io/badge/Built_with-Django_REST_framework-green.svg)](https://www.django-rest-framework.org/)

# Foodgram

**Foodgram** - это удобный помощник в планировании вашего рациона и осуществлении кулинарных фантазий. Здесь вы можете публиковать свои рецепты, изучать кулинарные шедевры других пользователей, сохранять избранные блюда и легко создавать списки продуктов для их приготовления.

Бэкенд для **Foodgram** написан на фреймворке Django.
В скором времени появится возможность для развертывания проекта с использованием Docker)

### Установка

Чтобы установить проект **Foodgram** локально, выполните следующие шаги:

1. Склонируйте репозиторий с помощью команды:

```
git clone https://github.com/<your_username>/foodgram.git
```

2. Создайте и активируйте виртуальное окружение:

```
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate  # для Windows
```

3. Установите зависимости:

```
pip install -r requirements.txt
```

4. Создайте базу данных и примените миграции:

```
python manage.py migrate
```

5. Создайте суперпользователя:

```
python manage.py createsuperuser
```

6. Запустите сервер:

```
python manage.py runserver
```

7. Откройте веб-браузер и перейдите по адресу http://localhost/


### Документация API

Документация API находится по адресу http://localhost/api/docs/

---