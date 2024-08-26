## Table of content
* [General info](#general-info)
* [Technologies](#technologies)
* [Setup](#setup)
* [Development](#development)

## General info

AI Album is software that allows you to digitize documents or photos. It is a project focused on exploring new technologies mainly related to artificial intelligence.


## Technologies
* Python 
* PostgreSQL
* Django 
* Tailwind CSS
* Docker
* Annotorious



## Setup
Clone the repository
```console
git clone https://github.com/AI-USS/ai-album.git
```

Create .env file with SECRET_KEY and DEBUG

```console
cd ai-album/
printf "SECRET_KEY=[random seq]\nDEBUG=True" > .env
```

Install requirements from a file

```console
conda create --name ai-album -c conda-forge --file req.txt
```

Add to file .env keys and values like:
```console
PGNAME=ALBUM
PGUSER=admin
PGPASSWORD=ABC
PGHOST=0.0.0.0
PGPORT=5432
```


## Development 


```console
docker compose up -d

python manage.py runserver

python manage.py tailwind start
```

After installed new python packeage use:
```console
pip list --format=freeze > req.txt
```

