# OpenPubArchive - Open Publications Archive Software (OPAS, working Acronym for project) 
 
(Software for online publishing of journal archives)

The purpose of this project is to produce software to publish an archive of journals to the web.  The first version is based on the requirements of Psychoanalytic Electronic Publishing (PEP), a non-profit company, who currently operate www.PEP-Web.org via commercial software to publish journals and books in the subject domain of Psychoanalysis.  The goal is to rebuild and replace that software with a completely open source alternative.  This project is sponsored and directed initially by PEP.

While the software that's part of this project is open source, the content any implementation may host does not need to be free or open source.  In the case of PEP, the content to be hosted is not, which will drive at least the default configuration described below.

The project plan is to build a server, written in Python and based on the Apache Solr engine.  It will have a RESTful interface, so that various clients can be written, which may be modules in this project or separate projects.

The rest of this file is a template for the initial project developers to fill in.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

At the moment, the only pre-requisite is having the docker demon installed.
Once that's taken care of:
```
cd /CURRENT/DIRECTORY
docker-compose up
```
will start both the sftp demon, and solr.
Sftp will be accessible on port :2222, while solr will be accessible on its normal port :8983.

The address:
http://localhost:8983/solr/#/pepwebrefsproto/query
should be accessible once the services have started.

**Please note** that the index will be empty. It is then necessary to copy/move the data for the index, or insert the documents. **The index will be persisted**.

### Installing

TBD.  A step by step series of examples shall be provided (eventually here) that tell you how to get a development env running

Say what the step will be

```
Give the example
```

And repeat

```
until finished
```

End with an example of getting some data out of the system or using it for a little demo

## Running the tests

Explain how to run the automated tests for this system

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

Docker or similar technology will be used to make deployment and redeployment easy.

## Built With

* [Python]
* [Solr](http://lucene.apache.org/solr/) - Dependency Management
* Python Web framework - Flask, Falcon, Hug, Pyramid, or other!
* XML/XSLT for coding source files and transforming them

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) standards for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Authors

* **Neil R. Shapiro** - *Initial work* - [Scilab Inc.](https://github.com/nrshapiro)

Future: See also the list of [contributors](https://github.com/nrshapiro/openpubarchive/contributors) who participated in this project.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Psychoanalytic Electronic Publishing is graciously funding this project and donating the code as Open Source to provide the resource to scholarly endeavors and related projects.

* The initial requirements for this project are based on PEP-Web, PEP's current system for archived journal search and retrieval.  The requirements for PEP-Web 2021, a future version of PEP-Web, will guide design and development for at least the first release.
