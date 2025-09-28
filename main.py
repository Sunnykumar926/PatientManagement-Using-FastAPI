from fastapi import FastAPI, Path, HTTPException, Query
from pydantic import BaseModel, Field, computed_field
from fastapi.responses import JSONResponse
from typing import Annotated, Literal, Optional
import json

app = FastAPI()


class Patient(BaseModel):

    id : Annotated[str, Field(..., description='Id of the patient', examples=['P001'])]
    name: Annotated[str, Field(..., description='Name of the patient')]
    city: Annotated[str, Field(..., description='City where the patient is living')]
    age: Annotated[int, Field(..., gt=0, lt=120, description='Age of the patient')]
    gender: Annotated[Literal['male', 'female', 'others'], Field(..., description='Gender of the patient')]
    height: Annotated[float, Field(..., description='Height of the patient in mtrs')]
    weight: Annotated[float, Field(..., description='Weight of the patient in kgs')]

    @computed_field
    @property
    def bmi(self) -> float:
        return round(self.weight/(self.height**2), 2)
    
    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi<18.5:
            return 'Underweight'
        elif self.bmi < 30:
            return 'Normal'
        else: return 'obese'

class PatientUpdate(BaseModel):

    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age : Annotated[Optional[int], Field(default=None, gt=0)]
    gender: Annotated[Optional[Literal['male', 'female']], Field(default=None)]
    height: Annotated[Optional[float], Field(default=None, gt=0)]
    weight: Annotated[Optional[float], Field(default=None, gt=0)]
    
def save_data(data):
    with open('patient.json', 'w') as f:
        json.dump(data, f)



def load_data():
    with open('patient.json', 'r') as f:
        data = json.load(f)
    return data

@app.get('/')   # here we define the route of our end point with the help of decorator which directly run hello function
def hello():
    return {'message':'Patient Management System API'}

@app.get('/about')
def about():
    return {'message':'A fully functions API to manage your patient records'}


@app.get('/patient')
def view():
    data = load_data()
    return data

@app.get('/patient/{patient_id}')
def view_patient(patient_id: str = Path(..., description='ID of the patient in the DB', example='P001')):
    data = load_data()

    if patient_id in data:
        return data[patient_id]
    raise HTTPException(status_code=404, detail='Patient not found')

@app.get('/sort')
def sort_patients(sort_by: str = Query(..., description='Sort on the basis of height, weight and bmi'), order: str = Query('asc', description='sort in the asc or desc order')):

    valid_fields=['height', 'weight', 'bmi']

    if sort_by not in valid_fields:
        raise HTTPException(status_code = 400,detail=f'Invalid field Select from {valid_fields}')
    
    if order not in ['asc', 'desc']:
        raise HTTPException(status_code=400, detail=f'Invalid order select between asc and desc')
    
    data = load_data()
    sort_order=True if order=='desc' else False
    sorted_data = sorted(data.values(), key=lambda x: x.get(sort_by, 0), reverse=sort_order)

    return sorted_data

@app.post('/create')
def add_patient(patient: Patient):
    
    data = load_data()

    if patient.id in data:
        raise HTTPException(status_code=400, detail='Patient already exist')
    
    data[patient.id]=patient.model_dump(exclude=['id'])

    save_data(data)

    return JSONResponse(status_code=200, content={'message': 'new patient added successfully'})


@app.put('/edit/{patient_id}')
def update_patient(patient_id: str, patient_update: PatientUpdate):

    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail='Patient not found')
    
    existing_patient_info = data[patient_id]
    update_patient_info= patient_update.model_dump(exclude_unset=True)

    for key, value in update_patient_info.items():

        existing_patient_info[key]=value

    existing_patient_info['id'] = patient_id
    patient_pydantic_obj = Patient(**existing_patient_info)
    existing_patient_info = patient_pydantic_obj.model_dump(exclude='id')

    # add this data to the dict
    data[patient_id]=existing_patient_info

    save_data(data)
    return JSONResponse(status_code=200, content={'message': 'patient information updated'})

@app.delete('/delete/{patient_id}')
def delete_patient(patient_id: str):

    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail='Patient not found')
    
    del data[patient_id]
    
    save_data(data)

    return JSONResponse(status_code=200, content={'message': 'patient deleted'})
