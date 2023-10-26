#%%

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Union
import numpy as np
import pandas as pd
import os
from zipfile import ZipFile

@dataclass
class BaseTemplate:
    # material metadata
    wafer_id: str
    die_x: int
    die_y: int
    device_id: str
    tapeout_name: str
    extra_material_metadata: dict  # any additional material information can go here (eg, ticket ID...)

    # test metadata
    nominal_temperature_K: float
    measured_temperature_K: float
    test_conditions: dict  # information about the test (integration time, etc...)

    # measurement_type_name will be set below for IV and PCR
    measurement_type_name = ""

    def get_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame()

    def to_json(self, filepath: Union[str, Path]):
        """
        write data object to json file
        """
        data = dict()
        data["test_meta"] = dict(
            test_conditions=self.test_conditions,
            test_run=dict(
                wafer_id=self.wafer_id,
                die_x=self.die_x,
                die_y=self.die_y,
                device_id=self.device_id,
                tapeout_name=self.tapeout_name,
                measurement_type_name=self.measurement_type_name,
                temperature_k=self.nominal_temperature_K,
                **self.extra_material_metadata,
            ),
            test_station_metadata=dict(temperature_user1_k=self.measured_temperature_K),
        )
        data["data"] = self.get_dataframe().to_dict("split")

        with open(filepath, "w") as f:
            json.dump(data, f)


@dataclass
class IVTemplate(BaseTemplate):
    voltage_source_V: List[float]
    voltage_source_applied_V: List[float]
    current_measure_A: List[float]
    voltage_snspd_measure_V: List[float]

    measurement_type_name = "SNSPD IV"

    def get_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            data=dict(
                voltage_source_V=self.voltage_source_V,
                voltage_source_applied_V=self.voltage_source_applied_V,
                current_measure_A=self.current_measure_A,
                voltage_snspd_measure_V=self.voltage_snspd_measure_V,
            )
        )


@dataclass
class PCRTemplate(BaseTemplate):
    voltage_source_V: List[float]
    voltage_source_applied_V: List[float]
    current_measure_A: List[float]
    voltage_snspd_measure_V: List[float]
    attenuation_dB: List[float]
    wavelength_m: List[float]
    count_rate_measured_cps: List[float]

    measurement_type_name = "SNSPD Flood"

    def get_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            data=dict(
                voltage_source_V=self.voltage_source_V,
                voltage_source_applied_V=self.voltage_source_applied_V,
                current_measure_A=self.current_measure_A,
                voltage_snspd_measure_V=self.voltage_snspd_measure_V,
                attenuation_dB=self.attenuation_dB,
                wavelength_m=self.wavelength_m,
                optical_power_coupler_2_dBm=None,  # extra column not applicable to NIST data
                count_rate_measured_cps=self.count_rate_measured_cps,
            )
        )

def pcr_data_to_json(
    df,
    jira_ticket, #  = "SCE-219"
    wafer_id,
    die_x,
    die_y,
    tapeout_name,
    path = '',
    ):

    test_conditions = dict(
        rbias = float(df.rbias.unique()[0]),
        vtrig = float(df.vtrig.median()),
        count_time = float(df.count_time.median()),
        )
    extra_material_metadata = dict(jira_ticket = jira_ticket)
    filepaths = []
    for (device_name, wavelength, temperature), df2 in df.groupby(["device","wavelength","temperature"]):
        data_obj = PCRTemplate(
            wafer_id=wafer_id,
            die_x=die_x,
            die_y=die_y,
            device_id=device_name,
            tapeout_name=tapeout_name,
            extra_material_metadata=extra_material_metadata,
            test_conditions=test_conditions,
            nominal_temperature_K=float(temperature),
            measured_temperature_K=float(df2.temperature_meas.median()),
            voltage_source_V = df2.voltage_source_V.to_list(),
            voltage_source_applied_V =  df2.voltage_source_applied_V.to_list(),
            current_measure_A =  df2.current_measure_A.to_list(),
            voltage_snspd_measure_V =  df2.voltage_snspd_measure_V.to_list(),
            attenuation_dB =  df2.attenuation_db.to_list(),
            wavelength_m =  (df2.wavelength*1e-9).to_list(),
            count_rate_measured_cps = df2.count_rate.to_list(),
            )
        filename = f"{tapeout_name}_wafer{wafer_id}_{jira_ticket}_PCR_{device_name}_{wavelength}nm_{temperature}K.json"
        filepath = os.path.join(path,filename)
        filepaths.append(filepath)
        data_obj.to_json(filepath)
    to_zip(path, filepaths, archive_name = f"json_{tapeout_name}_wafer{wafer_id}_{jira_ticket}_{wavelength}nm_PCR")


