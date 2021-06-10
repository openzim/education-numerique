FROM ubuntu:20.04

ENV TZ=UTC
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends wget aria2 python3 pngquant jpegoptim imagemagick libmagic-dev perl perl-modules ca-certificates && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*

RUN update-ca-certificates

RUN wget -L http://download.openzim.org/release/zim-tools/zim-tools_linux-x86_64-2.1.0-1.tar.gz \
    && tar xf zim-tools_linux-x86_64-2.1.0-1.tar.gz \
    && mv zim-tools_linux-x86_64-2.1.0-1/zim* /usr/bin/ \
    && rmdir zim-tools_linux-x86_64-2.1.0-1

RUN PERL_MM_USE_DEFAULT=1 cpan -i MIME::Types Log::Log4perl

RUN mkdir -p /data
WORKDIR /data

COPY edunum-scraper.py /usr/bin/scraper
RUN chmod +x /usr/bin/scraper
COPY favicon.png .
COPY fonts fonts

CMD scraper
