class StatMaker
 def initialize(ainputname,aoutput)
  @inputname=ainputname
  @output=aoutput
  
  @classes=0
  @methods=0
  @classmethods=0
  @staticfunctions=0
  @imports=0
  @comments=0
  @empty=0
  @docstrings=0
  @docstringlines=0
  @lines=0
  @functionlines=0
  @totalfunctionlines=0
  @longestfunction=[0,""]
  @currentfunction=""
  @static=false 
  @indocstring=false
  @inits=0
 end

 private
  def newBlock()
   @output.puts "Code lines: "+String(@functionlines) unless @functionlines==0
   @totalfunctionlines=@totalfunctionlines+@functionlines
   @longestfunction=[@functionlines,@currentfunction] if @longestfunction[0]<@functionlines and @currentfunction!=""    
   @functionlines=0
  end

  def newClass(name)
   newBlock()
   @output.puts "Class: "+name
   @classes=@classes+1
  end

  def newMethod(name,hasSelf=false)
   newBlock()
   @currentfunction=name
   if hasSelf then
    @output.puts "Class method: "+name
    @classmethods=@classmethods+1
   elsif not @static
    @output.puts "Method: "+name
    @methods=@methods+1
   else
    @output.puts "Static method: "+name
    @staticfunctions=@staticfunctions+1
    @static=false
   end
   # there might be a module init function
   @inits=@inits+1 if name=="__init__"
  end
  
  def import()
   @imports=@imports+1
  end
  
  def comment()
   @comments=@comments+1
  end
  
  def empty()
   @empty=@empty+1
  end
  
  def line()
   @lines=@lines+1
  end
  
  def docstringline()
   @docstringlines=@docstringlines+1
  end
  
  def functionline()
   @functionlines=@functionlines+1
  end
  
  def static()
   newBlock()
   @static=true
  end
  
  def docstring()
   if @indocstring then
    @indocstring=false
    @output.puts "Docstring found."
   else
    @docstrings=@docstrings+1
    @indocstring=true
   end
  end
 
 public
  #shows summary 
  def summary()
   @output.puts "-- SUMMARY --"
   @output.puts "Static imports:     "+String(@imports)
   @output.puts "Module functions:   "+String(@methods)
   @output.puts "Classes:            "+String(@classes)
   @output.puts "Methods in classes: "+String(@classmethods)
   @output.puts "Static methods:     "+String(@staticfunctions)
   @output.puts "Docstring blocks:   "+String(@docstrings)
   @output.puts "Docstring lines:    "+String(@docstringlines)
   @output.puts "Comment lines:      "+String(@comments)
   @output.puts "Empty lines:        "+String(@empty)
   @output.puts "Code lines:         "+String(@totalfunctionlines)
   @output.puts "Total lines:        "+String(@lines)
  end
 
  #shows various stats
  def stats()
   @output.puts "-- STATS --"
   @output.puts "Methods per class:                     "+String((((@staticfunctions+@classmethods)*1000)/@classes)/1000.0) if @classes>0
   zmp1=@methods+@classmethods+@staticfunctions
   @output.puts "Average function length:               "+String(((@totalfunctionlines*1000)/zmp1)/1000.0) if zmp1>0
   @output.puts "Longest function:                      "+@longestfunction[1]+", "+String(@longestfunction[0])+" lines" if @longestfunction[1]!=""
   @output.puts "Average docstring length:              "+String(((@docstringlines*1000)/@docstrings)/1000.0) if @docstrings>0
   if @lines>0 then
    commperc=((@comments*10000)/@lines)/100.0
    docsperc=((@docstringlines*10000)/@lines)/100.0
    @output.puts "Percentage of comments:                "+String(commperc)
    @output.puts "Percentage of docstrings:              "+String(docsperc)
    @output.puts "Total documentation percentage:        "+String(commperc+docsperc)
    @output.puts "Percentage of code lines:              "+String(((@totalfunctionlines*10000)/@lines)/100.0)
    @output.puts "Percentage of empty lines:             "+String(((@empty*10000)/@lines)/100.0)
   end
   @output.puts "Comments per 100 lines of code:        "+String(((@comments*100000)/@totalfunctionlines)/1000.0) if @totalfunctionlines>0
   @output.puts "Docstring lines per 100 lines of code: "+String(((@docstringlines*100000)/@totalfunctionlines)/1000.0) if @totalfunctionlines>0
   @output.puts "Docstring ratio:                       "+String(((@docstrings*1000)/(zmp1+@classes+1))/1000.0)
   zmp2=zmp1+@classes+1-@inits
   @output.puts "Docstring ratio (no inits):            "+String(((@docstrings*1000)/zmp2)/1000.0) if zmp2!=0
  end
 
  #parse function
  def doStat()
   @output.puts "--- FILE: ["+@inputname+"] ---"
   @output.puts "-- STRUCTURE --"
   IO.foreach(@inputname) do |line|
    if line=~/^\s*"""\s*$/ then
     docstring()
    elsif not @indocstring then
     begin
      # comments first, so they don't interfere with anything else
      if line=~/^\s*#/ then
       comment()
      # then static declarations
      elsif line=~/^\s*@staticmethod/ then
       static()
      # class definitions
      elsif line=~/class\s+([a-zA-Z0-9_]+)\s*(\([a-zA-Z0-9., _]+\)\s*)?:/ then
       newClass($1)
      # method declarations
      elsif line=~/def\s+([a-zA-Z0-9_]+)\s*\((self)?([,a-zA-Z0-9 =*._]*)\)\s*:/ then
       newMethod($1,$2!=nil)
      # imports
      elsif line=~/^\s*import\s+/ or line=~/from\s+\w+\s+import\s+/ then
       import()
      # empty lines
      elsif line=~/^\s*$/ then
       empty()
      # all the rest is the code
      else
       functionline()
      end   #if line  
     end    #begin indocstring
    else
     docstringline() 
    end     #if indocstring
    line() 
   end      #foreach
   newBlock()
   self.summary()
   self.stats()
   @output.puts "--- END:  ["+@inputname+"] ---"
  end
end

#processes the file
def dofile(filename,output)
 stat=StatMaker.new(filename,output)
 stat.doStat() 
end

#scans the directory and processes the files .py
#@param dirname name of the directory
#@param output output file
def dodir(dirname,output)
 Dir.foreach(dirname) do |content|
  if(content!="." and content!=".." and not content=~/^\./) then
   begin
    if(File.directory?(dirname+'/'+content)) then
     dodir(dirname+'/'+content,output)
    else
     dofile(dirname+'/'+content,output) if content=~/.py$/
    end
   end 
  end 
 end
end

#starts here
if ARGV.size==2 and ARGV[0]=="-d" then
 dodir(ARGV[1],STDOUT)
elsif ARGV.size>0 then
 output=STDOUT
 ARGV.each do |file|
  stat=StatMaker.new(file,output)
  stat.doStat()
 end
else
 puts "Usage: "
 puts "  pycode -d DIR         - scan recursively directory"
 puts "  pycode FILE1 FILE2... - process given files"
 puts "The program writes to standard output."
end
