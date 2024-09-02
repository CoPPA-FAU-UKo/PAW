from fastapi import FastAPI
import uvicorn
from prediction import predict_rfc, predict_xgb
from connector_api_service import get_training_data, get_prediction_input, data_prep, NoTrainingDataAvailable, NoPredictionInputDataAvailable
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

class ProcessInstancePrediction():
    key: float
    resultsRFC: list
    resultsXGB: list

class PredictionResult():
    flowNodeId: str
    nextFlowNode: str
    probabilityForNextFlowNode: str
    incident: str
    probabilityForIncident: str
    duration: str
    probabilityForDuration: str

# FastAPI initialisation
app = FastAPI()

# endpoint for exporting the prediciton
@app.get("/prediction_export/{processInstanceKey}")
async def prediction_export(processInstanceKey: str):
    # input for the prediction is requested from the Connector API via a function from connector_api_service.py
    try:
        df_input = get_prediction_input(processInstanceKey)
    except NoPredictionInputDataAvailable as e:
        print(str(e))
        return str(e)

    # training data is requested from the Connector API via a function from connector_api_service.py
    columns = data_prep(df_input.copy()).columns
    processDefinitionKey = df_input['processDefinitionKey'][0]
    try:
        df_training = get_training_data(processDefinitionKey, columns)
    except NoTrainingDataAvailable as e:
        print(str(e))
        return str(e)

    # predictions for the specified dataframe input and traing data
    prediction_rfc = predict_rfc(df_input, df_training)
    prediction_xgb = predict_xgb(df_input, df_training)

    # generating response object
    response = ProcessInstancePrediction()
    response.key = float(processInstanceKey)
    results_rfc = list()
    results_xgb = list()

    # fill the results list with the predictions of the corresponding classifier
    fill_results_list(results_rfc, prediction_rfc)
    fill_results_list(results_xgb, prediction_xgb)

    response.resultsRFC = results_rfc
    response.resultsXGB = results_xgb

    # return respose in json format
    json_compatible_item_data = jsonable_encoder(response)
    return JSONResponse(content=json_compatible_item_data)

def fill_results_list(results : list, prediction : list):

    i = 0
    while i<len(prediction[0]):
        result = PredictionResult()
        # put predictions in result object
        result.flowNodeId = str(prediction[0][i])
        result.nextFlowNode = str(prediction[1])
        result.probabilityForNextFlowNode = str(prediction[2][i])
        result.incident = str(prediction[3][i])
        result.probabilityForIncident = str(prediction[4][i].max())
        result.duration = str(prediction[5][i])
        result.probabilityForDuration = str(prediction[6][i].max())
        results.append(result)
        i += 1

# start FastAPI application with command "uvicorn api:app" (or "python -m uvicorn api:app --reload") after "cd Trainer"
if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)