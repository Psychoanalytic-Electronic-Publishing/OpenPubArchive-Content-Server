# OpenPubArchive - Open Publications Archive (Content) Server (OPAS)

Software for producing and providing a content server with a database of searchable archives of academic publications (including journals, books and transcribed videos).

The purpose of this project is to produce software to provide a searchable archive of academic publications on the web. The supplied version is based on the requirements for academic publications in the area of Psychoanalysis, but it should be easily generalizable to any academic area. Specifically, this software is designed and developed based on the requirements of Psychoanalytic Electronic Publishing (PEP), a non-profit company, who currently operate www.PEP-Web.org via commercial software to publish journals and books in the subject domain of Psychoanalysis. This project was completely sponsored by PEP.

PEP originally used v1 of the API in this project to provide an API around it's original journal database, which was written by Global Village Publishing and based on DTSearch. When PEP needed to replace that system, we decided to develop and make the content server open source.

While the software that's part of this project is open source, the content any implementation may host does not need to be free or open source. In the case of PEP, the content to be hosted is not, which will drive at least the default configuration described below.

The server is written in Python and based on the Apache Solr full-text search engine, and a MySQL based database, with a RESTful interface. It exposes all functionalty as an API, so that various clients can be written, which may be modules in this project or separate projects.

The server exposes a interactive OpenAPI interface at /docs/ which, besides testing and demonstrating features, can also be used to export the specification for OPAS in OpenAPI 3.0 compatible syntax, or HTML (requires permission via an API Key).

All references to the distribution below use the main folder, openpubarchive, as the root (.)

## Primary Components

1. Server with Restful API written in Python 3 using FastAPI - this is the main component, it provides an API to do queries against the journal, books, and videos stored
   `./app/main.py`
2. An app (Python 3) for a clean full load of PEP XML text (KBD3 DTD) into Solr with some metadata loaded into the MySQL compatible database
   `./app/opasDataLoader/opasDataLoader.py`
3. An app (Python 3) for updating MySQL and Solr with metadata about documents and statistical data about document usage, to be run each time after a clean load of data using opasDataLoader, and weekly or more often to update the data.
   `./app/opasDataUpdateStat/opasDataUpdateStat.py`
4. A Python 3 app for copying the api_client_configs table from a staging DB (MySQL) to the Production DB (MySQL) to transfer settings when "pushing" admin configurations from Stage to Production
   `./app/opasPushSettings/opasPushSettingsToProduction.py`

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

- Python 3.
- Python 3 compatible libraries per requirements.txt files within the main APP folder and component subfolders where needed
- [FastAPI](https://fastapi.tiangolo.com/) provides a fast, modern, API infrastructure, with a OpenAPI front end for trying out the endpoints.
- [Solr 8.x or newer](http://lucene.apache.org/solr/).
- A [MySQL](https://dev.mysql.com/downloads/) compatible database for data recording and some configuration data, e.g., MySQL or AWS RDS

* solrpy A convenience Python library for Solr. - original library used--still used for one feature, but due to some problems, switched to pysolr.
* pysolr A convenience Python library for Solr. - Main library used.
* Python Web framework - [FastAPI](https://github.com/tiangolo/fastapi) (see [Requirements.txt] for complete list)
* [XSLT](https://lxml.de/xpathxslt.html) via LXML for coding source files and transforming them
* [XML/DTD](http://peparchive.org/pepa1dtd/pepkbd3.dtd) The initial (base) version of the server schemas and imports is based on PEP's KBD3 DTD which is the document markup implemented in books and articles in PEP-Web. It can readily be adapted for other DTDs though.
* (Optional) [Docker](https://docs.docker.com/get-docker/)

### General Install Instructions

1. Download the OpenPubArchive-Content-Server (API) source
   Go to a local folder where you want to install in a subfolder, and run:

   `git clone https://github.com/Psychoanalytic-Electronic-Publishing/OpenPubArchive-Content-Server.git .`

2. Install Solr
   The repository contains a sample [docker-compose.yml](https://github.com/Psychoanalytic-Electronic-Publishing/OpenPubArchive-Content-Server/blob/Stage/docker-compose.yml) file if you would like to install using Docker. It can be executed by running `docker-compose up`
   The PEP schemas for three Solr cores (pepwebdocs, pepwebauthors, pepwebglossary are included). The compose file points to a local folder where you can persist the solr database (if you point to wherever you put folder ./solrCoreConfigurations/data, when Solr is started, the schemas will load automatically.)

3. Install or Set up a MySQL compatible database (e.g., MySQL or RDS)
   a. On AWS, PEP uses RDS.
4. Load the SQL schemafile into MySQL. It can be found in the ./sql folder
5. Run the OPAS app
   1. Rename the supplied localsecrets file, `localsecrets_fillin_and_change_name_to_localsecrets` to `localsecrets.py`
   1. Customize the localsecrets.py file to point to the Solr and MySQL database and provide the usernames and passwords that provide full access.
   1. Build and run
      - With Docker:
        1. Build docker image
           `docker build -t opas-api .`
        1. Run docker image
           `docker run opas-api`
      - Without Docker:
        1. Create virtual environment and install dependencies
           ```
           Windows:
           install.bat
           Unix:
           sh install.sh
           ```
        1. Run app
           ```
           Windows:
           app\serverstart.bat
           Unix:
           sh app/serverstart.sh
           ```

### Schema

There is currently no "sample schema" set provided. The schemas are included in the repository but are fairly complex and are all very specific to PEP's data. At the project close, we shall aim to develop a sample schema set.

The current schemas provided are the PEP-Web schemas:

1. pep-web-docs - the main document (book, article and transcribed video) solr core/database
2. pep-web-glossary - the pep consolidated glossary solr core/database used by the glossary endpoint.
3. pep-web-authors - a database of article authors in a solr core/database

## Running the tests

The source includes a set of tests intended to detect broken features during development using the pytest platform. It is, of course, schema dependent.

To test the Python API/Server code, there are both docstring tests and unittests.

To run the unittests, you must first set the python environment to the env folder and then run the tests. E.g., from the App folder:

```
Windows:
.\env\scripts\activate
.\env\scripts\python -m unittest discover tests

Unix systems:
source ./env/bin/activate
cd app
python -m unittest discover tests
```

From Windows you can also just run the batch file `app/testsuite.bat` to do all of the above for testing or `sh app/testsuite.sh` for unix systems.

## Versioning

We use a simple date + build number version numbers during Version 1 development:

We will prefix the date to [SemVer](http://semver.org/) standards for versioning with the first release version.

For the versions available, see the [tags on this repository](https://githuhttps://github.com/Psychoanalytic-Electronic-Publishing/openpubarchive/tags).

A changelog with more details than github can be found in CHANGELOG.MD:

## Authors

See the list of [contributors](https://github.com/Psychoanalytic-Electronic-Publishing/openpubarchive/openpubarchive/contributors) who participated in this project.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

- Psychoanalytic Electronic Publishing is graciously funding this project and donating the code as Open Source to provide the resource to scholarly endeavors and related projects.

- The initial requirements for this project are based on PEP-Web, PEP's current system for archived journal search and retrieval. The requirements for PEP-Web 2021, a future version of PEP-Web, will guide design and development for at least the first release.
