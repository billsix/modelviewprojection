modelviewprojection.adoc:  modelviewprojection.py
	sed -e 's/^\#\#//g' modelviewprojection.py > modelviewprojection.adoc

modelviewprojection.html: modelviewprojection.adoc
	asciidoc -b html5 -a icons -a toc2 -a theme=flask -n modelviewprojection.adoc
