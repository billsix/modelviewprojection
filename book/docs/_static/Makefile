all: cayleyImages graphs rotate0-0.svg
	cd gnuplot && make


/usr/local/bin/texExpToPng: tex_exp_to_png/meson.build
	cd tex_exp_to_png &&  \
           meson setup builddir && \
           meson compile -C builddir && \
           meson install -C builddir


%.png: %.tex /usr/local/bin/texExpToPng
	texExpToPng --file $< --size 300 --output $@

%.png: %.dot
	dot -Tpng  $< -o $@



graphs: currency.png \
	temp.png \
	demo11.png \
	demo10.png \
	demo10-2.png \
	demo06.png \
	demo07.png \
	demo08.png \
	demo09.png \
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
	      ndcToScreenspaceName.png \
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
		p1ToWname.png \
		p1ToWDemo06.png \
		p1ToWDemo07.png \
		p1ToWDemo09.png \
		p2ToW.png \
		p2ToWname.png \
		p2ToWDemo06.png \
		p2ToWDemo07.png \
		p2ToWDemo09.png \
		wToNDC.png \
		wToNDCname.png \
		wToP1.png \
		wToP2.png \
		p1ToP1.png \
		p2ToP2.png \
		cToW.png \
		wToC.png \
		cToNDC.png \
		s1ToP1.png \
		cToClip.png \
		clipToNDC.png \
		ch02_math_01.png \
		ch02_math_02.png \
		ch02_math_03.png \
		ch02_math_04.png \
		ch02_math_05.png \
		ch02_math_06.png \
		ch02_math_07.png \
		ch02_math_08.png \
		ch02_math_09.png \
		ch02_math_10.png \
		ch02_math_11.png \
		ch02_math_12.png \
		ch02_math_13.png \
		ch02_math_14.png \
		ch02_math_15.png \
		ch02_math_16.png \
		ch02_math_17.png \
		ch02_math_18.png \
		ch02_math_19.png \
		ch02_math_20.png \
		ch02_math_21.png \
		ch02_math_22.png




# dummy task to generate all the plots from generate_plots
rotate0-0.svg: ../../../src/modelviewprojection/plotsforbook/generate_plots.py
	generate_plots_for_book
