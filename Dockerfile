FROM python:3.8

WORKDIR /root/synapsemonitor
COPY . .
RUN pip install .

ENTRYPOINT [ "synapsemonitor" ]
