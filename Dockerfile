FROM python:3.10

RUN apt-get update -y && apt-get upgrade -y

WORKDIR /server_app/

RUN ln -snf /usr/share/zoneinfo/Europe/Paris /etc/localtime && echo Europe/Paris > /etc/timezone

COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./ /server_app/

CMD ["flask", "--app=meet", "run", "--host=0.0.0.0", "--debug"]
