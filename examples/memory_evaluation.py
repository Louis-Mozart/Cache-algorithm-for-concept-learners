"""Cache Memory Consumption per Concept Learner.

For each CEL (OCEL, CELOE, EvoLearner, CLIP), runs a set of learning problems
on the Family dataset under three cache modes:
  - Semantic Cache    (blue  solid)
  - No Cache          (orange solid)
  - Non-Semantic Cache(green hatched)

Produces a grouped bar plot saved as 'cache_memory_per_cel.png'.

Usage
-----
    python examples/memory_evaluation.py
    python examples/memory_evaluation.py --kb KGs/Family/family.owl \\
        --lps LPs/Family/lps.json --max_runtime 10 --n_problems 18
"""

import argparse
import json
import os
import random
import sys
import urllib.request

import pkg_resources
import jpype

# ---------------------------------------------------------------------------
# Java 11+ fix: inject jaxb-api before owlapy starts the JVM
# ---------------------------------------------------------------------------
def _ensure_jvm_with_jaxb():
    if jpype.isJVMStarted():
        return
    jar_folder = pkg_resources.resource_filename('owlapy', 'jar_dependencies')
    jar_files = [os.path.join(jar_folder, f) for f in os.listdir(jar_folder) if f.endswith('.jar')]
    jaxb_jar = os.path.join(jar_folder, 'jaxb-api-2.3.1.jar')
    if not os.path.exists(jaxb_jar):
        url = "https://repo1.maven.org/maven2/javax/xml/bind/jaxb-api/2.3.1/jaxb-api-2.3.1.jar"
        print("Downloading jaxb-api-2.3.1.jar for Java 11+ compatibility …")
        urllib.request.urlretrieve(url, jaxb_jar)
        print("Download complete.")
    if jaxb_jar not in jar_files:
        jar_files.append(jaxb_jar)
    jpype.startJVM(classpath=jar_files)

_ensure_jvm_with_jaxb()

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from owlapy.owl_individual import OWLNamedIndividual, IRI
from ontolearn.knowledge_base_ebr import KnowledgeBaseEBR
from ontolearn.learners import CELOE, OCEL
from ontolearn.concept_learner import EvoLearner, CLIP
from ontolearn.learning_problem import PosNegLPStandard
from ontolearn.metrics import F1
from ontolearn.refinement_operators import ModifiedCELOERefinement
from ontolearn.semantic_caching import non_semantic_caching_size

# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Cache memory consumption per CEL")
parser.add_argument("--kb",          type=str, default="KGs/Family/family.owl")
parser.add_argument("--lps",         type=str, default="LPs/Family/lps.json")
parser.add_argument("--reasoner",    type=str, default="abstract_reasoner",
                    choices=["abstract_reasoner", "EBR", "Pellet", "HermiT", "JFact", "Openllet"])
parser.add_argument("--max_runtime", type=int, default=10)
parser.add_argument("--n_problems",  type=int, default=10,
                    help="Number of learning problems to sample (default: 10).")
parser.add_argument("--output",      type=str, default="cache_memory_per_cel.csv")
args = parser.parse_args()

# ---------------------------------------------------------------------------
# Load learning problems
# ---------------------------------------------------------------------------
with open(args.lps) as f:
    raw = json.load(f)
all_problems = raw["problems"] if "problems" in raw else raw
random.seed(0)
n = min(args.n_problems, len(all_problems))
selected_problems = dict(random.sample(list(all_problems.items()), n))
print(f"Running {n} learning problems on '{os.path.basename(args.kb)}'")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_lp(examples):
    typed_pos = set(map(OWLNamedIndividual, map(IRI.create, examples["positive_examples"])))
    typed_neg = set(map(OWLNamedIndividual, map(IRI.create, examples["negative_examples"])))
    return PosNegLPStandard(pos=typed_pos, neg=typed_neg)

# Cache size used for the non-semantic wrapper (mirrors KnowledgeBaseEBR default)
NON_SEMANTIC_CACHE_SIZE = 1024 * 3

def get_cache_mb(kb: KnowledgeBaseEBR) -> float:
    """Return memory used by kb.cache in MB. Works for both semantic and non-semantic wrappers."""
    return kb.cache.get_cache_memory_bytes() / (1024 ** 2)

# ---------------------------------------------------------------------------
# CEL builder functions
# ---------------------------------------------------------------------------
def build_ocel(kb):
    return OCEL(knowledge_base=kb, quality_func=F1(), max_runtime=args.max_runtime)

def build_celoe(kb):
    return CELOE(knowledge_base=kb, quality_func=F1(), max_runtime=args.max_runtime)

def build_evo(kb):
    return EvoLearner(knowledge_base=kb, quality_func=F1(), max_runtime=args.max_runtime)

def build_clip(kb):
    return CLIP(
        knowledge_base=kb,
        refinement_operator=ModifiedCELOERefinement(kb),
        quality_func=F1(),
        max_num_of_concepts_tested=int(1e9),
        max_runtime=args.max_runtime,
        path_of_embeddings=None,
        pretrained_predictor_name=["LSTM", "GRU", "SetTransformer"],
        load_pretrained=True,
    )

CEL_BUILDERS = {
    "OCEL":        build_ocel,
    "CELOE":       build_celoe,
    "EvoLearner":  build_evo,
    "CLIP":        build_clip,
}

