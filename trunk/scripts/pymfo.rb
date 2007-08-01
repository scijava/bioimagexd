#!/usr/bin/ruby

# the script for analysing the output file of pymports.py
# again, it could be written better

class Modimp

 def initialize(name)
  @name=name
  @imports=[]
  @importedby=[]
 end
 
 def addImport(name)
  @imports.push(name) unless @imports.include?(name)
 end
 
 def addImportedBy(name)
  @importedby.push(name) unless @importedby.include?(name)
 end
 
 def to_s()
  result="-< START: "+@name+" >-\n"
  result+=" IMPORTS:\n"+@imports.join(",\n")+"\n" unless @imports.size==0
  result+=" IS IMPORTED BY:\n"+@importedby.join(",\n")+"\n" unless @importedby.size==0
  result+=">-  END:  "+@name+" -<\n\n"
  return result
 end
 
end

def dofile(filename,output)
 modules={}
 name=""
 IO.foreach(filename) do |line|
  if line=~/START: \[(.*?).py\]/ then
   # create a module object
   name=$1.gsub(/\//,".").gsub(/\.__init__/,"")
   modules[name]=Modimp.new(name)
  elsif line=~/((import\s+)|(from\s+))([a-zA-Z._0-9]+)/ then
   # add an import
   modules[name].addImport($4)
   # create a module that is imported if it not exists
   modules[$4]=Modimp.new($4) unless modules[$4]
   # this module is imported by
   modules[$4].addImportedBy(name)
  end
 end
 modules.keys.sort.each do |key|
  output.puts modules[key].to_s
 end 
end

puts "PYMFO - Pymports output analyser.\nWritten by Miki in 2007.\n"
if ARGV.size!=2 then
 puts "Please specify input file and output file.\n"
else
 begin
  output=File.open(ARGV[1],"w")
  dofile(ARGV[0],output)
 ensure
  output.close
 end 
 puts "Done."
end

