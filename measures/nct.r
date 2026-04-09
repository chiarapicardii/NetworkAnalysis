# ==========================================
# Network Comparison Test (NCT) for Two Countries
# ==========================================

library(bootnet)
library(qgraph)
library(igraph)
library(NetworkComparisonTest)

# --- DEFINE VARIABLES ---

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


# --- STEP 1: Choose your two countries ---
group_A_name <- "france" 
group_B_name <- "finland"

# --- STEP 2: Automatically match columns ---
# This ensures we only test variables that exist in BOTH datasets
common_vars <- intersect(names(all_data[[group_A_name]]), names(all_data[[group_B_name]]))

data_A <- all_data[[group_A_name]][, common_vars]
data_B <- all_data[[group_B_name]][, common_vars]

message("Running NCT for ", group_A_name, " vs ", group_B_name)
message("Common variables being tested: ", paste(common_vars, collapse=", "))

# --- STEP 2.5: Automatically delete rows that are the cause of eigen error (covariance 0 or NA for everyone) ---
# This step is to prevent 'eigen' error
is_valid <- function(x) {
  val <- na.omit(x)
  length(unique(val)) > 1 # OK if more than 2 unique values
}

keep_A <- sapply(data_A_raw, is_valid)
keep_B <- sapply(data_B_raw, is_valid)
final_vars <- names(keep_A[keep_A & keep_B])

data_A_final <- data_A_raw[, final_vars]
data_B_final <- data_B_raw[, final_vars]

# show removed variables if any
removed <- setdiff(common_vars, final_vars)
if(length(removed) > 0) {
  message("The following variables were deleted to avoid error: ", paste(removed, collapse=", "))
}

# --- STEP 3: Run the Test (Pairwise deletion) ---
message("starting NCT（it=1000 may take several minutes）...")

nct_result <- NCT(data_A_final, data_B_final, 
                  it = 1000, 
                  test.edges = TRUE, 
                  test.centrality = TRUE,
                  estimator = "cor_auto",
                  estimatorArgs = list(missing = "pairwise"), 
                  progressbar = TRUE)
# --- STEP 4: View Results ---
summary(nct_result)