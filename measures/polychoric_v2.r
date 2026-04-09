# ==========================================
# 1. LOAD LIBRARIES
# ==========================================
library(bootnet)
library(qgraph)
library(igraph)
library(NetworkComparisonTest)

# ==========================================
# 2. CONFIGURATION & DATA SOURCES
# ==========================================
vars <- c('trstlgl', 'trstplc', 'trstplt', 'trstsci', 'ccrdprs', 'gincdif', 'lrscale', 'imwbcnt', 'rlgdgr')

urls <- list(
  czech = "https://raw.githubusercontent.com/chiarapicardii/NetworkAnalysis/refs/heads/main/data/csv/czech_cleaned_data.csv",
  finland = "https://raw.githubusercontent.com/chiarapicardii/NetworkAnalysis/refs/heads/main/data/csv/finland_cleaned_data.csv",
  gb = "https://raw.githubusercontent.com/chiarapicardii/NetworkAnalysis/refs/heads/main/data/csv/greatbritain_cleaned_data.csv",
  france = "https://raw.githubusercontent.com/chiarapicardii/NetworkAnalysis/refs/heads/main/data/csv/france_cleaned_data.csv",
  greece = "https://raw.githubusercontent.com/chiarapicardii/NetworkAnalysis/refs/heads/main/data/csv/greece_cleaned_data.csv",
  hungary = "https://raw.githubusercontent.com/chiarapicardii/NetworkAnalysis/refs/heads/main/data/csv/hungary_cleaned_data.csv",
  netherlands = "https://raw.githubusercontent.com/chiarapicardii/NetworkAnalysis/refs/heads/main/data/csv/netherlands_cleaned_data.csv",
  italy = "https://raw.githubusercontent.com/chiarapicardii/NetworkAnalysis/refs/heads/main/data/csv/italy_cleaned_data.csv"
)

# ==========================================
# 3. LOOP PROCESS ALL COUNTRIES
# ==========================================
all_data <- list() 

for (name in names(urls)) {
  message("--- Processing: ", toupper(name), " ---")
  
  # A. LOAD AND SELECT VARS (Keep NAs for Pairwise)
  df <- read.csv(urls[[name]])
  net_data <- df[, vars]
  
  # B. CLEANING (Numerical check only)
  # Check for zero-variance columns (must exist to calculate correlations)
  v <- sapply(net_data, var, na.rm = TRUE)
  bad_cols <- names(v[is.na(v) | v == 0])
  if(length(bad_cols) > 0) {
    net_data <- net_data[, !(names(net_data) %in% bad_cols)]
    message("   ! Removed zero-variance column(s): ", paste(bad_cols, collapse=", "))
  }
  
  clean_df <- as.data.frame(lapply(net_data, as.numeric))
  all_data[[name]] <- clean_df # Store with NAs intact
  
  # C. ESTIMATE NETWORK (EBICglasso + Pairwise Deletion)
  # cor_auto with missing = "pairwise" handles NAs automatically for the matrix
  net_est <- estimateNetwork(clean_df, default = "EBICglasso", 
                             corMethod = "cor_auto", 
                             corArgs = list(ordinalLevelMax = 11, missing = "pairwise"))
  
  # D. CREATE IGRAPH & ENRICH WITH METRICS
  g <- graph_from_adjacency_matrix(net_est$graph, mode = "undirected", weighted = TRUE)
  
  V(g)$label <- V(g)$name
  V(g)$weighted_degree <- strength(g)
  V(g)$betweenness <- betweenness(g)
  V(g)$closeness <- closeness(g)
  V(g)$modularity_class <- cluster_louvain(g)$membership
  
  cc <- transitivity(g, type = "local")
  cc[is.na(cc)] <- 0
  V(g)$clustering_coefficient <- cc
  
  # E. EXPORT FOR GEPHI
  nodes_out <- as_data_frame(g, what = "vertices")
  colnames(nodes_out)[1] <- "Id"
  nodes_out$Label <- nodes_out$Id
  
  edges_out <- as_data_frame(g, what = "edges")
  colnames(edges_out)[1:2] <- c("Source", "Target")
  # Essential for Gephi's layout engines
  edges_out$weight <- abs(edges_out$weight) 
  
  write.csv(nodes_out, paste0(name, "_nodes.csv"), row.names = FALSE)
  write.csv(edges_out, paste0(name, "_edges.csv"), row.names = FALSE)
  
  message("   v Success: CSVs saved for ", name)
}

message("===========================================")
message("ALL COUNTRIES PROCESSED (PAIRWISE).")
message("===========================================")
