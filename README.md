# recipe-drf-api-202304

---

# Docker Commands

## Docker

### Run Project
```bash
docker-compose up
```

### Clear Any Containers
```bash
docker-compose down
```

### Build Container
```bash
docker-compose build
```

### List Volumes on the System
```bash
docker volume ls
```

### Remove a Volume on the System
```bash
docker volume rm <name-of-project_name-of-db>
```

---


## Django

### Create Django Project
```bash
docker-compose run --rm app sh -c "django-admin startproject app ."
```

### Create Django App
```bash
docker-compose run --rm app sh -c "python manage.py startapp core"
docker-compose run --rm app sh -c "python manage.py startapp user"
docker-compose run --rm app sh -c "python manage.py startapp recipe"
```

### Create Django Superuser
```bash
docker-compose run --rm app sh -c "python manage.py createsuperuser"
```

### Create Django Model Migragtions
```bash
docker-compose run --rm app sh -c "python manage.py makemigrations"
```

### Apply Django Model Migragtions
```bash
docker-compose run --rm app sh -c "python manage.py wait_for_db && python manage.py migrate"
```

### Run `flake8` through __Docker Compose__
```bash
docker-compose run --rm app sh -c "flake8"
docker-compose run --rm app sh -c "python manage.py wait_for_db && flake8"
```

### Run `tests` through __Docker Compose__
```bash
docker-compose run --rm app sh -c "python manage.py test"
```