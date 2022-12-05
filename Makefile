all:
	cd workflow && snakemake -c 8
clean:
	rm data/processed/*/*
cleanall: clean
	rm data/raw/*
