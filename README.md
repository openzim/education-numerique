Éducation & Numérique scraper
===

Content from [Éducation & Numérique](https://www.education-et-numerique.org/), under **CC-by-nc-sa** using a 2014 dump of the software+content.

# Usage

```
docker run -v `pwd`:/output:rw openzim/education-numerique
```
```
docker run -v /tmp:/tmp:rw openzim/education-numerique scraper --help
docker run -v /tmp:/tmp:rw openzim/education-numerique scraper --debug --outputdir /tmp --zimfname my-super-file.zim
```
