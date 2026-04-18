# Build the Docker image
build:
	sudo docker compose build

# Start the container
up:
	sudo docker compose up

# Stop and remove the container
down:
	sudo docker compose down

# Enter the container terminal
shell:
	sudo docker exec -it playwright_scraper /bin/bash

# Run the scraper inside the container
run:
	python scraper.py