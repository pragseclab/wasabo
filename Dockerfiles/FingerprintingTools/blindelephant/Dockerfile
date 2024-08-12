FROM insynchq/python2.6

RUN apt-get update && apt-get -y --force-yes install git python-pip wget python-setuptools

RUN wget --no-check-certificate https://www.crummy.com/software/BeautifulSoup/bs3/download/3.x/BeautifulSoup-3.2.2.tar.gz \ 
&& tar -xf BeautifulSoup-3.2.2.tar.gz \
&& cd BeautifulSoup-3.2.2/ \
&& python setup.py install

RUN git clone https://github.com/lokifer/BlindElephant \
&& cd BlindElephant/src && python setup.py install 

ADD mitmproxy-ca-cert.pem /usr/local/share/ca-certificates/mitmproxy-ca-cert.crt
RUN chmod 644 /usr/local/share/ca-certificates/mitmproxy-ca-cert.crt && update-ca-certificates

ADD fingerprint.py ./
ADD dbs /BlindElephant/src/blindelephant/dbs
ADD dbs /usr/local/lib/python2.7/dist-packages/blindelephant/dbs

ENTRYPOINT ["python", "fingerprint.py"]