def iv_data_to_json(
    df,
    jira_ticket, #  = "SCE-219"
    wafer_id,
    die_x,
    die_y,
    tapeout_name,
    path = '',
    ):
    test_conditions = dict(rbias=float(df.rbias.unique()[0]))
    extra_material_metadata = dict(jira_ticket = jira_ticket)
    filepaths = []
    for (device_name, temperature), df2 in df.groupby(["device","temperature"]):
        data_obj = IVTemplate(
            wafer_id=wafer_id,
            die_x=die_x,
            die_y=die_y,
            device_id=device_name,
            tapeout_name=tapeout_name,
            extra_material_metadata=extra_material_metadata,
            test_conditions=test_conditions,
            nominal_temperature_K=temperature,
            measured_temperature_K=df2.temperature_meas.median(),
            voltage_source_V = df2.voltage_source_V.to_list(),
            voltage_source_applied_V =  df2.voltage_source_applied_V.to_list(),
            current_measure_A =  df2.current_measure_A.to_list(),
            voltage_snspd_measure_V =  df2.voltage_snspd_measure_V.to_list(),
            )
        filename = f"{tapeout_name}_wafer{wafer_id}_{jira_ticket}_IV_{device_name}_{temperature}K.json"
        filepath = os.path.join(path,filename)
        filepaths.append(filepath)
        data_obj.to_json(filepath)
    to_zip(path, filepaths, archive_name = f"json_{tapeout_name}_wafer{wafer_id}_{jira_ticket}_IV")


def to_zip(path, filepaths, archive_name):
    with ZipFile(os.path.join(path,f'{archive_name}.zip'), 'a') as zip_object:
        for filepath in filepaths:
            zip_object.write(filepath, arcname = os.path.basename(filepath))
            os.remove(filepath)


column_mapping = {
    'vbias' : 'voltage_source_applied_V',
    'vbias_measured' : 'voltage_source_V',
    'ibias_measured' : 'current_measure_A',
    'ibias_meas' : 'current_measure_A',
    'vdut' :'voltage_snspd_measure_V',
}


jira_ticket = input(f'Enter study number (e.g. SCE-123): ')
wafer_id = int(input(f'Enter wafer id: '))
die_x = int(input(f'Enter die-x: '))
die_y = int(input(f'Enter die-y: '))
tapeout_name = input(f'Tapeout name (e.g. TV4): ')

zip_path = r"C:\Users\anm16\Desktop\temp\psiq"

#%% IV curve data

# df = pd.read_csv(r'C:\Users\anm16\Downloads\2023-07-24-17-39-05-IV-curves.csv')
filename = input(f'Enter IV CURVE .csv filename: ')
df = pd.read_csv(filename)
print(f'IV Curve @ Study {jira_ticket} / wafer {wafer_id} / loc ({die_x},{die_y}) / tapeout {tapeout_name}')
print(f'filename {filename}\n\n')
df = df.rename(columns = column_mapping)

if ('temperature' not in df) and ('temperature_meas' not in df) and ('wavelength' not in df):
    df['temperature_meas'] = 0.8
    df['temperature'] = 0.8
iv_data_to_json(
    df,
    jira_ticket = jira_ticket,
    wafer_id=wafer_id,
    die_x=die_x,
    die_y=die_y,
    tapeout_name=tapeout_name,
    path = zip_path
    )

#%% PCR data
# df = pd.read_csv(r'C:\Users\anm16\Downloads\2023-07-06-13-10-40-counts-vs-bias-1(1).csv')
filename = input(f'Enter PCR .csv filename: ')
df = pd.read_csv(filename)
print(f'IV Curve @ Study {jira_ticket} / wafer {wafer_id} / loc ({die_x},{die_y}) / tapeout {tapeout_name}')
print(f'filename {filename}\n\n')
df = df.rename(columns = column_mapping)

if ('temperature' not in df) and ('temperature_meas' not in df) and ('wavelength' not in df):
    df['temperature_meas'] = 0.8
    df['temperature'] = 0.8
    df['wavelength'] = 1550

pcr_data_to_json(
    df,
    jira_ticket = jira_ticket,
    wafer_id=wafer_id,
    die_x=die_x,
    die_y=die_y,
    tapeout_name=tapeout_name,
    path = zip_path
    )