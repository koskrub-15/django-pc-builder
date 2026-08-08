# Initialize configs. Re-running never overwrites an .env you have already edited.
init-i-configs:
    @cp --no-clobber compose.override.dev.yaml compose.override.yaml || true &&\
    cp --no-clobber .env.example .env || true
