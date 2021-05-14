FROM python:3.6-slim-stretch
RUN apt-get update --fix-missing && \
    apt-get install -y --fix-missing --no-install-recommends \
            libopencv-dev \
            libopencv-core-dev \
            libgl1-mesa-glx
ADD requirements.txt /
RUN pip install --no-cache-dir --upgrade -r requirements.txt  --timeout 600

ADD . /app
WORKDIR /app

EXPOSE 5000
CMD [ "python" , "app.py"]
