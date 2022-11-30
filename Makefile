all:
	cd workflow && snakemake -c 4
clean:
	rm data/processed/*/*
cleanall: clean
	rm data/raw/*
