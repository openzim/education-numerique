# Éducation & Numérique scraper

Content from [Éducation & Numérique](https://www.education-et-numerique.org/), under **CC-by-nc-sa** using a 2014 dump of the software+content.

[![Docker](https://ghcr-badge.deta.dev/openzim/education-numerique/latest_tag?label=docker)](https://ghcr.io/openzim/education-numerique)
[![CodeFactor](https://www.codefactor.io/repository/github/openzim/education-numerique/badge)](https://www.codefactor.io/repository/github/openzim/education-numerique)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Usage
-----

```bash
docker run -v `pwd`:/output:rw openzim/education-numerique
```

or

```bash
docker run -v /tmp:/tmp:rw ghcr.io/openzim/education-numerique scraper --help
docker run -v /tmp:/tmp:rw ghcr.io/openzim/education-numerique scraper --debug --outputdir /tmp --zimfname my-super-file.zim
```

License
-------

[GPLv3](https://www.gnu.org/licenses/gpl-3.0) or later, see
[LICENSE](LICENSE) for more details.
