import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

def clean_data(input_file, output_file, columns, country_code=None, deletion_criteria=None, normalize_criteria=None, reverse_scale_columns=None):
    """
    Read a CSV file, keep only specified columns, apply filters and transformations, and save to a new file.
    
    Args:
        input_file (str): Path to the input CSV file
        output_file (str): Path to the output CSV file
        columns (list): List of column names to keep
        country_code (str): Country code to filter the data (e.g., 'IT' for Italy). If None, no country filtering is applied.
        deletion_criteria (dict): Dictionary where keys are column names and values are lists of values to exclude
        normalize_criteria (dict): Dictionary where keys are column names and values are tuples (min_value, max_value) to normalize the scale
        reverse_scale_columns (list): List of column names to reverse the scale
    """
    df = pd.read_csv(input_file, encoding='utf-8', sep=',')
    df_filtered = df[columns].copy()
    print(f"Filtered columns: {columns}")

    # Filter by country code if provided
    if country_code is not None:
        df_filtered = df_filtered[df_filtered['cntry'] == country_code].copy()
        print(f"Filtered by country code: {country_code}")

    # replace invalid values to NaN
    df_filtered.replace(deletion_criteria, pd.NA, inplace=True)
    print(f"Null values introduced based on criteria: {deletion_criteria}")

    # normalize to 0 to 10
    if normalize_criteria is not None:
        for column, (min_val, max_val) in normalize_criteria.items():
            if column in df_filtered.columns:
                df_filtered[column] = pd.to_numeric(df_filtered[column], errors='coerce')
                non_null = df_filtered[column].notna()
                if non_null.any():
                    scaler = MinMaxScaler(feature_range=(0, 10))
                    scaled = scaler.fit_transform(df_filtered.loc[non_null, [column]])
                    df_filtered.loc[non_null, column] = scaled.flatten()
                    print(f"Normalized column '{column}' to range [0, 10]")
                else:
                    print(f"No valid numeric data in column '{column}' for normalization")

    # reverse scale for specified columns
    if reverse_scale_columns is not None:
        for column in reverse_scale_columns:
            if column in df_filtered.columns:
                df_filtered[column] = 10 - df_filtered[column]
                print(f"Reversed scale for column '{column}'")

    df_filtered.to_csv(output_file, index=False)
    print(f"Cleaned CSV saved to {output_file}")

#Execution

raw_data_file ='data/raw_data.csv'
output_file = 'data/finland_cleaned_data.csv'

# list to filter columns
columns_list = ['name', 'proddate','idno', 'agegroup', 'cntry', 'gndr', 'trstlgl', 'trstplc', 'trstplt', 'trstsci', 'ccrdprs', 'gincdif', 'lrscale', 'imwbcnt', 'rlgdgr']

#country code
country_code = 'FI'
# finland = 'FI'
# united kingdom = 'GB'
# netherlands = 'NL'
# greece = 'GR'
# czech republic = 'CZ'
# hungary = 'HU'
# france = 'FR'
# italy = 'IT'
# swizerland = 'CH'


# the values to be replaced with NaN for each column
deletion_criteria = {
    'trstlgl': [77, 88, 99],
    'trstplc': [77, 88, 99],
    'trstplt': [77, 88, 99],
    'trstsci': [77, 88, 99],
    'ccrdprs': [66, 77, 88, 99],
    'gincdif': [7, 8, 9],   
    'lrscale': [77, 88, 99],
    'imwbcnt': [77, 88, 99],
    'rlgdgr': [77, 88, 99]
    }

# columns to normalize and their original min and max values
normalize_criteria = {
    'gincdif': (1, 5)
}

# columns to reverse the scale
reverse_scale_columns = ['gincdif']

clean_data(raw_data_file, output_file, columns_list, country_code, deletion_criteria=deletion_criteria, normalize_criteria=normalize_criteria, reverse_scale_columns=reverse_scale_columns)