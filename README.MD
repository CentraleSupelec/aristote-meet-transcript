# Aristote Meet Transcript

This project was completed in a few hours during the "100days Challenge" hackathon on 9/12/24 and aims to retrieve the audio file of an Meet meeting, send out the transcript, and email it with an audio summary.

- Generating transcript and summary using Aristotle API
- By sending it to the backend of Meet, which will generate an email for each participant

## Copy environments file into local ones

```sh
cp -f .env.dist .env
```

## Run it

```sh
docker run --env-file .env -it -p 5000:5000 centralesupelec/aristote-meet-transcript:latest
```

Helm charts are available in [helm/](helm) directory

## Developpment

### Requirements

- python > 3.10

### Install python dependencies

For local development, create a virtual environment and activate it :

```sh
python3 -m venv env
source env/bin/activate
```

```sh
pip install -r requirements.txt
```

Change environment variables if necessary, particularly fill AristoteAPI credentials (the API Client) and the end-user-identifier to distingues the enrichment requests coming from this project.

## Start server

```sh
python3 meet.py
```
