#  Copyright (c) 2023. Davi Pereira dos Santos
#  This file is part of the sortedness project.
#  Please respect the license - more about this in the section (*) below.
#
#  sortedness is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  sortedness is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with sortedness.  If not, see <http://www.gnu.org/licenses/>.
#
#  (*) Removing authorship by any means, e.g. by distribution of derived
#  works or verbatim, obfuscated, compiled or rewritten versions of any
#  part of this work is illegal and it is unethical regarding the effort and
#  time spent here.
#
from functools import partial
from itertools import chain

from hyperopt import hp, fmin, tpe, STATUS_OK, Trials
from numpy import mean
from numpy.random import default_rng
from scipy.stats import weightedtau, kendalltau
from torch.optim import RMSprop

from sortedness import sortedness
from sortedness.embedding.sortedness_ import balanced_embedding
from sortedness.embedding.surrogate import cau
from sortedness.local import geomean_np


def tuple2hyperopt(key, v):
    if type(v) is tuple and type(v[0]) is int:
        return hp.quniform(key, *v, 1)
    if type(v) is tuple and type(v[0]) is float:
        return hp.uniform(key, *v)
    return hp.choice(key, v)


def balanced_embedding__opt(X, symmetric, swapXX_=False, d=2, gamma=4, k=17, global_k: int = "sqrt", beta=0.5, epochs=10,
                            embedding__param_space=None,
                            embedding_optimizer=RMSprop, embedding_optimizer__param_space=None,
                            hyperoptimizer_algorithm=None, max_evals=10, progressbar=False, return_trials=False,
                            min_global_k=100, max_global_k=1000, seed=0, gpu=False, show_parameters=True, **hyperoptimizer_kwargs):
    if symmetric and swapXX_:
        raise Exception(f"Conflicting flags: {symmetric=} and {swapXX_=}")
    if hyperoptimizer_algorithm is None:
        hyperoptimizer_algorithm = partial(tpe.suggest, n_startup_jobs=4, n_EI_candidates=8)
    if embedding__param_space is None:
        embedding__param_space = {}
    if embedding_optimizer__param_space is None:
        embedding_optimizer__param_space = {}

    for key, v in {"smooothness_tau": (0.0001, 20), "neurons": (d, 200), "batch_size": (1, min(200, len(X)))}.items():
        if key not in embedding__param_space:
            embedding__param_space[key] = v
    for key, v in {"lr": (0.0001, 0.1), "alpha": (0.90, 0.99), "weight_decay": (0.0, 0.1), "momentum": (0.0, 0.1), "centered": [True, False]}.items():
        if key not in embedding_optimizer__param_space:
            embedding_optimizer__param_space[key] = v

    space = {}
    for key, v in chain(embedding__param_space.items(), embedding_optimizer__param_space.items()):
        space[key] = tuple2hyperopt(key, v)

    if "algo" not in hyperoptimizer_kwargs:
        hyperoptimizer_kwargs["algo"] = hyperoptimizer_algorithm
    if "max_evals" not in hyperoptimizer_kwargs:
        hyperoptimizer_kwargs["max_evals"] = max_evals
    if "show_progressbar" not in hyperoptimizer_kwargs:
        hyperoptimizer_kwargs["show_progressbar"] = progressbar
    if "trials" not in hyperoptimizer_kwargs:
        trials = Trials()
        hyperoptimizer_kwargs["trials"] = trials
    else:
        trials: Trials = hyperoptimizer_kwargs["trials"]

    def taus(r, r_):
        tau_local = weightedtau(r, r_, weigher=partial(cau, gamma), rank=False)[0]
        tau_global = kendalltau(r, r_)[0]
        return geomean_np(tau_local, tau_global)

    bestval = [-1]

    def objective(space):
        embedding__kwargs = {key: (v if key == "smooothness_tau" else int(v))
                             for key, v in space.items()
                             if key in ["smooothness_tau", "neurons", "batch_size"]}
        embedding_optimizer__kwargs = {key: v for key, v in space.items() if key not in embedding__kwargs}
        if show_parameters:
            print("___________________________________")
            print(embedding__kwargs, flush=True)
            print(embedding_optimizer__kwargs, flush=True)
        X_ = balanced_embedding(X, symmetric, d, gamma, k, global_k, beta, **embedding__kwargs,
                                embedding_optimizer=embedding_optimizer,
                                min_global_k=min_global_k, max_global_k=max_global_k, seed=seed, gpu=gpu, **embedding_optimizer__kwargs)
        quality = mean(sortedness(X_, X, symmetric=symmetric, f=taus)) if swapXX_ else mean(sortedness(X, X_, symmetric=symmetric, f=taus))

        if quality > bestval[0]:
            bestval[0] = quality
        else:
            X_ = None

        if show_parameters:
            print("\n", quality, flush=True)
        return {"loss": -quality, "status": STATUS_OK, "X_": X_}

    rnd = default_rng(seed)
    fmin(fn=objective, space=space, rstate=rnd, **hyperoptimizer_kwargs)
    X_ = trials.best_trial["result"]["X_"]
    if show_parameters:
        dct = {k: round(v[0], 3) for k, v in trials.best_trial["misc"]["vals"].items()}
        print("Best:", dct, f"λ:\t{-trials.best_trial['result']['loss']}", flush=True, sep="\t")
    return (X_, trials) if return_trials else X_
