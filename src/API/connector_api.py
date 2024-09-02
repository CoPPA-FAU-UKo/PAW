import requests
import pandas as pd

class NoTrainingDataAvailable(Exception):
    "There is no training data available for the given instance, all instances with corresponding definition key may be not active or the instance key may not exist."
    pass

class NoPredictionInputDataAvailable(Exception):
    "There is no prediction input data available for the given instance. The instance may not exist or be not active."
    pass

#function to get the training data from the Connector API
#the parameter columns is a list containing the columns that are in the prediction data
def get_training_data(processDefinitionKey: str, columns: list):
    print("Training method started")
    #URL definition (first for docker, second localhost)
    # url = "http://coppaconnector:8080/ConnectorExport/" + str(processDefinitionKey)
    url = "http://localhost:8080/ConnectorExport/" + str(processDefinitionKey)

    data = []
    #request to the Connector API
    response = requests.get(url)
    if response.status_code != 200:
        print("Error on request for training data")
        message = str(response.content)
        raise NoTrainingDataAvailable(message[2:len(message)-1])
    else:
        data = response.json()
        print("Request for training data successful")

    #filling a Pandas dataframe with the data
    df = pd.json_normalize(data)
    df = data_prep(df)

    #columns, that are not in prediction data, are dropped
    for col in df.columns:
        if col == 'nextFlowNodeId' or col == 'nodeDuration' or col == 'nodeIncident':
            continue
        if len(columns)!=0 and col not in columns:
            df = df.drop([col], axis=1)

    #columns, that are in prediction data, but not in training data, are added and mapped to 0
    if(len(columns)!=0):
        for col in columns:
            if col not in df.columns:
                df[col] = 0

    #columns are sorted alphabetically to ensure the same order in training and prediction data
    df = df.reindex(sorted(df.columns), axis=1)
    return df

# the data for the prediction is requested from the Connector API
def get_prediction_input(processInstanceKey : str):
    print("Prediction method started")
    # URL definition (first for docker, second localhost)
    # url = "http://coppaconnector:8080/PredictionInput/" + str(processInstanceKey)
    url = "http://localhost:8080/PredictionInput/" + str(processInstanceKey)

    # request to the Connector API
    response = requests.get(url)
    if response.status_code != 200:
        print("Error on request for prediction input data")
        message = str(response.content)
        raise NoPredictionInputDataAvailable(message[2:len(message)-1])
    else:
        data = response.json()
        print("Request for prediction data successful")

    # filling a Pandas dataframe with the data
    df = pd.json_normalize(data)

    return df

#data preparation as a function that can also be used on the prediction data
def data_prep(df: pd.DataFrame):

    # drop the state as the state in the prediction input data is always 'ACTIVE'
    df = df.drop(['nodeState'], axis=1)

    stringVars = []
    #building a list of all String process variables
    for col in df.columns:
        if col.startswith('variablesString'):
            stringVars.append(col)

    #One-Hot-Encoding
    cls = ['nodeType', 'bpmnProcessId', 'processState', 'flowNodeId']
    cls.extend(stringVars)
    df = pd.get_dummies(df, columns = cls)

    #basic NaN handling. Booleans will be False, Strings will be 'missing' and Floats will be 0.0
    for col in df.columns:
        if col.startswith('variablesBool'):
            df[col].fillna(False, inplace=True)
        elif col.startswith('variablesString'):
            df[col].fillna('missing', inplace=True)
        elif col.startswith('variablesDouble'):
            df[col].fillna(0.0, inplace=True)
        elif col.startswith('executionFlow'):
            df[col].fillna(0, inplace=True)
    return df