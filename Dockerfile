FROM python:3.8

WORKDIR /root/synapsemonitor
COPY . .
RUN pip install --no-cache-dir .

ENTRYPOINT [ "synapsemonitor" ]
