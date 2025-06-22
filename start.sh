#!/bin/bash

set -o errexit

# pip install -r requirements.txt


python manage.py makemigrations --noinput

python manage.py migrate --noinput

python manage.py collectstatic --noinput

#run one-time
# python manage.py createsuperuser --noinput \
#   --username shaheenansari1906@gmail.com \
#   --email shaheenansari1906@gmail.com

# echo "from django.contrib.auth import get_user_model; \
#    User = get_user_model(); \
#    user = User.objects.get(username='shaheenansari1906@gmail.com'); \
#    user.set_password('Adminpass@123'); \
#    user.save()" \ 
#    | python manage.py shell

echo "from django.contrib.auth import get_user_model; \
  User = get_user_model(); \
  user = User.objects.get(username='shaheenansari1906@gmail.com'); \
  user.set_password('adminpass@123'); \
  user.save()" \
  | python manage.py shell

gunicorn task_management.wsgi:application --bind 0.0.0.0$PORT