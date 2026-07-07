# Run tests locally (requires env vars or .env file to be set up)
@test-i-run:
    python manage.py test apps

# Run tests with verbosity
@test-i-run-i-verbose:
    python manage.py test apps --verbosity=2
