## Table of content
* [General info](#general-info)
* [Technologies](#technologies)
* [Setup](#setup)

## General info

AI Album is software that allows you to digitize documents or photos. It is a project focused on exploring new technologies mainly related to artificial intelligence.


## Technologies
* Python 
* PostgreSQL
* Django 



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

