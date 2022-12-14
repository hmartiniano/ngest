# ngest


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

## Setup neo4j

1. Install docker with docker-compose plugin:

[https://docs.docker.com/compose/install/]()

2. Copy example env file to neo4j/env:

```
cd neo4j
cp env.example env
```

3. Replace username and password in env file.

4. Start neo4j:

```
docker compose up -d
```

5. Run conversion script:

```
python ../scripts/tsv_to_neo4j ../data/finals/merged_nodes.tsv ../data/finals/merged_edges.tsv
cp nodes.csv.gz edges.csv.gz import
```

6. Enter container 

```
docker compose exec neo4j bash 
```

7. Import data 
Inside the container run:

```
./bin/neo4j-admin database import full --nodes /import nodes.csv.gz --edges /import/edges.csv.gz --overwrite-destination
```


