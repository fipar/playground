clean: 
	rm -f *aux *dvi *log *pdf

pdfs:
	for f in $(shell ls *tex); do texi2pdf $$f; done	
