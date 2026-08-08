import "vars.just"
import "configs.just"

# Compose reads USER_ID (uppercase) for both the image build arg and the runtime
# user, so the container writes into the bind-mounted source tree as you, not root.
export USER_ID := user_id

# Up services with build
d-up: init-i-configs
    @COMPOSE_PROFILES=full_dev \
    COMPOSE_BAKE=true COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 \
    	docker compose \
    	  up \
          --build

# Up services with build for local development
d-up-i-local-dev: init-i-configs
    @COMPOSE_PROFILES=local_dev \
    COMPOSE_BAKE=true COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 \
    	docker compose \
    	  up \
          --build

# Up services with build and watch changes
d-up-i-watch: init-i-configs
    @COMPOSE_PROFILES=full_dev \
    COMPOSE_BAKE=true COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 \
    	docker compose \
    	  up \
          --build \
          --watch

# Run app. For interact with app in "interactive" mode with "tty" enabled.
d-run-i-app:
    @COMPOSE_PROFILES=full_dev \
    COMPOSE_BAKE=true COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 \
    	docker compose \
            run \
            --rm --build \
            app-wsgi

# Build services
d-build:
    @COMPOSE_PROFILES=full_dev \
    COMPOSE_BAKE=true COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 \
    	docker compose \
    		build

# Purge all data related with services
d-purge:
    @COMPOSE_PROFILES=full_dev \
    COMPOSE_BAKE=true COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 \
    	docker compose \
    	    down \
    	    --volumes --remove-orphans --rmi local --timeout 0

# Get information about current compose configuration
d-compose-inspect:
    @COMPOSE_PROFILES=full_dev \
    COMPOSE_BAKE=true COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 \
    	docker compose config
