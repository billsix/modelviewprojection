all: cayleyImages graphs rotate0-0.svg
	cd gnuplot && make



graphs: currency.png \
	temp.png \
	demo11.png \
	demo10.png \
	demo10-2.png \
	demo06.png \
	demo08.png \
	demo02.png \
	demo03.png \
	demo05.png \
	perspective.png \
	demo18-1.png \
	demo18-2.png \
	demo18-3.png \
	demo18-4.png \
	demo18-5.png \
	demo18-6.png \
	demo18-7.png \
	demo18-8.png \
	cayleygraph.png \
	assignment2.png \
	demo16.png


cayleyImages: ndcToScreenspace.png \
		nickleToPenny.png \
		dimeToPenny.png \
		quarterToPenny.png \
		dollarToPenny.png \
		celciusToKelvin.png \
		fahrenheitToCelsuis.png \
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
celciusToKelvin.png: celciusToKelvin.tex
	python3 texExpToPng.py --file celciusToKelvin.tex --size 300 --output celciusToKelvin.png
fahrenheitToCelsuis.png: fahrenheitToCelsuis.tex
	python3 texExpToPng.py --file fahrenheitToCelsuis.tex --size 300 --output fahrenheitToCelsuis.png


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




currency.png: currency.dot
	dot -Tpng  $< -o $@

temp.png: temp.dot
	dot -Tpng $< -o $@

demo16.png: demo16.dot
	dot -Tpng $< -o $@

demo11.png: demo11.dot
	dot -Tpng $< -o $@

demo10.png: demo10.dot
	dot -Tpng $< -o $@

demo10-2.png: demo10-2.dot
	dot -Tpng $< -o $@

assignment2.png: assignment2.dot
	dot -Tpng $< -o $@


demo06.png: demo06.dot
	dot -Tpng $< -o $@

demo08.png: demo08.dot
	dot -Tpng $< -o $@

demo02.png: demo02.dot
	dot -Tpng $< -o $@

demo03.png: demo03.dot
	dot -Tpng $< -o $@

demo05.png: demo05.dot
	dot -Tpng $< -o $@

cayleygraph.png: cayleygraph.dot
	dot -Tpng $< -o $@

perspective.png: perspective.dot
	dot -Tpng $< -o $@


demo18-1.png: demo18-1.dot
	dot -Tpng $< -o $@

demo18-2.png: demo18-2.dot
	dot -Tpng $< -o $@

demo18-3.png: demo18-3.dot
	dot -Tpng $< -o $@

demo18-4.png: demo18-4.dot
	dot -Tpng $< -o $@

demo18-5.png: demo18-5.dot
	dot -Tpng $< -o $@

demo18-6.png: demo18-6.dot
	dot -Tpng $< -o $@

demo18-7.png: demo18-7.dot
	dot -Tpng $< -o $@

demo18-8.png: demo18-8.dot
	dot -Tpng $< -o $@


# dummy task to generate all the plots from generate_plots.py
rotate0-0.svg: generate_plots.py
	python3 generate_plots.py
