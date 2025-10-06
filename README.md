

## Caching Algorithm for Ontology Reasoners

This repository contains our caching algorithm designed to optimize ontology instance retrieval by accelerating reasoners. The implementation supports various eviction strategies and can be configured to use different cache types and sizes. Below, I have for you with the instructions to run the algorithm and generate the results.


## Installation

```shell
# First, you need to download this repository and make sure you are in to it. Then follow the steps below

# To create a virtual python env with conda 
conda create -n venv python=3.10.14 --no-default-packages && conda activate venv && pip install -e . && cd Ontolearn
# To unzip the benchmark datasets knowledge graphs
unzip KGs.zip
# To unzip the learning problems
unzip LPs.zip
```
Other datasets and learning problems can be manually downloaded from [here](https://drive.google.com/file/d/1LWmrtVQFh2_9eWOUsGZTGVeTkxi3n5pk/view?usp=sharing) 

## Caching Strategy

The cache can be initialized with a set of concepts (e.g., named and existential concepts), functioning as a cold cache. Alternatively, it can remain uninitialized and fill up during execution, functioning as a hot cache.

We support five eviction strategies: LRU, MRU, RP, FIFO, and LIFO.
The available reasoners include: EBR, Pellet, HermiT, Openllet, Structural and JFact.
Caching the Reasoners

To run the EBR reasoner on the Family and Father datasets with cache size ratios of 0.1, 0.4, and 0.8, using a cold cache and LRU strategy:

#### Caching the reasoners

 To run the EBR reasoner on the Family and Father datasets, with ratios 0.1, 0.4 and 0.8, on a cold cache (i.e. we initialize the cache with few concepts), using the LRU eviction strategy, first make sure you are located in this directory, then run

```shell
python examples/retrieval_with_cache.py --cache_size_ratios [.1, .4, .8] \
                        --path_kg ["KGs/Family/family.owl", "KGs/Family/father.owl"] \
                        --name_reasoner EBR \
                        --eviction_strategy LRU \
                        --random_seed_for_RP 10 \
                        --cache_type cold \
                        --shuffle_concepts
```
The results would be saved as two csv files in this same directory for further analysis. If you want the results for only datasets, just put the path to the dataset inside the list, similarly for the ratio.
e.g. we can run the above code only for the Father dataset and with a cache size ratio of 0.8 as

```shell
python examples/retrieval_with_cache.py --cache_size_ratios [.8] \
                        --path_kg ["KGs/Family/father.owl"] \
                        --name_reasoner EBR \
                        --eviction_strategy LRU \
                        --random_seed_for_RP 10 \
                        --cache_type cold \
                        --shuffle_concepts
```

To see the results for other reasoners, you can replace EBR with any other reasoner in the following list ["Pellet", "HermiT", "JFact", "Openllet", "Structural", "abstract_reasoner"]

### Caching the concept learners

In the experiments, all the concept learners were run using their default reasoners `abstract_reasoner` to evaluate the results with cache, run

```shell
python examples/run_cache_comparison.py --lps LPs/Family/lps.json --kb KGs/Family/family-benchmark_rich_background.owl --data_name Family
```

To use a different reasoner, ["Pellet", "HermiT", "JFact", "Openllet", "Structural"], simply add the `--reasoner` flag

```shell
python examples/run_cache_comparison.py --lps LPs/Family/lps.json --kb KGs/Family/family-benchmark_rich_background.owl --data_name Family --reasoner Pellet
```

The default max runtime is 60s, but this can be changed using the `--max_runtime` flag e.g, to run for 3 minutes

```shell
python examples/run_cache_comparison.py --lps LPs/Family/lps.json --kb KGs/Family/family-benchmark_rich_background.owl --data_name Family --reasoner Pellet --max_runtime 180
```

### Running on Other Datasets

For some datasets (Carcinogenesis, Mutagenesis, Vicodi), the learning problems are in the `datasets/` folder example, for Carcinogenesis

```shell
python examples/run_cache_comparison.py --lps datasets/carcinogenesis/training_data/training_data_prep.json --kb  datasets/carcinogenesis/kb/ontology.owl --data_name carcinogenesis
```

Example for Mutagenesis:

```shell
python examples/run_cache_comparison.py --lps datasets/mutagenesis/training_data/training_data_prep.json --kb  datasets/mutagenesis/kb/ontology.owl --data_name mutagenesis
```

Example for Vicodi:

```shell
python examples/run_cache_comparison.py --lps datasets/vicodi/training_data/training_data_prep.json --kb  datasets/vicodi/kb/ontology.owl --data_name vicodi
```

## Output

The results of these experiments will be saved in a new directory named `Experiments_normal_cache`.
Each reasoner will have a corresponding subdirectory, and the results will be stored in CSV format for further analysis.

### Example Results for Concept learning

#### Results Without Cache

|   LP |   F1-OCEL-no_cache |   RT-OCEL-no_cache |   F1-CELOE-no_cache |   RT-CELOE-no_cache |   F1-Evo-no_cache |   RT-Evo-no_cache |   F1-clip-no_cache |   RT-clip-no_cache |
|------|---------------------|---------------------|----------------------|----------------------|-------------------|-------------------|---------------------|---------------------|
|    Carbon-21 ⊔ Sulfur-78           |                0.55 |              157.99 |                 0.77 |                60.99 |              0.77 |              3.32 |                0.77 |              60.61  |
|    Carbon-21 ⊔ Di23 ⊔ Sulfur-74     |                0.30 |              574.50 |                 0.66 |                60.71 |              0.66 |              2.48 |                0.66 |              60.68  |
|    Bromine-94 ⊔ Di51   |                0.19 |              570.39 |                 0.99 |                60.67 |              0.99 |              2.80 |                0.99 |              61.04  |
|     Bromine ⊔ Sulfur-74 ⊔ (∃ isMutagenic.{True})  |                0.30 |              588.91 |                 0.99 |                60.76 |              0.99 |              2.49 |                0.99 |              62.32  |
Di23 ⊔ Hydrogen ⊔ Nitrogen-499 |                0.10 |              592.52 |                 0.89 |                60.63 |              0.89 |              2.51 |                0.89 |              61.94  |
|     Arsenic-101 ⊔ Bond    |                0.80 |              598.25 |                 0.80 |                60.65 |              0.80 |              3.11 |                0.80 |              61.91  |
|    Di227 ⊔ (∃ salmonella_reduc.{False})      |                0.33 |              573.14 |                 0.33 |                60.61 |              0.33 |              2.53 |                0.33 |              61.56  |
|     Five_ring ⊔ (Atom ⊓ (Carbon-27 ⊔ (¬Zinc-87)))  |                0.64 |              564.56 |                 0.64 |                60.73 |              0.64 |              2.64 |                0.64 |              60.61  |
|    Non_ar_6c_ring ⊔ Oxygen-40  |                0.70 |              559.23 |                 0.70 |                60.60 |              0.70 |              2.58 |                0.70 |              60.91  |
|   Hydrogen-2 ⊔ Phosphorus-61 ⊔ (∃ drosophila_rt.{False})  |                0.52 |              573.98 |                 0.52 |                60.61 |              0.52 |              2.52 |                0.52 |              61.21  |
|   Nitrogen-36 ⊔ (∃ salmonella_reduc.{False}) |                0.58 |              574.29 |                 0.60 |                60.71 |              0.60 |              2.44 |                0.60 |              60.65  |
|   Bond-7 ⊔ Di66 |                0.40 |              577.92 |                 0.99 |                60.65 |              0.99 |              3.38 |                0.99 |              60.92  |
|  Di227 ⊔ Di51 ⊔ (∃ hasAtom.Arsenic)  |                0.46 |              582.01 |                 0.99 |                60.62 |              0.99 |              3.43 |                0.99 |              60.97  |
|    Five_ring ⊔ Nitrogen-499 ⊔ Sulfur-74 |                0.70 |              573.13 |                 0.70 |                60.66 |              0.70 |              2.91 |                0.70 |              61.13  |
|   Krypton-83 ⊔ Phosphorus ⊔ (∃ drosophila_rt.{False})      |                0.60 |              580.95 |                 0.60 |                60.66 |              0.60 |              2.63 |                0.60 |              61.21  |
|   Oxygen-50 ⊔ Oxygen-53 |                0.70 |              574.33 |                 0.70 |                60.91 |              0.70 |              2.57 |                0.70 |              61.53  |
|   Di66 ⊔ Lead ⊔ Methoxy  |                0.55 |              584.15 |                 0.55 |                60.62 |              0.55 |              2.56 |                0.55 |              60.72  |
|   Five_ring ⊔ Hydrogen-1 ⊔ Oxygen-41   |                0.55 |              567.74 |                 0.55 |                60.66 |              0.55 |              2.47 |                0.55 |              61.15  |
|  (Nitrogen-31 ⊔ Oxygen-51) ⊓ (¬Carbon-27)  |                0.62 |              559.01 |                 0.62 |                60.60 |              0.62 |              2.48 |                0.62 |              60.59  |
|   Arsenic ⊔ Phosphorus ⊔ (∃ drosophila_rt.{False})  |                0.70 |              559.59 |                 0.70 |    60.75 |              0.70 |              2.60 |                0.70 |              60.89  |


#### Results with Cache

|   LP |   F1-OCEL-cache |   RT-OCEL-cache |   F1-CELOE-cache |   RT-CELOE-cache |   F1-Evo-cache |   RT-Evo-cache |   F1-clip-cache |   RT-clip-cache |
|------|------------------|------------------|-------------------|-------------------|----------------|----------------|------------------|------------------|
|    Carbon-21 ⊔ Sulfur-78   |             0.55 |            87.99 |              0.77 |             64.51 |           0.77 |           2.40 |             0.77 |            61.30 |
|    Carbon-21 ⊔ Di23 ⊔ Sulfur-74    |             0.30 |            98.28 |              0.66 |             61.57 |           0.66 |           2.55 |             0.66 |            69.19 |
|    Bromine-94 ⊔ Di51 |             0.19 |            94.12 |              0.99 |             60.65 |           0.99 |           3.79 |             0.99 |            60.39 |
|    Bromine ⊔ Sulfur-74 ⊔ (∃ isMutagenic.{True}) |             0.30 |            99.42 |              0.99 |             63.03 |           0.99 |           2.50 |             0.99 |            66.45 |
|    Arsenic-101 ⊔ Bond  |             0.10 |            94.63 |              0.89 |             64.63 |           0.89 |           2.54 |             0.89 |            61.55 |
|    Di227 ⊔ (∃ salmonella_reduc.{False})   |             0.80 |            93.78 |              0.80 |             61.01 |           0.80 |           3.07 |             0.80 |            63.11 |
|    Five_ring ⊔ (Atom ⊓ (Carbon-27 ⊔ (¬Zinc-87))) |             0.33 |            96.86 |              0.33 |             63.78 |           0.33 |           2.52 |             0.33 |            62.18 |
|    Non_ar_6c_ring ⊔ Oxygen-40 |             0.64 |           116.79 |              0.64 |             67.53 |           0.64 |           2.64 |             0.64 |            64.01 |
|    Hydrogen-2 ⊔ Phosphorus-61 ⊔ (∃ drosophila_rt.{False}) |             0.70 |            99.93 |              0.70 |             62.12 |           0.70 |           2.59 |             0.70 |            63.45 |
|   Nitrogen-36 ⊔ (∃ salmonella_reduc.{False})  |             0.52 |            99.41 |              0.52 |             62.44 |           0.52 |           2.54 |             0.52 |            60.47 |
|   Bond-7 ⊔ Di66 |             0.58 |           113.11 |              0.60 |             61.51 |           0.60 |           2.45 |             0.60 |            61.46 |
|   Di227 ⊔ Di51 ⊔ (∃ hasAtom.Arsenic)  |             0.40 |            99.27 |              0.99 |             62.01 |           0.99 |           3.36 |             0.99 |            60.67 |
|  Five_ring ⊔ Nitrogen-499 ⊔ Sulfur-74  |             0.46 |            99.38 |              0.99 |             62.09 |           0.99 |           3.36 |             0.99 |            61.18 |
|  Krypton-83 ⊔ Phosphorus ⊔ (∃ drosophila_rt.{False})        |             0.70 |           102.58 |              0.70 |             63.10 |           0.70 |           2.88 |             0.70 |            60.90 |
|   Oxygen-50 ⊔ Oxygen-53            |             0.60 |           106.35 |              0.60 |             62.48 |           0.60 |           2.62 |             0.60 |            62.35 |
|   Di66 ⊔ Lead ⊔ Methoxy        |             0.70 |            98.92 |              0.70 |             64.25 |           0.70 |           2.55 |             0.70 |            63.83 |
|   Five_ring ⊔ Hydrogen-1 ⊔ Oxygen-41 |             0.55 |           100.09 |              0.55 |             63.62 |           0.55 |           2.57 |             0.55 |            61.79 |
|  (Nitrogen-31 ⊔ Oxygen-51) ⊓ (¬Carbon-27) |             0.55 |           100.65 |              0.55 |             62.01 |           0.55 |           2.42 |             0.55 |            61.62 |
|   Arsenic ⊔ Phosphorus ⊔ (∃ drosophila_rt.{False})  |             0.62 |            94.87 |              0.62 |             60.89 |           0.62 |           2.52 |             0.62 |            60.99 |
