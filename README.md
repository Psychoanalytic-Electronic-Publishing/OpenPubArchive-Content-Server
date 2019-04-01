# OpenPubArchive - Open Publications Archive Software (OPAS, working Acronym for project) 
 
(Software for online publishing of journal archives)

The purpose of this project is to produce software to publish an archive of journals to the web.  The first version is based on the requirements of Psychoanalytic Electronic Publishing (PEP), a non-profit company, who currently operate www.PEP-Web.org via commercial software to publish journals and books in the subject domain of Psychoanalysis.  The goal is to rebuild and replace that software with a completely open source alternative.  This project is sponsored and directed initially by PEP.

While the software that's part of this project is open source, the content any implementation may host does not need to be free or open source.  In the case of PEP, the content to be hosted is not, which will drive at least the default configuration described below.

The project plan is to build a server, written in Python and based on the Apache Solr engine.  It will have a RESTful interface, so that various clients can be written, which may be modules in this project or separate projects.

The rest of this file is a template for the initial project developers to fill in.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

What things you need to install the software and how to install them

```
Give examples
```

### Installing

A step by step series of examples that tell you how to get a development env running

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

Explain what these tests test and why

```
Give an example
```

### And coding style tests

Explain what these tests test and why

```
Give an example
```

## Deployment

Add additional notes about how to deploy this on a live system

## Built With

* [Dropwizard](http://www.dropwizard.io/1.0.2/docs/) - The web framework used
* [Maven](https://maven.apache.org/) - Dependency Management
* [ROME](https://rometools.github.io/rome/) - Used to generate RSS Feeds

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Authors

* **Neil R. Shapiro** - *Initial work* - [Scilab Inc.](https://github.com/nrshapiro)

See also the list of [contributors](https://github.com/nrshapiro/openpubarchive/contributors) who participated in this project.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Psychoanalytic Electronic Publishing is graciously funding this project and donating the code as Open Source to provide the resource to scholarly endevours in other fields.

* The initial requirements for this project are based on PEP-Web, PEP's current system for archived journal search and retrieval.

