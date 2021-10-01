FROM ubuntu:20.04 AS gunicorn_fastapi

RUN TZ="Asia/Bangkok" && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezoneT && \
    apt-get update && apt-get update --fix-missing && \
    apt-get install -y python3 python3-pip && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    python -m pip install --upgrade pip && \
    pip --version && \
    mkdir /app && \
    chmod 777 /app

WORKDIR /app
COPY ./requirements.txt /app

## Imstall llvm and numba seprately due to ARM64 problem
RUN pip install --no-cache-dir -r requirements.txt 
#install --pre torch torchvision -f https://download.pytorch.org/whl/nightly/cpu/torch_nightly.html
#pip install torch==1.8.1+cpu torchvision==0.9.1+cpu torchaudio==0.8.1 -f https://download.pytorch.org/whl/lts/1.8/torch_lts.html
#COPY ./engine-sg.json /app/credential.json

COPY ./ /app

#ENV GOOGLE_APPLICATION_CREDENTIALS=credential.json
EXPOSE 80
EXPOSE 443
EXPOSE 27017



ARG THREADS=10
ARG MONGO_HOST=mongo
ARG MONGO_USER=root
ARG MONGO_PW=secret
ARG MARIADB_HOST=mariadb
ARG MARIADB_ROOT_USER=root
ARG MARIADB_ROOT_PASSWORD=secret
ARG SECRET_KEY=51671eddeef043bf64df9344cffd66fa82b30a26e1bb805425d194add860394d

ENV THREADS=${THREADS}
ENV MONGO_HOST=${MONGO_HOST}
ENV MONGO_USER=${MONGO_USER}
ENV MONGO_PW=${MONGO_PW}
ENV MARIADB_HOST=${MARIADB_HOST}
ENV MARIADB_ROOT_USER=${MARIADB_ROOT_USER}
ENV MARIADB_ROOT_PASSWORD=${MARIADB_ROOT_PASSWORD}
ENV SECRET_KEY=${SECRET_KEY}
ENV CACHE_DIR=/tmp
# Expose mongodb

CMD bash start.sh

FROM gunicorn_fastapi AS gunicorn_fastapi_test
RUN apt-get install -y git python3.8-venv && \
    pip install yapf pylint notebook jupyter_contrib_nbextensions && \
    jupyter contrib nbextension install && \
    python3 -m pip install --upgrade build twine