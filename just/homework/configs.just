# Initialize configs
init-i-configs:
    @cp compose.override.dev.yaml compose.override.yaml &&\
    cp .env.example .env
