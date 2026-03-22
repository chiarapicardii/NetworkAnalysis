# import necessary libraries
import argparse
import itertools
import os
import numpy as np
import pandas as pd
import networkx as nx

from sklearn.covariance import GraphicalLasso
from sklearn.preprocessing import StandardScaler

# ──────────────────────────────────────────────
# Variable definitions
# ──────────────────────────────────────────────
VARIABLES = {
    "trstplt": "Trust in Politicians",
    "trstplc": "Trust in Police",
    "trstsci": "Trust in Scientists",
    "trstlgl": "Trust in Legal System",
    "ccrdprs": "Personal Responsibility (Climate)",
    "imwbcnt": "Immigrants: Country Better/Worse",
    "lrscale": "Left-Right Scale",
    "gincdif": "Gov. Reduce Income Differences",
    "rlgdgr": "How Religious Are You",
}
VAR_NAMES = list(VARIABLES.keys())

# ──────────────────────────────────────────────
# Preprocessing
# ──────────────────────────────────────────────

# Preprocess the data to make the direction of agreement consistent across variables
    # for "gincdif" ( originally 1 = Agree strongly, 5 = Disagree strongly -> transformed to 0 = Agree strongly, 10 = Disagree strongly ), 
    # we reverse the scale:
    # 1(Agree strongly) → 10
    # 5(Disagree strongly) → 0
    # This makes the direction of agreement consistent across variables
def preprocess(input_csv, missing_threshold=0.3):
    df = pd.read_csv(input_csv, encoding="utf-8", sep=",")
    df["gincdif_r"] = 10 - df["gincdif"]

    # Because France and Czech were missing too many values for "trstsci"
    missing_rate = df[VAR_NAMES].isnull().mean() # Calculate the percentage of missing values for each variable
    too_empty = missing_rate[missing_rate > missing_threshold].index.tolist()
    if too_empty:
        print(f"Warning: The following variables have more than {missing_threshold*100:.0f}% missing values and will be dropped: {too_empty}")
        
    usable_vars = [v for v in VAR_NAMES if v not in too_empty]
    return df, usable_vars

# ──────────────────────────────────────────────
# Correlation computation using Graphical Lasso
# ──────────────────────────────────────────────

def compute_glasso(df, variables, alpha=0.01):
    X = df[variables].dropna().values     # shape: (n_samples, n_features)
    X = StandardScaler().fit_transform(X) # GL assumes standardized data

    model = GraphicalLasso(alpha=alpha, max_iter=500) # L1 regularization zeros out weak edges during fitting (instead of by abs_t >= threshold)
    # Fit model -> sparse precision matrix instead of computing all correlations
    model.fit(X)

    precision = pd.DataFrame(model.precision_, index=variables, columns=variables)
    # Convert precision to partial correlation
    results = []
    for var1, var2 in itertools.combinations(variables, 2):
        p12 = precision.loc[var1, var2] # off-diagonal: joint precision of var1 and var 2
        p11 = precision.loc[var1, var1] # diagonal: variance-like term for var1
        p22 = precision.loc[var2, var2] # diagonal: variance-like term for var2
        partial_r = -p12 / np.sqrt(p11 * p22) # how strongly are var1 and var2 related, holding all other variables constant

        sign_str = "positive" if partial_r > 0 else ("negative" if partial_r < 0 else "zero")
        results.append({
            "var1": var1,
            "var2": var2,
            "label1": VARIABLES.get(var1, var1),
            "label2": VARIABLES.get(var2, var2),
            "r": round(partial_r, 4), # partial correlation coefficient
            "abs_r": round(abs(partial_r), 4), # absolute value, e.g. 0.3421
            "sign": sign_str, # positive, negative, or zero correlation
        })
    
    # Converts list of dictionaries into a table: each row corresponds to a pair of variables,
    # with columns for the keys, e.g. variable names, labels, correlation coefficient, etc.
    return precision, pd.DataFrame(results)

#  ──────────────────────────────────────────────
# create a gefx file for Gephi visualization
# ──────────────────────────────────────────────
def build_network(results_df, output_file, threshold):
    G = nx.Graph()

    for var, label in VARIABLES.items():
        G.add_node(var, label=label)

    filtered = results_df[results_df["abs_r"] >= threshold].copy()
    print(f"Number of edges with |r| >= {threshold}: {len(filtered)}")

    for _, row in filtered.iterrows():
        color = "0000FF" if row["sign"] == "positive" else "FF0000"
        G.add_edge(
            row["var1"], row["var2"],
            weight=float(row["abs_r"]),
            r=float(row["r"]),
            sign=row["sign"],
            color=color,
        )
    

    # ── compute weight degree and Betweenness Centrality 
    for u, v, d in G.edges(data=True):
        d["distance"] = 1.0 / d["weight"] if d["weight"] > 0 else 1e6

    bc = nx.betweenness_centrality(G, weight="distance", normalized=True)
    wd = {n: sum(d["weight"] for _, _, d in G.edges(n, data=True)) for n in G.nodes()}
    dg = dict(G.degree())

    print("\n=== Betweenness Centrality ===")
    for node, val in sorted(bc.items(), key=lambda x: -x[1]):
        print(f"  {node:10s}  BC={val:.4f}  WeightedDeg={wd[node]:.4f}  Deg={dg[node]}")

    for node in G.nodes():
        G.nodes[node]["betweenness_centrality"] = round(bc[node], 6)
        G.nodes[node]["weighted_degree"]        = round(wd[node], 6)
        G.nodes[node]["degree"]                 = dg[node]

    nx.write_gexf(G, output_file)
    print(f"Network saved to {output_file}")

# ──────────────────────────────────────────────
# implementation
# ──────────────────────────────────────────────

# PREPROCESSING
#divide_by_lr("finlandSubset.csv", "fin_left_group.csv", "fin_right_group.csv")
#df = preprocess("data/finland_cleaned_data.csv")
#df, usable_vars = preprocess("data/france_cleaned_data.csv")

# COMPUTING
#precision, results_df = compute_glasso(df, usable_vars, alpha=0.1)

# BUILDING NETWORK
#build_network(results_df, "fra_glasso_network.gexf", threshold=0.0)

# THis goes quicker
for filename in os.listdir("data"):
    if filename.endswith("_cleaned_data.csv"):
        country = filename.split("_")[0]
        print(f"\nProcessing {country}...")
        df, usable_vars = preprocess(os.path.join("data", filename))
        precision, results_df = compute_glasso(df, usable_vars, alpha=0.1)
        build_network(results_df, f"{country}_glasso_network.gexf", threshold=0.0)