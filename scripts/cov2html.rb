#cov2html
#generates a nice looking html for the coverage report file
# created by Miki on 19 Jun 2007
# last modified by Miki on 19 Jun 2007

#performs the stuff
#@param filename name of the file to open and read
#@param output the output
def dohtml(filename,output)
 #prepare html skeleton with internal css style
 output.puts <<HTML
<html>
 <head>
  <title>Code Coverage</title>
  <style type="text/css">
   body {
    background: white;
    color: black;
    font-family: Tahoma, Verdana, sans-serif;
    font-size: small;
    text-align: center;
   }
   table {
    border-collapse: collapse;
    border: 2px solid black;
    margin-top: 1em;
   }
   caption {
    margin-bottom: 0.5em;
    font-size: larger;
    font-weight: bold;
    font-style: italic;
   }
   th {
    background: silver;
    font-style: italic;
   }
   tr.zero {
    background: red;
   }
   tr.none {
    background: #ff8888;
   }
   tr.little {
    background: #ffcdcd;
   }
   tr.full {
    background: #bbffbb;
   }
   td {
    padding-top: 5px;
    padding-bottom: 5px;
    border: 1px solid gray;
    text-align: center;
   }
   td.file {
    font-family: Courier New, monospace;
    text-align: left;
   }
   td.file strong {
    font-weight: bold;
    text-decoration: underline;
   }
   td.coverage {
    font-weight: bold;
   }
   td.missing {
    font-size: smaller;
    text-align: justify;
    line-height: 125%;
   }
   p.info {
    font-size: x-small;
   }
  </style>
 </head>
 <body>
 <table>
  <caption>Code coverage</caption>
  <tr><th>Module name</th><th>No. of statements</th><th>Executed statements</th><th>Coverage</th><th>Not covered lines</th></tr>
HTML

 #count modules of each type
 counter={"zero"=>[0,"Zero. None.",0],
          "none"=>[0,"Almost none (less than 20%).",0],
          "little"=>[0,"Not enough (less than 75%).",0],
          "enough"=>[0,"Acceptable rate (75% and more).",0],
          "full"=>[0,"Full.",0]}

 #parse every line of given file
 IO.foreach(filename) do |line|
  if line=~/([a-zA-Z0-9\/._-]+)\s+(\d+)\s+(\d+)\s+(\d+)%(\s+([0-9, -]+))?/ then
   #assign variables according to the pattern
   modulename,statements,executed,coverage,missing=$1,$2,$3,$4,$6==nil ? "" : $6
   #determine the highlight of the row based on the coverage
   rowclass=case Integer(coverage)
                 when 1..19 then "none"
                 when 20..74 then "little"
                 when 75..99 then "enough"
                 when 100 then "full"
                 else "zero"
            end
   #increase counter if not total
   if modulename!="TOTAL" then
    counter[rowclass][0]+=1
    counter[rowclass][2]+=Integer(executed)
   else
    #emphasise TOTAL
    modulename="<strong>"+modulename+"</strong>"
   end
   # put a row of the table        
   output.puts "<tr class="+rowclass+"><td class='file'>"+modulename+"</td><td>"+statements+"</td><td>"+executed+"</td><td class='coverage'>"+coverage+"%</td><td class='missing'>"+missing+"</td></tr>\n"
  end 
 end

 #close table and put some nice summary
 output.puts "</table>"
 output.puts "<table style='width: 66%%'><caption>Summary</caption><tr><th>Coverage</th><th>Number of modules</th><th>Executed statements</th></tr>"
 total=[0,0]
 ["zero","none","little","enough","full"].each do |key|
  value=counter[key]
  total[0]+=value[0]
  total[1]+=value[2]
  output.puts "<tr class='"+key+"'><td class='coverage'>"+value[1]+"</td><td>"+String(value[0])+"</td><td>"+String(value[2])+"</td></tr>";
 end 
 output.puts "<tr><td><strong>TOTAL</strong></td><td>"+String(total[0])+"</td><td>"+String(total[1])+"</td></tr>"
 output.puts "</table>"
 output.puts "<p class=\"info\">Generated from file ["+filename+"].</p></body></html>"
end

#start here
if ARGV.size!=2 then
 puts "Coverage filename and output filename required."
else
 begin
  output=File.open(ARGV[1],"w")
  dohtml(ARGV[0],output)
 ensure
  output.close
 end
end
