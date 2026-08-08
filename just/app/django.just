# Django. Generate migrations.
@django-i-migrations:
    python manage.py makemigrations

# Django. Apply migrations.
@django-i-migrate:
    python manage.py migrate

# Django. Create superuser.
django-i-create-superuser:
    #!/usr/bin/env bash
    django_superuser_password=${django_superuser_password:-admin123} \
    django_superuser_username=${django_superuser_username:-admin} \
    django_superuser_email=${django_superuser_email:-a@a.com} \
    ;
    DJANGO_SUPERUSER_PASSWORD=${django_superuser_password} \
    python manage.py createsuperuser --noinput \
    --username "${django_superuser_username}" \
    --email "${django_superuser_email}"
