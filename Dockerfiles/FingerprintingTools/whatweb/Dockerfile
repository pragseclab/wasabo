FROM ruby

RUN apt-get update && apt-get -y install git 

ADD mitmproxy-ca-cert.pem /usr/local/share/ca-certificates/mitmproxy-ca-cert.crt
RUN chmod 644 /usr/local/share/ca-certificates/mitmproxy-ca-cert.crt && update-ca-certificates

RUN git clone https://github.com/urbanadventurer/whatweb  \
&& cd whatweb \
&& make install

ENTRYPOINT ["whatweb"]
#ENTRYPOINT ["/bin/sh"]
