#!/bin/bash

echo "Deploying to App"
ssh ec2-user@3.85.36.231
cd /www/greenbudget-api

echo "Building"
sudo docker-compose -f docker-compose.dev.yml up --build -d

echo "Collecting Static Files"
docker-compose -f docker-compose.dev.yml exec web python manage.py collectstatic -c --no-input

echo "Running Migrations"
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate

echo "Restarting..."
docker-compose -f docker-compose.dev.yml restart