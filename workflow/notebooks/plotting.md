```python
# imports
import numpy as np
import umap
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import seaborn as sns
import os, sys
import csrgraph as cg
import nodevectors
sys.path.append("../scripts")
from graph_analysis import load_nodes, load_edges

%matplotlib inline

```

```python
# read graph
lcc_path = "../../data/processed/finals/lcc.tar.gz" if not os.path.exists("../../data/processed/finals/lcc_edges.tsv") else "../../data/processed/finals/lcc_edges.tsv"
if os.path.exists("../../data/processed/finals/lcc_edges.tsv"):
    G = cg.read_edgelist("../../data/processed/finals/lcc_edges.tsv", directed=False, 
                         sep='\t', low_memory=False, usecols=["subject", "object"], header=0)
else:
    edges_df = load_edges(lcc_path, usecols=["subject", "object"])
    G = cg.csrgraph(edges_df, directed=False)
```

```python
# Create model
ggvec_model = nodevectors.GGVec(n_components=256, order=2) 
```

```python
# Produce embeddings
embeddings = ggvec_model.fit_transform(G)
```

```python
# Get node names and types
nodes = list(G.nodes())
node_types = load_nodes(lcc_path, usecols=["id", "category"])
node_types = node_types.set_index("id").astype("category")
```

```python
# Create UMAP embeddings for visulalization
reducer = umap.UMAP(random_state=42)
reducer.fit(embeddings)
```

```python
umap.plot.points(reducer, labels=node_types.category.cat.categories, width=500, height=500)
```

```python
embedding = reducer.embedding_
```

```python
# Plot embeddings
plt.figure(figsize=(4, 4), dpi=300)
plt.scatter(embedding[:, 0], embedding[:, 1], c=node_types.category.cat.codes, cmap='Spectral', s=0.01)
plt.gca().set_aspect('equal', 'datalim')
plt.colorbar(boundaries=np.arange(13)-0.5).set_ticks(np.arange(12))
plt.title('UMAP projection of the full dataset', fontsize=24);
```

```python
for n, cat in reversed(list(enumerate(node_types.category.cat.categories))):
    print(n, cat)
```

```python
node_types.shape
```

```python
len(nodes)
```

```python

```
