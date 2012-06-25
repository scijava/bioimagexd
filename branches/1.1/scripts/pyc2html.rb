#pycode 2 html formatter

def docstringRow(line)
 if line=~/^Docstring found/ then
#  puts "<tr class='ok'><td class='name'>Docstring</td><td>Found</td></tr>"
  return true
 else
  puts "<tr class='warning'><td class='name'>Docstring</td><td>Not found</td></tr>"
  return false
 end #if
end

def codelines(number)
 rowclass=case number
            when   0..149 then "ignore"
            when 150..299 then "warning"
            else "error"
           end
 puts "<tr class='"+rowclass+"'><td class='name'>Code lines</td><td>"+String(number)+"</td></tr>"
end

def html()
  strp1=<<HTML
<html>
 <head>
  <title>Code statistics</title>
  <style type="text/css">
   body {
    background: white;
    color: black;
    text-align: center;
    font-family: Tahoma, Verdana, Arial, sans-serif;
   }
   h2 {
    text-align: center;
    font-size: large;
    font-family: Courier New, monospace;
    letter-spacing: 2px;
    font-weight: bold;
    margin: 0
    padding: 0
    margin-top: 0.3em;
   }
   hr {
    height: 2px;
    color: black;
   }
   table {
    border-collapse: collapse;
    margin-bottom: 1em;
    font-size: smaller;
    border: 3px solid black;
    width: 100%;
   }
   table caption {
    font-size: larger;
    font-weight: bold;
    color: navy;
   }
   table.class {
    width: 90%;
   }
   table.summary {
    border: 2px solid black;
    width: 75%;
   }
   th {
    font-weight: bold;
    font-style: italic;
   }
   tr {
    border-top: 1px solid gray;
    border-bottom: 1px solid gray;
   }
   tr.ok {
    background: #bbffbb;
   }
   tr.warning {
    background: #ffcdcd;
   }
   tr.error {
    background: red;
   }
   td.name {
    font-style: italic;
    width: 40%;
   }
   td {
    border: 1px solid gray;
    text-align: center;
   }
   tr.new td {
    border-top: 2px solid black;
   }
   td.init {
    color: navy;
    font-weight: bold;
    background: silver;
   }
   td.static {
    color: maroon;
    font-weight: bold;
    background: silver;
   }
   p.info {
    font-size: x-small;
   }
  </style>
 </head>
 <body>
HTML
 return strp1
end

def dohtml(input)
 puts html()

 inclass=false
 instruct=false
 count=0
  
 # real parsing here
 until count>input.size
  #read two lines ahead
  line=input[count]
  nextline     = count+1>=input.size ? "" : input[count+1]
  #process
  #beginning of a file
  if line=~/^--- FILE: \[([a-zA-Z0-9_\/.-]+)\]/ then
   puts "<h2>"+$1+"</h2>"
  #end of the file
  elsif line=~/^--- END:/ then
   puts "</table>"
   puts "<hr/>"
  #structure start
  elsif line=~/^-- STRUCTURE --/ then
   begin
    instruct=true
    puts "<table><caption>Module structure</caption><tr><th>Type</th><th>Value</th></tr>"
    count=count+1 if docstringRow(nextline)
   end
  elsif line=~/^Code lines: (\d+)$/ and instruct then
   codelines(Integer($1))
  #usual or class methods
  elsif line=~/^((Class m)|(M))ethod: ([a-zA-Z0-9_]+)/ then
   #if inclass and have a new non-class method, close class table
   if inclass and $3!=nil then
    puts "</table></td></tr>"
    inclass=false
   end
   #if a name is __init__, mark it somehow
   initmodifier= $4=="__init__" ? " class='init'" : ""
   puts "<tr class='new'><td class='name'>Method</td><td"+initmodifier+">"+$4+"</td></tr>"
   count=count+1 if docstringRow(nextline)
  #static methods
  elsif line=~/^Static method: ([a-zA-Z0-9_]+)/ then
   puts "<tr class='new'><td class='name'>Static method</td><td class='static'>"+$1+"</td></tr>"
   count=count+1 if docstringRow(nextline)
  #classes
  elsif line=~/^Class: ([a-zA-Z0-9_]+)/ then
   #close previous class table, if needed
   puts "</table></td></tr>" if inclass
   inclass=true
   #open class table
   puts "<tr><td colspan='2'><table class='class'><caption>"+$1+"</caption><tr><th>Type</th><th>Value</th></tr>"
   count=count+1 if docstringRow(nextline)    
  #summary part starts
  elsif line=~/^-- ((SUMMARY)|(STATS)) --/ then
   puts "</td></tr></table>" if inclass
   puts "</table>"
   instruct=false
   inclass=false
   puts "<table class='summary'><caption>"+$1.capitalize+"</caption><tr><th>Name</th><th>Value</th></tr>"
  #any summary
  elsif line=~/^([a-zA-Z0-9 \(\),]+):\s+([a-zA-Z0-9_., \(\)]+)$/ then
   puts "<tr><td class='name'>"+$1+"</td><td>"+$2+"</td></tr>"
  end #end if line...
  #go to next line
  count=count+1 
 end  #end until
 
 now=Time.new
 strp2=String(now.year)+"-"+(now.month<10 ? "0"+String(now.month) : String(now.month))+"-"+String(now.day)+" "+String(now.hour)+":"+String(now.min)+":"+String(now.sec)
 puts "<p class='info'>Generated on "+strp2+".</body></html>"  
end

# starts here

if ARGV.size>1 then
 puts "At most one parameter as input is accepted."
else
 input=ARGV.size==1 ? IO.readlines(ARGV[0]) : STDIN.readlines
 # render html to standard output
 dohtml(input)
end
