FROM python:3.10-slim

COPY ./requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

WORKDIR /app

COPY ./config/mkdocs.yml mkdocs.yml

RUN mkdir docs
RUN mkdir static

RUN mkdocs build

EXPOSE 8000

ENTRYPOINT ["mkdocs"]
