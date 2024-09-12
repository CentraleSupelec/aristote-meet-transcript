FROM python:3.10

WORKDIR /server_app/

RUN ln -snf /usr/share/zoneinfo/Europe/Paris /etc/localtime && echo Europe/Paris > /etc/timezone

COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY aristote.py \
    meet.py \
    /server_app/

CMD ["python3", "meet.py"]
