######
## BioImage Makefile
######
### Changed: 28-Jun-2007 by Miki
## File restructured, comments added. Coverage section completely
## rewritten. HTML files are now stored as subdirectory in unittest.
## HTML generating rewritten to use more of Corea tool. 
######

##### variables

####  interpreters, programs, shell tools...
PYTHON = python
RUBY   = ruby
CAT    = cat

####  directories
###   unittests
TESTDIRNAME = unittest
TESTDIR     = ./$(TESTDIRNAME)
###   logs
RESULTDIRNAME = results
TESTRESULTDIR = $(TESTDIR)/$(RESULTDIRNAME)
###   html files
HTMLDIRNAME = htmls
HTMLDIR     = $(TESTDIR)/$(HTMLDIRNAME)
###   useful scripts
SCRIPTSDIRNAME = scripts
SCRIPTSDIR     =./$(SCRIPTSDIRNAME)
###   source code
SOURCEDIRNAME = 
SOURCEDIR     = ./$(SOURCEDIRNAME)

####  command lines
###   code coverage tool
COVERAGE        = $(SCRIPTSDIR)/coverage.py
PYCOVER         = $(PYTHON) $(COVERAGE)
PYCOVEREXEC     = $(PYCOVER) -x
PYCOVERSHOW     = $(PYCOVER) -r -m -o /usr/,\<string,$(SCRIPTSDIRNAME) 
###   corea (coverage to html)
COREA      = $(SCRIPTSDIR)/corea
COREAHTML  = $(COREA) -x -q -C
COREAHTMLS = $(COREA) -X -q -w 
###   stats generator
COMET      = $(SCRIPTSDIR)/comet
COMETSYNTAX= $(SCRIPTSDIR)/syntax.yaml
COMETRULES = $(SCRIPTSDIR)/config.yaml
COMETFORMAT= $(SCRIPTSDIR)/output.yaml
STATS      = $(COMET) -S $(COMETSYNTAX) -R $(COMETFORMAT) -P $(COMETRULES)
STATSEXEC  = $(STATS) -e py -d
###   stats report to html
STATSTXT      = $(STATSEXEC)
STATSHTMLS    = $(STATSEXEC) -f html
STATSHTML     = $(STATSEXEC) -f summary-html

####  file and directory tags
tag      = $(shell date +%Y%m%d-%H%M%S)
daytag   = $(shell date +%Y%m%d)

####  files
###   log files (plain text)
testresultfile = $(TESTRESULTDIR)/res_$(tag).log
coveragefile   = $(TESTRESULTDIR)/cov_$(tag).log
statsfile      = $(TESTRESULTDIR)/sta_$(tag).log
###   latest files
latestcoveragefile   = $(TESTRESULTDIR)/`ls -t $(TESTRESULTDIR) | grep -m 1 -e "cov_.*\.log"`
latesttestresultfile = $(TESTRESULTDIR)/`ls -t $(TESTRESULTDIR) | grep -m 1 -e "res_.*\.log"`
lateststatsfile      = $(TESTRESULTDIR)/`ls -t $(TESTRESULTDIR) | grep -m 1 -e "sta_.*\.log"` 
###   html files and directories
coveragehtml          = $(HTMLDIR)/coverage.$(daytag).html
coveragelatesthtml    = $(HTMLDIR)/coverage.html 
coveragehtmldir       = $(HTMLDIR)/$(daytag).coverage
coveragelatesthtmldir = $(HTMLDIR)/.coverage
statshtml             = $(HTMLDIR)/stats.$(daytag).html
statslatesthtml       = $(HTMLDIR)/stats.html
statshtmldir          = $(HTMLDIR)/$(daytag).stats
statslatesthtmldir    = $(HTMLDIR)/.stats
###  files with unittests
fortesting := $(wildcard $(TESTDIR)/test_*.py)

##### targets

####
####  information and help
####

### displays help
help:
	@echo "--< BioImage Makefile >--"
	@echo "Common targets:"
	@echo " info          - displays useful information"
	@echo " clean         - cleans html files, log files and coverage data"
	@echo " test          - runs tests located in test directory"
	@echo " coverage      - runs tests and calculates their code coverage"
	@echo " coverage-html - calculates coverage and generates html output"
	@echo " stats         - generates statistics of the source in single txt file"
	@echo " stats-html    - generates source statistics in html"
	@echo " all-html      - same as: coverage-html stats-html"
	@echo " all           - same as: clean all-html"

### displays useful information
info:
	@echo "Test directory:         $(TESTDIR)"
	@echo "Test result directory:  $(TESTRESULTDIR)"
	@echo "Test files:"
	@for t in $(fortesting); do echo "$$t"; done
	@echo "Scripts directory:      $(SCRIPTSDIR)"
	@echo "Python coverage tool:   $(PYCOVER)"
	@echo "Stats harvester:        $(COMET)"
	@echo "HTML directory:         $(HTMLDIR)"
	@echo "Coverage to html tool:  $(COREA)"

####
####  cleaning
####

