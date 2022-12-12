# ngest


## Installation

1. Install conda ([https://docs.conda.io/en/latest/miniconda.html]())

2. clone the repo and create conda env
```
git clone github.com/hmartiniano/ngest.git
cd ngest conda env create -n ngest -f env.yml
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

Install docker with docker-compose plugin:

[https://docs.docker.com/compose/install/]()

```

```


