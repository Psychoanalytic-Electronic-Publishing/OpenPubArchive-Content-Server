# openpubarchive
Software for online publishing of journal archives - Open Publications Archive Software (OPAS, working Acronym for project) 

The purpose of this project is to produce software to publish an archive of journals to the web.  The first version is based on the requirements of Psychoanalytic Electronic Publishing (PEP), a non-profit company, who currently operate www.PEP-Web.org via commercial software to publish journals and books in the subject domain of Psychoanalysis.  The goal is to rebuild and replace that software with a completely open source alternative.  This project is sponsored and directed initially by PEP.

While the software that's part of this project is open source, the content any implementation may host does not need to be free or open source.  In the case of PEP, the content to be hosted is not, which will drive at least the default configuration described below.

The project plan is to build a server, written in Python and based on the Apache Solr engine.  It will have a RESTful interface, so that various clients can be written, which may be modules in this project or separate projects.

The server will permit the upload of documents in XML and text-based PDF formats, as a core.  Uploads will be via FTP, with a web interface to start ingestion.  The FTP target site will ingest documents organized in file trees by copyright restrictions: Archive, Current, and Free, as PEP's existing system does. These file trees correspond to predefined embargo periods for the content, where Current documents may be time embargoed so that the full content may not be viewable to end users until the embargo period ends.  Moving documents from one file tree to another is a simple way to manipulate the embargo, but it may also optionally be done and supported by metadata tagging embargo dates.

A "OPA Admin" web page will be used to initiate ingestion, and will provide live progress indications.  The FTP target site will maintain the current documents uploaded, and thus the system can be updated and additional documents uploaded by adding to the file trees.  All XML files must be valid per the designated DTD, or errors will be logged.  The error status and log file shall be accessible via the admin page.  

A fourth FTP file tree, PDFOriginals, will contain a set of original PDF files which are included as support files, not indexed.  These support files will be the original scans or textual PDFs for the XML files indexed by the system.  These are provided administrators and end users to verify the accuracy of the XML archives, as well as show original formatting.  These files are not required, but where provided, will match the file names of any indexed XML documents in the ingested tree.

Access to the documents in the Archive will be controlled by a user-id/password system initially.  Adding users and their permissions will be done manually by designated administrative users, as part of the admin web pages, rather than a user-initiated sign up form, initially.  Eventually, the user security system will be enhanced to included other forms of authentication, including IP authentication and federated login via OpenAthens and Shibboleth.

A third group of administrative pages will be used to verify and test the document database.  This will consist of a table of document counts by document categories (journal/book/video, year, embargo type) and a query capability, where a list of matching documents can be displayed for any queried metadata field, and the specific document viewed in source form by selecting one of the list entries.

A second phase of the project will focus on adding RESTful interface to allow client applications to be used to access the data, including end-user and client-developer authentication.  Sample clients may be included, but real-use clients will be developed under a separate project. 
