import pandas as pd

def extract(log):
    data = log[log["nodeState"] == "COMPLETED"].drop(columns=["nodeState"])
    data = data[data["processState"] == "COMPLETED"].drop(columns=["processState"])
    data = data[data["nodeType"] == "USER_TASK"]
    data["startDate"] = data["startDate"].apply(pd.to_datetime)
    data["endDate"] = data["endDate"].apply(pd.to_datetime)
    data = data.rename(columns={"processInstanceKey": "Case ID", "flowNodeId": "Activity"})
    data_core = data[["Case ID", "Activity", "endDate"]]

    return data_core
