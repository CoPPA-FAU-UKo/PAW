import numpy as np
import pandas as pd
from src.Log import Reformat
from src.Preprocessing import Extraction
from src.Preprocessing import Preprocess


def prepare_log(json_log):
    data_trace = Reformat.roll_sequence(Extraction.extract(json_log), time_column="endDate", case_column="Case ID")
    data_trace = data_trace.reset_index()
    data_trace["RemTime"] = data_trace["endDate"].apply(Preprocess.cal_remtime)
    data_trace["LapseTime"] = data_trace["endDate"].apply(Preprocess.cal_lapse)
    train, val, test, le = Preprocess.split_encode(data_trace, ["Activity"])

    return train, val, test, le
