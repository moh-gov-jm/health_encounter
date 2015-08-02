from trytond.pool import Pool
from .encounter import PatientEncounter
from .encounter_component_type import EncounterComponentType
from .components import *
from .appointment import CreateAppointmentEncounter


def register():
    Pool.register(
        EncounterComponentType,
        PatientEncounter,
        EncounterAnthro,
        EncounterAmbulatory,
        EncounterClinical,
        Directions,
        SecondaryCondition,
        DiagnosticHypothesis,
        SignsAndSymptoms,
        EncounterComponent,
        ChooseComponentTypeView,
        module='health_encounter', type_='model')

    Pool.register(
        EditComponentWizard,
        CreateAppointmentEncounter,
        module='health_encounter', type_='wizard')
