import "vars.just"

# Run tests in Docker
@test-i-docker-run:
    export user_id={{ user_id }} &&\
    docker compose exec app-wsgi python manage.py test apps

# Run tests in Docker with verbosity
@test-i-docker-run-i-verbose:
    export user_id={{ user_id }} &&\
    docker compose exec app-wsgi python manage.py test apps --verbosity=2
