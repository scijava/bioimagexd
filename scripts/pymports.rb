#!/usr/bin/ruby
# PYMPORTS

# scans the directory for .py files and extracts import statements
# shows the places where dynamic __import__ is used

# a bit messy
# can be written in million better ways ;)
# since there's no ruby in linux here, this one works ONLY for Windows 

#searches the file
#@param file name of the file
#@param output output file
def dofile(file,output)
 # we are using the fact that the path will be given by \ in command line, so / is added by ruby
 filename=file[file.index("/")+1..file.size]
 output.puts "*** START: ["+filename+"] ***\n"
 IO.foreach(file) do |line|
  output.puts line.lstrip if (line=~/^\s*import\s+/ or line=~/from\s+\w+\s+import\s+/) and not (line=~/^\s*#/)
  output.puts "! Dynamic import !\n" if line=~/__import__/
 end
 output.puts "***  END:  ["+filename+"] ***\n"
end

#scans the directory and processes the files .py
#@param dirname name of the directory
#@param output output file
def dodir(dirname,output)
 Dir.foreach(dirname) do |content|
  if(content!="." and content!=".." and not content=~/^\./) then
   begin
    if(File.directory?(dirname+'/'+content)) then
     output.puts "--- START: ["+content+"] ---\n"
     dodir(dirname+'/'+content,output)
     output.puts "---  END:  ["+content+"] ---\n"
    else
     dofile(dirname+'/'+content,output) if content=~/.py$/
    end
   end 
  end 
 end
end

#main part
puts "PYMPORTS 0.1 - Written by MIKI in 2007\n"
dirmode=ARGV.index("-d")!=nil
output=ARGV.index("-o")
 
#there is at least one required parameter
reqparam=1
#two parameters extra if output provided
reqparam+=2       if output!=nil
#one extra if dirmode
reqparam+=1       if dirmode 

if ARGV.size!=reqparam then
 puts "Filters Python files so that they show only import statements\n\n"
 puts "Usage:\n"
 puts "  pymports [OPTIONS] NAME\n"
 puts "where OPTIONS are one or more following options:\n"
 puts "  -o FILENAME      - write output to given file\n"
 puts "                     (create if not exists, rewrite if exists)\n"
 puts "  -d               - directory mode, treat NAME as a directory\n"
 puts "                     and process it recursively\n"
 puts "and NAME is the name of the file (or, if -d used, a directory).\n\n"
else
 begin 
  outfile=output==nil ? STDOUT : File.open(ARGV[output+1],"w")
  puts "Output file:    ["+outfile.path+"]\n"  if output!=nil
  puts "Directory mode on\n"                      if dirmode
  puts "Processing:     ["+ARGV.last+"]\n"
  if dirmode then
   dodir(ARGV.last,outfile)
  else
   dofile(ARGV.last,outfile)
  end
 ensure
  outfile.close if output!=nil
 end
 puts "...done.\n"
end
