call setenv
cd OpasDataLoader
python opasdataloader.py --nocheck -d X:\_PEPA1\_PEPa1v\_PEPFree
start python opasdataloader.py --nocheck -d X:\_PEPA1\_PEPa1v\_PEPOffsite
start python opasdataloader.py --nocheck -d X:\_PEPA1\_PEPa1v\_PEPCurrent
start python opasdataloader.py --nocheck -d X:\_PEPA1\_PEPa1v\_PEPCurrent --reverse
start python opasdataloader.py --nocheck -d X:\_PEPA1\_PEPa1v\_PEPArchive
python opasdataloader.py --nocheck -d X:\_PEPA1\_PEPa1v\_PEPArchive --reverse
cd ..\OpasDataUpdateStat
python opasDataUpdateStat.py --all