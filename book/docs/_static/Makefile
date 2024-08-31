all: cayleyImages graphs pythonplots
	cd gnuplot && make



graphs: currency.png \
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
	assignment2.png


cayleyImages:
	./texExpToPng.sh "\vec{f}_{ndc}^{ss}" 450 ndcToScreenspace.png
	./texExpToPng.sh "{f}_{nickel}^{penny}" 450 nickleToPenny.png
	./texExpToPng.sh "{f}_{dime}^{penny}" 450 dimeToPenny.png
	./texExpToPng.sh "{f}_{quarter}^{penny}" 450 quarterToPenny.png
	./texExpToPng.sh "{f}_{dollar}^{penny}" 450 dollarToPenny.png
	./texExpToPng.sh "{f}_{d}^{c}" 300 dToC.png
	./texExpToPng.sh "{f}_{c}^{a}" 300 cToA.png
	./texExpToPng.sh "{f}_{b}^{a}" 300 bToA.png
	./texExpToPng.sh "{f}_{p_1}^{ndc}" 300 p1ToNDC.png
	./texExpToPng.sh "{f}_{p_2}^{ndc}" 300 p2ToNDC.png
	./texExpToPng.sh "{f}_{p_1}^{w}" 300 p1ToW.png
	./texExpToPng.sh "{f}_{p_2}^{w}" 300 p2ToW.png
	./texExpToPng.sh "{f}_{w}^{ndc}" 300 wToNDC.png
	./texExpToPng.sh "{f}_{w}^{p_1}" 300 wToP1.png
	./texExpToPng.sh "{f}_{w}^{p_2}" 300 wToP2.png
	./texExpToPng.sh "{f}_{p_1}^{p_1}" 300 p1ToP1.png
	./texExpToPng.sh "{f}_{p_2}^{p_2}" 300 p2ToP2.png
	./texExpToPng.sh "{f}_{c}^{w}" 300 cToW.png
	./texExpToPng.sh "{f}_{w}^{c}" 300 wToC.png
	./texExpToPng.sh "{f}_{c}^{ndc}" 300 cToNDC.png


currency.png: currency.dot
	dot -Tpng -Gsize=6,9\! -Gdpi=200 $< -o $@

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


pythonplots: rotate0.gif



rotate0.gif: generate_plots.py
	python3 generate_plots.py
