FROM openzim/zimwriterfs:latest

RUN apt-get update -y
RUN apt-get install -y aria2 python3 pngquant jpegoptim imagemagick 
RUN cpan -i MIME::Types
RUN cpan -i Log::Log4perl

RUN mkdir -p /data
WORKDIR /data

COPY edunum-scraper.py /usr/bin/scraper
RUN chmod +x /usr/bin/scraper
COPY favicon.png .
COPY fonts fonts

CMD scraper
