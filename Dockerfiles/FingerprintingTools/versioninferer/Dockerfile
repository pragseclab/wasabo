FROM python:3.8

RUN apt update && apt install -y git 

ADD mitmproxy-ca-cert.pem /usr/local/share/ca-certificates/mitmproxy-ca-cert.crt
RUN chmod 644 /usr/local/share/ca-certificates/mitmproxy-ca-cert.crt && update-ca-certificates

ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

RUN git clone https://github.com/wichmannpas/VersionInferrer \
&& cp -r VersionInferrer/* ./ \
&& pip install -r requirements.txt

ADD settings_local.py ./
ADD wappalyzer_apps.json /vendor/wappalyzer_apps.json
ADD db.sqlite3 /db.sqlite3
RUN sed -i 's/HTTP_TIMEOUT = 5/HTTP_TIMEOUT = 20/g' /settings.py

RUN ./analyze_site.py --help

ENTRYPOINT ["./analyze_site.py"]
