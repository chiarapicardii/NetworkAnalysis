# import necessary libraries
import argparse
import itertools
import numpy as np
import pandas as pd
import networkx as nx
from xarray import corr

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
    #"lrscale": "Left-Right Scale",
    "gincdif": "Gov. Reduce Income Differences",
    #"aesfdrk": "Safety Walking Alone After Dark",
}
VAR_NAMES = list(VARIABLES.keys())

# ──────────────────────────────────────────────
# Preprocessing
# ──────────────────────────────────────────────

# divide data by left-right scale
def divide_by_lr(input_csv, left_output, right_output):
    df = pd.read_csv(input_csv, encoding="utf-8", sep=",")
    left = df[df["lrscale"] < 5].copy()
    right = df[df["lrscale"] > 5].copy()
    left.to_csv(left_output, index=False)
    right.to_csv(right_output, index=False)
    print(f"left and right data saved")

# Preprocess the data to make the direction of agreement consistent across variables
    # for "gincdif" ( originally 1 = Agree strongly, 5 = Disagree strongly -> transformed to 0 = Agree strongly, 10 = Disagree strongly ), 
    # we reverse the scale:
    # 1(Agree strongly) → 10
    # 5(Disagree strongly) → 0
    # This makes the direction of agreement consistent across variables
def preprocess(input_csv):
    df = pd.read_csv(input_csv, encoding="utf-8", sep=",")
    df["gincdif_r"] = 10 - df["gincdif"]
    return df

# ──────────────────────────────────────────────
# Compute edges: correlation coefficient
# ──────────────────────────────────────────────
# Compute pairwise correlations between variables with Pearson Correlation method

def compute_correlations(df, variables):
    n = len(variables)
    corr_matrix = pd.DataFrame(np.zeros((n, n)), index=variables, columns=variables)

    pairs = list(itertools.combinations(variables, 2))
    total = len(pairs)

    print(f"Computing correlations for {total} pairs...")

    results = []
    for idx, (var1, var2) in enumerate(pairs):
        print (f"Processing pair [{idx + 1}/{total}] {var1:10s} x {var2:10s}", end="", flush=True)

        r = df[var1].corr(df[var2], method="pearson")
        corr_matrix.loc[var1, var2] = r
        corr_matrix.loc[var2, var1] = r

        print(f" → Correlation: {r:.4f}")

        sign_str = "positive" if r > 0 else ("negative" if r < 0 else "zero")
        results.append({
            "var1": var1,
            "var2": var2,
            "label1": VARIABLES.get(var1, var1),
            "label2": VARIABLES.get(var2, var2),
            "r": round(r, 4),
            "abs_r": round(abs(r), 4),
            "sign": sign_str
        })

    results_df = pd.DataFrame(results)
    return corr_matrix, results_df


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
#df = preprocess("fin_left_group.csv")

# COMPUTING
#corr_matrix, results_df = compute_correlations(df, VAR_NAMES)

# BUILDING NETWORK
#build_network(results_df, "fin_left_correlation_network.gexf", threshold=0.01)
