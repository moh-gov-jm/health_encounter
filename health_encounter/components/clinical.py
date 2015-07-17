from trytond.model import ModelSQL, ModelView, fields
from .base import BaseComponent, SIGNED_STATES as STATES

DASHER = ('-' * 15, )  # minimal text based spacer line


class EncounterClinical(BaseComponent):
    'Clinical'
    __name__ = 'gnuhealth.encounter.clinical'

    diagnosis = fields.Many2One(
        'gnuhealth.pathology', 'Presumptive Diagnosis',
        help='Presumptive Diagnosis. If no diagnosis can be made'
        ', encode the main sign or symptom.',
        states=STATES)

    secondary_conditions = fields.One2Many(
        'gnuhealth.secondary_condition',
        'clinical_component', 'Secondary Conditions',
        help='Other, Secondary conditions found on the patient',
        states=STATES)

    diagnostic_hypothesis = fields.One2Many(
        'gnuhealth.diagnostic_hypothesis',
        'clinical_component', 'Hypotheses / DDx',
        help='Other Diagnostic Hypotheses / Differential Diagnosis (DDx)',
        states=STATES)

    signs_symptoms = fields.One2Many(
        'gnuhealth.signs_and_symptoms',
        'clinical_component', 'Signs and Symptoms',
        help='Enter the Signs and Symptoms for the patient in this evaluation.',
        states=STATES)
    procedures = fields.One2Many(
        'gnuhealth.directions', 'clinical_component', 'Procedures',
        help='Procedures / Actions to take',
        states=STATES)
    treatment_plan = fields.Text('Treatment Plan', states=STATES)

    def make_critical_info(self):
        out = []
        if self.signs_symptoms:
            out.extend([
                'Signs:',
                ';'.join([x.clinical.code for x in self.signs_symptoms])])
        if self.diagnosis:
            out.append(' - '.join([self.diagnosis.code, self.diagnosis.name]))
        if self.diagnostic_hypothesis:
            if self.diagnosis:
                out.append('or')
            else:
                out.append('DDx')
            out.append(';'.join([x.pathology.code
                                 for x in self.diagnostic_hypothesis]))
        if self.procedures:
            out.append('Procedures:')
            if len(self.procedures) <= 2:
                out.append(
                    '; '.join(['%s-%s' % (x.procedure.name,
                                          x.procedure.description)
                              for x in self.procedures])
                )
            else:
                out.append(';'.join(x.procedure.name for x in self.procedures))
        return ', '.join(out)

    def flip_one2many(self, title, o2mlist, fld, fld_name='name'):
        mylines = []
        if o2mlist:
            mylines.append(('%s:' % title, ))
            for p in o2mlist:
                pline = (' *', getattr(getattr(p, fld), fld_name))
                if getattr(p, 'comments', False):
                    pline += ('-', p.comments)
                mylines.append(pline)
            return mylines
        return None

    def get_report_info(self, name):
        lines = [('== Clinical ==',)]
        if self.signs_symptoms:
            lines.extend(
                self.flip_one2many('Signs And Symptoms:',
                                   self.signs_symptoms, 'clinical')
            )
        if self.notes:
            lines.extend([('Clinical Notes:', ),
                          ('\n'.join(filter(None, self.notes.split('\n'))), ),
                          DASHER])
        if self.diagnosis:
            lines.append(('Presumptive Diagnosis:', self.diagnosis.name))
        if self.treatment_plan:
            lines.extend([('Treatment Plan:', ),
                          ('\n'.join(filter(None,
                                            self.treatment_plan.split('\n'))), ),
                          DASHER])
        if self.procedures:
            lines.extend(
                self.flip_one2many('Procedures', self.procedures, 'procedure',
                                   'description')
            )

        if self.diagnostic_hypothesis:
            lines.extend(
                self.flip_one2many('Diagnostic Hypothesis',
                                   self.diagnostic_hypothesis, 'pathology')
            )

        if self.secondary_conditions:
            lines.extend(
                self.flip_one2many('Secondary Conditions found on the patient',
                                   self.secondary_conditions, 'pathology')
            )

        return '\n\n'.join([' '.join(x) for x in lines])


# Modification to GNU Health Default classes to point them here instead
class RewireEvaluationPointer(ModelSQL):
    clinical_component = fields.Many2One('gnuhealth.encounter.clinical',
                                         'Clinic', readonly=True)

    # @classmethod
    # def __setup__(cls):
    #     super(RewireEvaluationPointer, cls).__setup__()
    #     evaluation_field = getattr(cls, cls._evalutaion_field_name)
    #     evaluation_field.model_name = 'gnuhealth.encounter.clinical'


# PATIENT EVALUATION DIRECTIONS
class Directions(RewireEvaluationPointer, ModelView):
    'Patient Directions'
    __name__ = 'gnuhealth.directions'
    _evalutaion_field_name = 'name'


# SECONDARY CONDITIONS ASSOCIATED TO THE PATIENT IN THE EVALUATION
class SecondaryCondition(RewireEvaluationPointer, ModelView):
    'Secondary Conditions'
    __name__ = 'gnuhealth.secondary_condition'


# PATIENT EVALUATION OTHER DIAGNOSTIC HYPOTHESES
class DiagnosticHypothesis(RewireEvaluationPointer, ModelView):
    'Other Diagnostic Hypothesis'
    __name__ = 'gnuhealth.diagnostic_hypothesis'


# PATIENT EVALUATION CLINICAL FINDINGS (SIGNS AND SYMPTOMS)
class SignsAndSymptoms(RewireEvaluationPointer, ModelView):
    'Evaluation Signs and Symptoms'
    __name__ = 'gnuhealth.signs_and_symptoms'
