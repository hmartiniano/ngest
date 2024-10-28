
.PHONY: all clean cleanall release

all:
	cd workflow && snakemake -c 8

clean:
	rm data/processed/*/*

cleanall: clean
	rm data/raw/*

create-release-draft: 
	git tag ${TAG}
	git push origin ${TAG}
	gh release create ${TAG} --draft
	rm -rf release/ && mkdir -p release
	gzip -c data/processed/finals/merged_edges.tsv > release/merged_edges.tsv.gz
	gzip -c data/processed/finals/merged_nodes.tsv > release/merged_nodes.tsv.gz
	cp data/processed/db_versions.yaml data/processed/finals/merged_graph_stats.yaml release/
	#kgx graph-summary data/processed/finals/lcc_edges.tsv data/processed/finals/lcc_edges.tsv -i tsv -o release/lcc_graph_summary.yaml
	cd release && git clone https://github.com/hmartiniano/ngest ngest-${TAG} && tar -czvf ngest-${TAG}.tar.gz ngest-${TAG}/ && zip ngest-${TAG}.zip ngest-${TAG}/ && rm -rf ngest-${TAG}/
	gh release upload ${TAG} release/*


