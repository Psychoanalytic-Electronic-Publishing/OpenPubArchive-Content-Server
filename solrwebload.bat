e:
cd E:\usr3\GitHub\openpubarchive\app
call env\scripts\activate
cd solrXMLWebLoad
echo off
echo
echo  ------------------------------------------------------------
echo  To run all peparchive data
echo  py solrXMLPEPWebLoad.py -d X:\_PEPA1\_PEPa1v\_PEPArchive -v -f -a
echo  ------------------------------------------------------------
echo 
echo  To run all pepcurrent data
echo  py solrXMLPEPWebLoad.py -d X:\_PEPA1\_PEPa1v\_PEPCurrent -v -f -a
echo  ------------------------------------------------------------

echo To run all pepglossary data
echo  py solrXMLPEPWebLoad.py -d X:\_PEPA1\_PEPa1v\_PEPCurrent -v -g -a
echo  ------------------------------------------------------------

echo For incremental run, simply remove the -a (all) from above
echo  ------------------------------------------------------------
