FROM openzim/zimwriterfs:1.3.5

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends aria2 python3 pngquant jpegoptim imagemagick && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*

RUN cpan -i MIME::Types
RUN cpan -i Log::Log4perl

RUN mkdir -p /data
WORKDIR /data

COPY edunum-scraper.py /usr/bin/scraper
RUN chmod +x /usr/bin/scraper
COPY favicon.png .
COPY fonts fonts

CMD scraper
