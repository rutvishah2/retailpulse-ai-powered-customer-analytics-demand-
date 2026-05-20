# RetailPulse - Docker Build & Push Script

# Build arguments
DOCKER_REGISTRY=gcr.io
DOCKER_PROJECT=retailpulse
DOCKER_IMAGE=retailpulse
DOCKER_TAG=latest
VERSION=2.0

# Build image
build:
	docker build -t $(DOCKER_REGISTRY)/$(DOCKER_PROJECT)/$(DOCKER_IMAGE):$(DOCKER_TAG) .
	docker build -t $(DOCKER_REGISTRY)/$(DOCKER_PROJECT)/$(DOCKER_IMAGE):v$(VERSION) .

# Push to registry
push:
	docker push $(DOCKER_REGISTRY)/$(DOCKER_PROJECT)/$(DOCKER_IMAGE):$(DOCKER_TAG)
	docker push $(DOCKER_REGISTRY)/$(DOCKER_PROJECT)/$(DOCKER_IMAGE):v$(VERSION)

# Run locally
run-docker-compose:
	docker-compose up -d

# Stop services
stop-docker-compose:
	docker-compose down

# View logs
logs:
	docker-compose logs -f dashboard

# Clean up
clean:
	docker-compose down -v
	docker system prune -f

.PHONY: build push run-docker-compose stop-docker-compose logs clean
