clean: 
	rm -f *aux *dvi *log *pdf

pdf: 
	texi2pdf $$f.tex

pdfs:
	for f in $(shell ls *tex); do texi2pdf $$f; done	
