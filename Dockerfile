FROM python:3.5-slim

RUN mkdir /car_share_testing/
COPY ./requirements.txt /car_share_testing/
COPY ./setup.py ./setup.py

RUN pip install --upgrade pip
RUN pip install -e .
RUN pip3 install -r /car_share_testing/requirements.txt
RUN pip3 install docker

COPY ./proto/ /car_share_testing/proto/
RUN ls /car_share_testing/proto/
RUN python3 -m grpc_tools.protoc -I /car_share_testing/proto --python_out=. --grpc_python_out=. /car_share_testing/proto/css_rpc/*.proto

WORKDIR /car_share_testing/



ENV PYTHONDONTWRITEBYTECODE=true
ENV TESTING_ENV=docker
ENV PASSWORD_HASHING_METHOD=plain
ENV ENABLE_SOCKETS=True