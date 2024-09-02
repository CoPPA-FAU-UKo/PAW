import os
import pandas as pd
import numpy as np


def read_files(folder_path, suffix=".pkl"):
    # Dictionary to hold DataFrames
    dataframes = {}
    # List all files in the folder
    for filename in os.listdir(folder_path):
        # Check if the file is a CSV
        if filename.endswith(suffix):
            file_path = os.path.join(folder_path, filename)
            # Read the CSV file into a DataFrame
            df = pd.DataFrame()
            if suffix[-4:] == ".pkl":
                df = pd.read_pickle(file_path)
            elif suffix[-4:] == ".csv":
                df = pd.read_csv(file_path, low_memory=False)
            elif suffix[-5:] == ".json":
                df = pd.read_json(file_path)
            # Use the filename without extension as the key
            key = os.path.splitext(filename)[0]
            dataframes[key] = df
    return dataframes
