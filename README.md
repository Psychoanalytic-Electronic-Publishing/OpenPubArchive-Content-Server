# OpenPubArchive - Open Publications Archive Software (OPAS) 
 
(Software for online publishing of journal archives)

The purpose of this project is to produce software to publish an archive of journals to the web.  The first version is based on the requirements of Psychoanalytic Electronic Publishing (PEP), a non-profit company, who currently operate www.PEP-Web.org via commercial software to publish journals and books in the subject domain of Psychoanalysis.  The goal is to rebuild and replace that software with a completely open source alternative.  This project is sponsored and directed initially by PEP.

While the software that's part of this project is open source, the content any implementation may host does not need to be free or open source.  In the case of PEP, the content to be hosted is not, which will drive at least the default configuration described below.

The project plan is to build a server, written in Python and based on the Apache Solr engine.  It will have a RESTful interface, so that various clients can be written, which may be modules in this project or separate projects.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

- The server is written in Python.  
- It uses Solr as it's own backend.  
- [FastAPI](https://fastapi.tiangolo.com/) provides a fast, modern, API infrastructure, with a OpenAPI front end for trying out the endpoints.
- It uses a structured, SQL database for data recording and some configuration data: Currently, either MySQL or AWS RDS
- The configuration itself is specific to PEP's needs.  The configuration/addressing of these components is in a private .py file called localsecrets.  For PEP, it's been setup so it can be switched quickly between local running on a PC, and running on AWS, or a hybrid of the two.

### Setup

Server local install requires Solr, MySQL, and Python.  

#TODO DevOPS.

### Schema

There is currently no "sample schema" set provided.  The schemas are included in the repository but are fairly complex and are all very specific to PEP's data.  At the project close, we shall aim to develop a sample schema set.

### Installing

#TODO DevOPS.  

A step by step series of examples shall be provided (eventually here) that tell you how to get a development env running without giving direct security info here.

## Running the tests

The source includes a set of tests intended to detect broken features during development using the pytest platform.  It is, of course, schema dependent.

To test the Python API/Server code, there are both docstring tests and unittests.  To run the unittests, go to the test folder and run the batch file testsuite.bat:

./testsuite - in Windows, or the equiv in Unix environments.  Basically, you must first set the python environment to the env folder and then run the tests.  E.g., from the App folder:

.\env\scripts\activate
.\env\scripts\python -m unittest discover tests

### Break down into end to end tests

An initial test set for Phase I will be developed and consist of queries against the various parts of the schema and to make sure query results make sense in terms of term weighting (e.g., albino elephant problem) and global search versus fielded.  

```
http://lucene.472066.n3.nabble.com/The-downsides-of-not-splitting-on-whitespace-in-edismax-the-old-albino-elephant-prob-td4327440.html
```

### And coding style tests

Code should be well commented in English.
Python code should follow style guidelines, e.g.,

```
http://google.github.io/styleguide/pyguide.html
```

## Deployment

Docker will be used to make deployment and redeployment easy.

## Built With

* [Python 3]
* [Solr](http://lucene.apache.org/solr/) - Dependency Management
* solrpy A convenience Python library for Solr. - still used for one feature, but due to problems, mostly isolated
* pysolr A convenience Python library for Solr. - Main library used.
* Python Web framework - [FastAPI](https://github.com/tiangolo/fastapi) (see [Requirements.txt] in APP for complete list)
* [MySQL](https://dev.mysql.com/downloads/)
* [XSLT](https://lxml.de/xpathxslt.html) via LXML for coding source files and transforming them
* [XML/DTD](http://peparchive.org/pepa1dtd/pepkbd3.dtd) The initial (base) version of the server schemas and imports is based on PEP's KBD3 DTD which is the document markup implemented in books and articles in PEP-Web.  It can readily be adapted for other DTDs though.
* [PEP-Web API](https://app.swaggerhub.com/apis/nrshapiro/PEP-Web/1.1.0) The initial (base) version of the server API will be largely based on the PEP-Web 1.0 Open API implemented in the current PEP-Web system in order to allow a mostly unmodified version of the PEP-Easy front end to work with the server.  As PEP embarks on new, more functional client developments, this will be expanded.  Incompatible endpoints in the expanded API will be V2 endpoints, whereas anything compatible (such as those not used in PEP-Easy) will be marked as V1 endpoints.  Note that the server itself will provide [OpenAPI](https://www.openapis.org/) based documentation via FastAPI's built-in /docs endpoint.

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) standards for versioning. We will use the build date as year.moday as the first two parts of the version numbers followed by a sequential differentiating number for any given day in case there are more than one builds for that day.

For the versions available, see the [tags on this repository](https://githuhttps://github.com/Psychoanalytic-Electronic-Publishing/openpubarchive/tags). 

A changelog with more details than github can be found in CHANGELOG.MD: 

## Authors

See the list of [contributors](https://github.com/Psychoanalytic-Electronic-Publishing/openpubarchive/openpubarchive/contributors) who participated in this project.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Psychoanalytic Electronic Publishing is graciously funding this project and donating the code as Open Source to provide the resource to scholarly endeavors and related projects.

* The initial requirements for this project are based on PEP-Web, PEP's current system for archived journal search and retrieval.  The requirements for PEP-Web 2021, a future version of PEP-Web, will guide design and development for at least the first release.
