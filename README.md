# ngest
Ngest is an Automated pipeline for the creation of Biomedical Knowledge Graphs from heterogeneous data sources.

## Installation

1. Install conda ([https://docs.conda.io/en/latest/miniconda.html]())

2. clone the repo and create conda env
```
git clone github.com/hmartiniano/ngest.git
cd ngest 
conda env create -n ngest -f env.yml
conda activate ngest
```

## Usage 
To build a KG with all the databases you need 64 GB of RAM and around 10 GB disk space.

I the root dir of the repo run:

```
make
```

This will run the snakemake workflow.

## Data Model & Semantic Standards

For details on the graph schema, Biolink Model (v4.x) alignment, ontology axiom normalization (`owl:inverseOf`, `rdfs:subPropertyOf`), and interaction predicate definitions, see [docs/DATA_MODEL.md](docs/DATA_MODEL.md).

## Setup neo4j

1. Install docker with docker-compose plugin:

[https://docs.docker.com/compose/install/]()

2. Copy example env file to `neo4j/env` and configure credentials:

```bash
cd neo4j
cp env.example env
```

Replace username and password in `env` file as needed.

3. Convert graph to Neo4j admin import format:

From the repository root directory, run:

```bash
python workflow/scripts/tsv_to_neo4j.py -i data/processed/finals/lcc.tar.gz -o neo4j/import
```

4. Import data into Neo4j:

Inside the `neo4j/` directory, run the import tool via a one-off container:

```bash
cd neo4j
docker compose run --rm neo4j bin/neo4j-admin database import full \
  --nodes=/import/nodes.csv.gz \
  --relationships=/import/edges.csv.gz \
  --overwrite-destination neo4j
```

5. Start Neo4j:

```bash
docker compose up -d
```

The Neo4j browser will be accessible at [http://localhost:7474](http://localhost:7474).


