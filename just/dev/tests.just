# Recipes for running tests.
#
# "core.test_settings" needs no .env and no Postgres — it runs on in-memory
# SQLite with a locmem email backend, so these work straight after a clone.

# Run all tests
@test-i-run:
    uv run python manage.py test apps --settings=core.test_settings

# Run tests with verbosity
@test-i-run-i-verbose:
    uv run python manage.py test apps --settings=core.test_settings --verbosity=2

# Run tests, stop on first failure
@test-i-fail-fast:
    uv run python manage.py test apps --settings=core.test_settings --failfast

# Run tests for a specific app or dotted path: just test-i-path apps.chat
@test-i-path path:
    uv run python manage.py test {{ path }} --settings=core.test_settings

# Run all tests with coverage and print a per-file report
@test-i-coverage:
    uv run coverage run manage.py test apps --settings=core.test_settings &&\
    uv run coverage report

# Run tests with coverage and write coverage.xml (used by CI)
@test-i-coverage-i-xml:
    uv run coverage run manage.py test apps --settings=core.test_settings &&\
    uv run coverage xml

# Open the HTML coverage report
@test-i-coverage-i-html:
    uv run coverage run manage.py test apps --settings=core.test_settings &&\
    uv run coverage html &&\
    echo "Report: htmlcov/index.html"

# Run tests in Docker
@test-i-docker-run:
    docker compose exec app-wsgi python manage.py test apps

# Run tests in Docker with verbosity
@test-i-docker-run-i-verbose:
    docker compose exec app-wsgi python manage.py test apps --verbosity=2
