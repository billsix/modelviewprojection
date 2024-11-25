all: cayleyImages graphs pythonplots
	cd gnuplot && make



graphs: currency.svg \
	demo11.svg \
	demo10.svg \
	demo10-2.svg \
	demo06.svg \
	demo08.svg \
	demo02.svg \
	demo03.svg \
	demo05.svg \
	perspective.svg \
	demo18-1.svg \
	demo18-2.svg \
	demo18-3.svg \
	demo18-4.svg \
	demo18-5.svg \
	demo18-6.svg \
	demo18-7.svg \
	demo18-8.svg \
	cayleygraph.svg \
	assignment2.svg \
	demo16.svg


cayleyImages: ndcToScreenspace.png \
		nickleToPenny.png \
		dimeToPenny.png \
		quarterToPenny.png \
		dollarToPenny.png \
		dToC.png \
		cToA.png \
		bToA.png \
		p1ToNDC.png \
		p2ToNDC.png \
		p1ToW.png \
		p2ToW.png \
		wToNDC.png \
		wToP1.png \
		wToP2.png \
		p1ToP1.png \
		p2ToP2.png \
		cToW.png \
		wToC.png \
		cToNDC.png \
		s1ToP1.png \
		cToClip.png \
		clipToNDC.png

ndcToScreenspace.png: ndcToScreenspace.tex
	python3 texExpToPng.py --file ndcToScreenspace.tex --size 300 --output ndcToScreenspace.png
nickleToPenny.png: nickleToPenny.tex
	python3 texExpToPng.py --file nickleToPenny.tex --size 300 --output nickleToPenny.png
dimeToPenny.png: dimeToPenny.tex
	python3 texExpToPng.py --file dimeToPenny.tex --size 300 --output dimeToPenny.png
quarterToPenny.png: quarterToPenny.tex
	python3 texExpToPng.py --file quarterToPenny.tex --size 300 --output quarterToPenny.png
dollarToPenny.png: dollarToPenny.tex
	python3 texExpToPng.py --file dollarToPenny.tex --size 300 --output dollarToPenny.png
dToC.png: dToC.tex
	python3 texExpToPng.py --file dToC.tex --size 300 --output dToC.png
cToA.png: cToA.tex
	python3 texExpToPng.py --file cToA.tex --size 300 --output cToA.png
bToA.png: bToA.tex
	python3 texExpToPng.py --file bToA.tex --size 300 --output bToA.png
p1ToNDC.png: p1ToNDC.tex
	python3 texExpToPng.py --file p1ToNDC.tex --size 300 --output p1ToNDC.png
p2ToNDC.png: p2ToNDC.tex
	python3 texExpToPng.py --file p2ToNDC.tex --size 300 --output p2ToNDC.png
p1ToW.png: p1ToW.tex
	python3 texExpToPng.py --file p1ToW.tex --size 300 --output p1ToW.png
p2ToW.png: p2ToW.tex
	python3 texExpToPng.py --file p2ToW.tex --size 300 --output p2ToW.png
wToNDC.png: wToNDC.tex
	python3 texExpToPng.py --file wToNDC.tex --size 300 --output wToNDC.png
wToP1.png: wToP1.tex
	python3 texExpToPng.py --file wToP1.tex --size 300 --output wToP1.png
wToP2.png: wToP2.tex
	python3 texExpToPng.py --file wToP2.tex --size 300 --output wToP2.png
p1ToP1.png: p1ToP1.tex
	python3 texExpToPng.py --file p1ToP1.tex --size 300 --output p1ToP1.png
p2ToP2.png: p2ToP2.tex
	python3 texExpToPng.py --file p2ToP2.tex --size 300 --output p2ToP2.png
cToW.png: cToW.tex
	python3 texExpToPng.py --file cToW.tex --size 300 --output cToW.png
wToC.png: wToC.tex
	python3 texExpToPng.py --file wToC.tex --size 300 --output wToC.png
cToNDC.png: cToNDC.tex
	python3 texExpToPng.py --file cToNDC.tex --size 300 --output cToNDC.png
s1ToP1.png: s1ToP1.tex
	python3 texExpToPng.py --file s1ToP1.tex --size 300 --output s1ToP1.png
cToClip.png: cToClip.tex
	python3 texExpToPng.py --file cToClip.tex --size 300 --output cToClip.png
clipToNDC.png: clipToNDC.tex
	python3 texExpToPng.py --file clipToNDC.tex --size 300 --output clipToNDC.png




currency.svg: currency.dot
	dot -Tsvg -Gsize=6,9\! -Gdpi=200 $< -o $@

demo16.svg: demo16.dot
	dot -Tsvg $< -o $@

demo11.svg: demo11.dot
	dot -Tsvg $< -o $@

demo10.svg: demo10.dot
	dot -Tsvg $< -o $@

demo10-2.svg: demo10-2.dot
	dot -Tsvg $< -o $@

assignment2.svg: assignment2.dot
	dot -Tsvg $< -o $@


demo06.svg: demo06.dot
	dot -Tsvg $< -o $@

demo08.svg: demo08.dot
	dot -Tsvg $< -o $@

demo02.svg: demo02.dot
	dot -Tsvg $< -o $@

demo03.svg: demo03.dot
	dot -Tsvg $< -o $@

demo05.svg: demo05.dot
	dot -Tsvg $< -o $@

cayleygraph.svg: cayleygraph.dot
	dot -Tsvg $< -o $@

perspective.svg: perspective.dot
	dot -Tsvg $< -o $@


demo18-1.svg: demo18-1.dot
	dot -Tsvg $< -o $@

demo18-2.svg: demo18-2.dot
	dot -Tsvg $< -o $@

demo18-3.svg: demo18-3.dot
	dot -Tsvg $< -o $@

demo18-4.svg: demo18-4.dot
	dot -Tsvg $< -o $@

demo18-5.svg: demo18-5.dot
	dot -Tsvg $< -o $@

demo18-6.svg: demo18-6.dot
	dot -Tsvg $< -o $@

demo18-7.svg: demo18-7.dot
	dot -Tsvg $< -o $@

demo18-8.svg: demo18-8.dot
	dot -Tsvg $< -o $@


pythonplots: rotate0.gif



rotate0.gif: generate_plots.py
	python3 generate_plots.py