###   cleans html directory with subdirectories
clean-htmls:
	@echo "Erasing htmls directory..."
	@rm -f -r $(HTMLDIR)/*
	@echo "Htmls directory erased."

###   cleans log directory (removes all logs)
clean-logs:
	@echo "Erasing test results directory..."
	@rm -f $(TESTRESULTDIR)/*
	@echo "Test results directory erased."

###   cleans coverage cache
clean-coverage:
	@echo "Erasing coverage data..."
	@$(PYCOVER) -e
	@echo "Coverage data erased."

###   cleans hidden directories
clean-dirs:
	@echo "Erasing contents of hidden html dirs..."
	@rm -f -r $(coveragelatesthtmldir)/*
	@rm -f -r $(statslatesthtmldir)/*
	@echo "Contents of directories erased."

###   cleans htmls, logs, dirs and coverage cache
clean: clean-htmls clean-logs clean-dirs clean-coverage

####
####  unittests
####

###   runs and logs the test files in unittest directory
test-run:
	@echo "Test result file:  $(testresultfile)"
	@echo "Test date-time tag: $(tag)" >> $(testresultfile)
	@for t in $(fortesting); do \
	echo "Running file:      $$t" ;\
	echo " " >> $(testresultfile) ;\
	echo "** Test results for file:  $$t" >> $(testresultfile) ;\
	$(PYTHON) $$t 2>> $(testresultfile) ;\
	echo "** End of test result for: $$t" >> $(testresultfile) ;\
	echo " " >> $(testresultfile) ;\
	done
	@echo "Test result file:  $(testresultfile)"
	@echo "Tests completed."

###   shows the most recent test log file
test-show:
	@echo "The most recent log file:"
	@$(CAT) $(latesttestresultfile)

###   runs the test and shows the log file
test: test-run test-show

####
####  code coverage for tests
####

###   runs the tests and calculates code coverage of their execution
coverage: clean-coverage
	@echo "Running coverage for tests..."
	@echo "Test result file:  $(testresultfile)"
	@echo "Coverage file:     $(coveragefile)"
	@echo "Test date-time tag: $(tag)" >> $(testresultfile)
	@for t in $(fortesting); do \
	echo "Running file:      $$t" ;\
	echo " " >> $(testresultfile) ;\
	echo "** Test results for file:  $$t" >> $(testresultfile) ;\
	$(PYCOVEREXEC) $$t 2>> $(testresultfile) >> /dev/null ;\
	echo "** End of test result for: $$t" >> $(testresultfile) ;\
	echo " " >> $(testresultfile) ;\
	done
	@echo "Generating coverage report..."
	@$(PYCOVERSHOW) >> $(coveragefile)
	@echo "Coverage report generated."

####
####  coverage html files
####

###   generates single html from coverage report (does not include source code)
coverage-html-one:
	@echo "Generating html from latest coverage report..."
	@$(COREAHTML) $(latestcoveragefile) $(coveragehtml)
	@echo "Setting generated html as the most recent file..."
	@cp $(coveragehtml) $(coveragelatesthtml)
	@echo "Coverage html file generated."

###   generates html structure from coverage report (includes source code)
coverage-html-many:
	@echo "Generating html structure from latest coverage report..."
	@$(COREAHTMLS) $(latestcoveragefile) $(coveragehtmldir)
	@echo "Setting generated structure as the most recent one..."
	@cp $(coveragehtmldir)/* $(coveragelatesthtmldir)
	@echo "Coverage html structure generated."

###   calculates coverage and generates both single html and html structure from the report
coverage-html: coverage coverage-html-one coverage-html-many

####
####  code statistics
####

###   generates code statistics
stats-run:
	@echo "Generating code statistics..."
	@echo "Stats file:        $(statsfile)"
	@echo "Scanning files in  $(SOURCEDIR)..."
	@$(STATSTXT) -o $(statsfile) $(SOURCEDIR)
	@echo "Code statistics generated."

###   shows the most recent statistics file (huuuge)
stats-show:
	@echo "The most recent stats file:"
	@$(CAT) $(lateststatsfile)

###   runs the statistics
stats: stats-run

####
####  stats html files
####

###   generates one html from the most recent statistics report
stats-html-one:
	@echo "Generating code statistics in html format..."
	@echo "Stats file:        $(statshtml)"
	@echo "Scanning files in  $(SOURCEDIR)..."
	@$(STATSHTML) -o $(statshtml) $(SOURCEDIR)
	@echo "Setting generated html as the most recent file..."
	@cp $(statshtml) $(statslatesthtml)
	@echo "Statistics html generated."

###   generates html structure from code statistics
stats-html-many:
	@echo "Generating code statistics as html structure..."
	@echo "Stats directory:   $(statshtmldir)"
	@echo "Scanning files in  $(SOURCEDIR)..."
	@$(STATSHTMLS) -o $(statshtmldir) $(SOURCEDIR)
	@echo "Setting generated structure as the most recent one..."
	@cp $(statshtmldir)/* $(statslatesthtmldir)
	@echo "Stats html structure generated."

###   calculates code statistics and generates html from the report
stats-html: stats-html-one stats-html-many

####
####  "all" targets
####

###   runs all html html generating targets  
all-html: coverage-html stats-html

###   makes all
all: clean all-html
