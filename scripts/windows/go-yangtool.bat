@echo off
echo Run the yang tool.
set a=%1
set b=%2
set c=%3
set d=%4
set e=%5
set f=%6
set g=%7
set h=%8
set i=%9
shift /0  
set y=%9 
shift /1  
set x=%9
set pa=%a% %b% %c% %d% %e% %f% %g% %h% %i% %y% %x%


python ..\..\code\convert2yang.py ^
       --config ..\..\config\yangtool.conf ^
       --section windows ^
       --verbose ^
       %pa%
       
       