# ---------------------------------------------------------------------------
# Cache modes to evaluate
# ---------------------------------------------------------------------------
# "semantic"     → KnowledgeBaseEBR(use_cache=True)  — semantic_caching_size wrapper
# "non_semantic" → inject non_semantic_caching_size into kb.cache; same routing path
CACHE_MODES = ["semantic", "non_semantic"]

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
results = []   # list of dicts {CEL, mode, cache_memory_MB}

for cache_mode in CACHE_MODES:
    print(f"\n{'#'*60}")
    print(f"Cache mode : {cache_mode}")
    print(f"{'#'*60}")

    for cel_name, builder in CEL_BUILDERS.items():
        print(f"\n  CEL : {cel_name}")
        evo_mode = (cel_name == "EvoLearner")
        mem_samples = []

        # ---- build shared KB (for non-evo learners) ----
        if not evo_mode:
            try:
                kb = KnowledgeBaseEBR(path=args.kb, which_reasoner=args.reasoner,
                                      use_cache=True, path_kge=None)
                if cache_mode == "non_semantic":
                    # Replace the semantic cache with a non-semantic one.
                    # kb.use_cache=True stays so KnowledgeBaseEBR.individuals() routes through kb.cache.
                    kb.cache = non_semantic_caching_size(kb.individuals_, cache_size=NON_SEMANTIC_CACHE_SIZE)
                learner = builder(kb)
            except Exception as e:
                print(f"    [ERROR] Could not build {cel_name} ({cache_mode}): {e}")
                results.append({"CEL": cel_name, "mode": cache_mode, "cache_memory_MB": None})
                continue

        for lp_name, examples in selected_problems.items():
            lp = make_lp(examples)
            try:
                if evo_mode:
                    kb = KnowledgeBaseEBR(path=args.kb, which_reasoner=args.reasoner,
                                          use_cache=True, path_kge=None)
                    if cache_mode == "non_semantic":
                        kb.cache = non_semantic_caching_size(kb.individuals_, cache_size=NON_SEMANTIC_CACHE_SIZE)
                    learner = builder(kb)

                learner.fit(lp)

                mem = get_cache_mb(kb)

                mem_samples.append(mem)
                print(f"    [{lp_name}] memory = {mem:.4f} MB")
            except Exception as e:
                print(f"    [ERROR] {lp_name}: {e}")

        if not mem_samples:
            results.append({"CEL": cel_name, "mode": cache_mode, "cache_memory_MB": None})
            continue

        final_mem = mem_samples[-1] if not evo_mode else float(np.mean(mem_samples))
        print(f"  → {cache_mode} | {cel_name}: {final_mem:.4f} MB")
        results.append({"CEL": cel_name, "mode": cache_mode,
                        "cache_memory_MB": round(final_mem, 6)})

# ---------------------------------------------------------------------------
# Report & CSV
# ---------------------------------------------------------------------------
df = pd.DataFrame(results)
print("\n\n" + "=" * 60)
print("CACHE MEMORY SUMMARY")
print("=" * 60)
print(df.to_string(index=False))
df.to_csv(args.output, index=False)
print(f"\nResults saved to: {args.output}")

# ---------------------------------------------------------------------------
# Grouped bar plot — 2 bars per CEL: Semantic Cache vs Non-Semantic Cache
# ---------------------------------------------------------------------------
CEL_ORDER = ["OCEL", "CELOE", "EvoLearner", "CLIP"]

# Colours matching the reference screenshot (blue solid / green hatched)
MODE_STYLE = {
    "semantic":     dict(color="#4C72B0", hatch="",    label="Semantic Cache"),
    "non_semantic": dict(color="#2ecc71", hatch="///", label="Non-Semantic Cache"),
}

width = 0.35
x     = np.arange(len(CEL_ORDER))

fig, ax = plt.subplots(figsize=(9, 5))

for i, mode in enumerate(CACHE_MODES):   # ["semantic", "non_semantic"]
    heights = []
    for cel in CEL_ORDER:
        row = df[(df["CEL"] == cel) & (df["mode"] == mode)]
        val = float(row["cache_memory_MB"].iloc[0]) \
            if not row.empty and row["cache_memory_MB"].notna().any() else 0.0
        heights.append(val)

    style  = MODE_STYLE[mode]
    offset = (i - 0.5) * width   # centres the 2-bar group: -width/2, +width/2
    ax.bar(x + offset, heights, width=width,
           color=style["color"], hatch=style["hatch"],
           edgecolor="black", label=style["label"])

ax.set_xticks(x)
ax.set_xticklabels(CEL_ORDER, fontsize=12)
ax.set_xlabel("", fontsize=12)
ax.set_ylabel("Average Memory (MB)", fontsize=12)
ax.set_title(
    f"{os.path.splitext(os.path.basename(args.kb))[0].replace('-', ' ').title()}",
    fontsize=13, fontweight="bold",
)
ax.legend(fontsize=10)
ax.grid(axis="y", linestyle="--", alpha=0.4)
fig.tight_layout()

plot_path = "cache_memory_per_cel.png"
fig.savefig(plot_path, dpi=150, bbox_inches="tight")
print(f"Plot saved to: {plot_path}")
plt.show()


