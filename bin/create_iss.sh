#! /bin/sh
/bin/sh bin/build_innosetup.sh > temp.txt

echo > BioImageXD.iss
while read -r line
do
   if [ "$line" = "__FILES__" ]; then
    	cat temp.txt >> BioImageXD.iss
   else

     	echo $line >> BioImageXD.iss
   fi

done < bin/BioImageXD_template.iss