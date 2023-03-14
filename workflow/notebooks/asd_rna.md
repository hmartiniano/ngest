---
jupyter:
  jupytext:
    formats: ipynb,md
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.14.5
  kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
---

```python
import functools
import requests
import pandas as pd
import numpy as npa
import networkx as nx
from matplotlib_venn import venn3

pd.options.display.max_colwidth = None
```

```python

def rnacentral_api(id_):
    r = requests.get(f"https://rnacentral.org/api/v1/rna/{id_}/?format=json")
    return r.json()


def extract_ids(xrefs):
    ids = []
    for xref in xrefs["results"]:
        if xref["taxid"] == 9606:
            ids.append(xref["accession"]["id"])
    ids = process_ids(ids)
    return ids

def process_ids(ids):
    result = {}
    for id_ in ids:
        a = id_.split(":")
        try:
            if a[0].startswith("NR"):
                result["Refseq"] = a[0]
            elif a[0].startswith("ENST"):
                result["ENST"] = a[0]
            elif a[0].startswith("NO"):
                result["NONCODE"] = a[0]
            else:
                result[a[0]] = a[1]
            print(a)
        except:
            print("Failed:", a)
    return result
```

```python
df = pd.read_csv("../../data/processed/finals/lcc_edges.tsv", sep="\t", usecols=["subject", "object", "predicate"])
```

```python
g = nx.from_pandas_edgelist(df, source="subject", target="object", edge_attr="predicate", create_using=nx.MultiGraph, edge_key="predicate")
```

```python
rna = [node for node in g.nodes if node.startswith("RNA")]
```

```python
aa = nx.adamic_adar_index(nx.Graph(g), (("HP:0000717", r) for r in rna))
```

```python
aa = sorted(aa, key=lambda x: x[-1], reverse=True)
```

```python
jc = nx.jaccard_coefficient(nx.Graph(g), (("HP:0000717", r) for r in rna))
```

```python
jc = sorted(jc, key=lambda x: x[-1], reverse=True)
```

```python
pa = nx.preferential_attachment(nx.Graph(g), (("HP:0000717", r) for r in rna))
```

```python
pa = sorted(pa, key=lambda x: x[-1], reverse=True)
```

```python
venn3([set([a[1] for a in aa[:100]]), set([j[1] for j in jc[:100]]), set([p[1] for p in pa[:100]])])
```

```python
def borda_sort(lists):
    scores = {}
    for l in lists:
        for idx, elem in enumerate(reversed(l)):
            if not elem in scores:
                scores[elem] = 0
            scores[elem] += idx
    return sorted(scores.keys(), key=lambda elem: scores[elem], reverse=True)
```

```python
ranked = borda_sort([[a[1] for a in aa[:100]], [j[1] for j in jc[:100]], [p[1] for p in pa[:100]]])
```

```python
ranked[:100]
```

```python
rnac = [rnacentral_api(r.split(":")[-1]) for r in ranked[:50]]
```

```python
rnac = pd.DataFrame(rnac)
```

```python
rnac["xrefs_"] = rnac["xrefs"].apply(lambda x: requests.get(x).json())
```

```python
rnac["ids"] = rnac["xrefs_"].apply(extract_ids)
```

```python
rnac
```

```python
(rnac[["rnacentral_id", "ids"]]
 .set_index("rnacentral_id")["ids"]
 .apply(pd.Series))
```

```python
[i for i in xrefs_["results"] if i["taxid"] == 9606]
```

```python
xrefs_
```

```python
xref = xrefs_["results"][1]
```

```python
xref
```

```python

```
