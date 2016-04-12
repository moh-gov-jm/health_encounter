from trytond.model import ModelSQL, ModelView, fields
from .base import BaseComponent, SIGNED_STATES as STATES

DASHER = ('-' * 15, )  # minimal text based spacer line


def flip_one2many(title, o2mlist, fld, fld_name='rec_name'):
    mylines = []
    if o2mlist:
        if title:
            mylines.append((u'%s:' % title, ))
        for p in o2mlist:
            pline = (u'   *', getattr(getattr(p, fld), fld_name))
            if getattr(p, 'comments', False):
                pline += (u'-', p.comments)
            mylines.append(pline)
        return mylines
    return None


class EncounterClinical(BaseComponent):
    'Clinical'
    __name__ = 'gnuhealth.encounter.clinical'

    diagnosis = fields.Many2One(
        'gnuhealth.pathology', 'Main Condition',
        help='Presumptive Diagnosis. If no diagnosis can be made'
        ', encode the main sign or symptom.',
        states=STATES)

    secondary_conditions = fields.One2Many(
        'gnuhealth.secondary_condition',
        'clinical_component', 'Secondary Conditions',
        help='Other diseases treated in this encounter',
        states=STATES)

    diagnostic_hypothesis = fields.One2Many(
        'gnuhealth.diagnostic_hypothesis',
        'clinical_component', 'Hypotheses / DDx',
        help='Other Diagnostic Hypotheses / Differential Diagnosis (DDx)',
        states=STATES)

    signs_symptoms = fields.One2Many(
        'gnuhealth.signs_and_symptoms',
        'clinical_component', 'Signs and Symptoms',
        help='Signs and Symptoms for the patient in this encounter.',
        states=STATES)
    treatment_plan = fields.Text('Treatment Plan', states=STATES)

    @classmethod
    def __setup__(cls):
        super(EncounterClinical, cls).__setup__()
        cls.notes.help = 'Clinical history and examination findings'

    def make_critical_info(self):
        out = []
        if self.signs_symptoms:
            citxt = ', '.join([x.clinical.code for x in self.signs_symptoms])
            if citxt:
                out.append(u'Signs: %s' % citxt)
        if self.diagnosis:
            out.append(self.diagnosis.rec_name)
        if self.diagnostic_hypothesis:
            citxt = u', '.join([x.pathology.code
                                for x in self.diagnostic_hypothesis])
            if citxt and self.diagnosis:
                out.append(u'or %s' % citxt)
            else:
                out.append(u'DDx: %s' % citxt)
        return '; '.join(out)

    def get_report_info(self, name):
        lines = [(u'== Clinical ==',)]
        if self.signs_symptoms:
            lines.extend(
                flip_one2many(u'Signs And Symptoms',
                              self.signs_symptoms, 'clinical')
            )
        if self.notes:
            lines.extend([(u'Clinical Notes:', ),
                          (u'\n'.join(filter(None, self.notes.split('\n'))), ),
                          DASHER])
        if self.diagnosis:
            lines.append((u'Presumptive Diagnosis:', self.diagnosis.rec_name))
        if self.secondary_conditions:
            lines.extend(
                flip_one2many(u'Secondary Conditions found on the patient',
                              self.secondary_conditions, 'pathology')
            )

        if self.diagnostic_hypothesis:
            lines.extend(
                flip_one2many(u'Diagnostic Hypothesis',
                              self.diagnostic_hypothesis, 'pathology')
            )
        if self.treatment_plan:
            lines.extend([(u'Treatment Plan:', ),
                          (u'\n'.join(
                           filter(None, self.treatment_plan.split('\n'))), ),
                          DASHER])

        return u'\n'.join([u' '.join(x) for x in lines])


# Modification to GNU Health Default classes to point them here instead
class RewireEvaluationPointer(ModelSQL):
    clinical_component = fields.Many2One('gnuhealth.encounter.clinical',
                                         'Clinic', readonly=True)

    # @classmethod
    # def __setup__(cls):
    #     super(RewireEvaluationPointer, cls).__setup__()
    #     evaluation_field = getattr(cls, cls._evalutaion_field_name)
    #     evaluation_field.model_name = 'gnuhealth.encounter.clinical'


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


# Procedures, often done by a nurse or other. Separated for clarity, 2015-11-24
class EncounterProcedures(BaseComponent):
    'Procedures'
    __name__ = 'gnuhealth.encounter.procedures'
    procedures = fields.One2Many(
        'gnuhealth.directions', 'encounter_component', 'Procedures',
        help='Procedures / Actions to take',
        states=STATES)

    def get_report_info(self, name):
        lines = [(u'== Procedures ==',)]
        if self.procedures:
            lines.extend(
                flip_one2many(False, self.procedures, 'procedure')
            )
        if self.notes:
            lines.append((str(self.notes), ))
        return u'\n'.join([' '.join(x) for x in lines])

    def make_critical_info(self):
        if self.procedures:
            if len(self.procedures) <= 2:
                out = [x.procedure.rec_name for x in self.procedures]
            else:
                out = [x.procedure.name for x in self.procedures]
        else:
            out = []
        return u', '.join(out)


# PATIENT EVALUATION DIRECTIONS
class Directions(ModelSQL, ModelView):
    'Patient Procedures'
    __name__ = 'gnuhealth.directions'

    encounter_component = fields.Many2One('gnuhealth.encounter.procedures',
                                          'Component', readonly=True)
