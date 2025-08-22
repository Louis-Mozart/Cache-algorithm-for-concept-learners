import json
import time
import pandas as pd
from ontolearn.knowledge_base import KnowledgeBase
from ontolearn.knowledge_base_ebr import KnowledgeBaseEBR
from ontolearn.learners import CELOE, OCEL
from ontolearn.concept_learner import EvoLearner
from ontolearn.learners import Drill, TDL
from ontolearn.concept_learner import NCES, NCES2, ROCES, CLIP
from ontolearn.learning_problem import PosNegLPStandard
from ontolearn.metrics import F1
from owlapy.owl_individual import OWLNamedIndividual, IRI
import argparse
from ontolearn.utils.static_funcs import compute_f1_score
import random
from examples.retrieval_eval_under_incomplete import generate_subgraphs
import numpy as np
import os
from ontolearn.refinement_operators import ExpressRefinement, ModifiedCELOERefinement
from tqdm import tqdm

pd.set_option("display.precision", 5)

def dl_concept_learning(args):
    random.seed(0)
    with open(args.lps) as json_file:
        settings = json.load(json_file)

    kb_origin = KnowledgeBase(path=args.kb)

    if "problems" in settings:
        problems = settings['problems']
    else:
        problems = settings
    problems = dict(random.sample(problems.items(), 18))

    if args.lps_difficult:
        with open(args.lps_difficult) as json_file:
            settings_difficult = json.load(json_file)

        if "problems" in settings_difficult:
            problems_difficult = settings_difficult['problems']
        else:
            problems_difficult = settings_difficult
        problems_difficult = dict(random.sample(problems_difficult.items(), 15))
    else:
        problems_difficult = {}

    selected_problems = {**problems, **problems_difficult}

    if args.operation in ["incomplete", "inconsistent"]:
        paths = generate_subgraphs(kb_path=args.kb, directory=f"{args.operation}_{args.data_name}", n=1, ratio=args.ratio, operation=args.operation)
    else:
        paths = [args.kb]

    data = {"LP": []}

    # Two modes: cache and no_cache
    for use_cache in [True, False]:
        learners_per_algo = dict()
        for algo_name, learner_cls in {
            "OCEL": OCEL,
            "CELOE": CELOE,
            "Evo": EvoLearner,
            "clip": CLIP,
        }.items():
            learners_per_algo[algo_name] = dict()
            for path in paths:
                kb_local = KnowledgeBaseEBR(path=path, which_reasoner=args.reasoner, use_cache=use_cache, path_kge=None)
                if algo_name == "Evo":
                    continue
                if algo_name == "clip":
                    learner = learner_cls(
                        knowledge_base=kb_local,
                        refinement_operator=ModifiedCELOERefinement(kb_local),
                        quality_func=F1(),
                        max_num_of_concepts_tested=int(1e9),
                        max_runtime=args.max_runtime,
                        path_of_embeddings=None,
                        pretrained_predictor_name=["LSTM", "GRU", "SetTransformer"],
                        load_pretrained=True
                    )
                else:
                    learner = learner_cls(
                        knowledge_base=kb_local,
                        quality_func=F1(),
                        max_runtime=args.max_runtime
                    )
                learners_per_algo[algo_name][path] = learner

        mode = "cache" if use_cache else "no_cache"

        for str_target_concept, examples in tqdm(selected_problems.items(), desc=f"Processing problems ({mode})"):
            print('\n\nTarget concept:', str_target_concept)
            if use_cache:
                data.setdefault("LP", []).append(str_target_concept)

            p = set(examples['positive_examples'])
            n = set(examples['negative_examples'])
            typed_pos = set(map(OWLNamedIndividual, map(IRI.create, p)))
            typed_neg = set(map(OWLNamedIndividual, map(IRI.create, n)))
            lp = PosNegLPStandard(pos=typed_pos, neg=typed_neg)

            for algo_name, learner_cls in {
                "OCEL": OCEL,
                "CELOE": CELOE,
                "Evo": EvoLearner,
                "clip": CLIP,
            }.items():
                f1s, runtimes = [], []

                for path in paths:
                    # try:
                    if algo_name == "Evo":
                        kb_local = KnowledgeBaseEBR(path=path, which_reasoner=args.reasoner, use_cache=use_cache, path_kge=None)
                        learner = learner_cls(
                            knowledge_base=kb_local,
                            quality_func=F1(),
                            max_runtime=args.max_runtime
                        )
                    else:
                        learner = learners_per_algo[algo_name][path]

                    start_time = time.time()
                    pred = learner.fit(lp).best_hypotheses(n=1)
                    runtime = time.time() - start_time

                    f1 = compute_f1_score(
                        individuals=frozenset({i for i in kb_origin.individuals(pred)}),
                        pos=lp.pos, neg=lp.neg
                    )
                    f1s.append(f1)
                    runtimes.append(runtime)

                # except AssertionError as e:
                #     print(f"⚠️ Skipping learning problem due to invalid pos/neg examples: {e}")
                # except Exception as e:
                #     print(f"❌ Unexpected error during learner run: {e}")

                f1_key = f"F1-{algo_name}-{mode}"
                rt_key = f"RT-{algo_name}-{mode}"

                if f1s:
                    data.setdefault(f1_key, []).append(np.mean(f1s))
                    data.setdefault(rt_key, []).append(np.mean(runtimes))
                    print(f"{algo_name} ({mode}): F1={np.mean(f1s):.3f}, RT={np.mean(runtimes):.3f}")
                else:
                    data.setdefault(f1_key, []).append(None)
                    data.setdefault(rt_key, []).append(None)
                    print(f"{algo_name} ({mode}): Skipped.")

    # Save results
    df = pd.DataFrame.from_dict(data)
    output_dir = f"Experiments_{args.operation}_cache_comparison"
    os.makedirs(output_dir, exist_ok=True)

    if args.operation == "normal":
        df.to_csv(f"{output_dir}/{args.data_name}_{args.reasoner}.csv", index=False)
    else:
        ratio_str = str(args.ratio).replace(".", "_")
        df.to_csv(f"{output_dir}/{args.data_name}_{args.reasoner}_{ratio_str}.csv", index=False)

    print(df)
    print(df.select_dtypes(include="number").mean())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Description Logic Concept Learning')
    parser.add_argument("--max_runtime", type=int, default=60)
    parser.add_argument("--lps", type=str, default="LPs/Family/lps.json")
    parser.add_argument("--lps_difficult", type=str, default=None)#, required=True)datasets/family/training_data/training_data_prep.json
    parser.add_argument("--kb", type=str, default="KGs/Family/family-benchmark_rich_background.owl")
    parser.add_argument("--path_pretrained_kge", type=str, default=None)
    parser.add_argument("--data_name", type=str, default="family")
    parser.add_argument("--reasoner", type=str, default="EBR", choices=["EBR", "Pellet", "HermiT", "JFact", "Openllet", "Structural", "abstract_reasoner"])
    parser.add_argument("--operation", type=str, default="normal", choices=["incomplete", "inconsistent", "normal"])
    parser.add_argument("--use_cache", type=bool, default=True, help="Use the semantic cache for the reasoners")
    parser.add_argument("--ratio", type=float, default=0.1, help="level of incompleteness, inconsistencies")
    dl_concept_learning(parser.parse_args())

