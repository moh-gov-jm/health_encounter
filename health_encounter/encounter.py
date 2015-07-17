
from datetime import datetime
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, Not, Equal, Or, Greater, In
from trytond.modules.health import HealthInstitution, HealthProfessional
from trytond.modules.health_jamaica import tryton_utils as utils


class PatientEncounter(ModelSQL, ModelView):
    'Patient Encounter'
    __name__ = 'gnuhealth.encounter'

    STATES = {'readonly': Or(Equal(Eval('state'), 'signed'),
                             Equal(Eval('state'), 'done'),
                             Equal(Eval('state'), 'invalid'))}
    SIGNED_STATES = {'readonly': Equal(Eval('state'), 'signed')}
    SIGNED_VISIBLE = {'invisible': Not(Equal(Eval('state'), 'signed'))}

    state = fields.Selection(
        [('in_progress', 'In progress'),
         ('done', 'Done'),
         ('signed', 'Signed'),
         ('invalid', 'Invalid')],
        'State', readonly=True, sort=False)
    patient = fields.Many2One('gnuhealth.patient', 'Patient', required=True,
                              states=STATES)
    primary_complaint = fields.Char('Primary complaint', states=STATES)
    start_time = fields.DateTime('Start', required=True, states=STATES)
    end_time = fields.DateTime('End', states=STATES)
    institution = fields.Many2One('gnuhealth.institution', 'Institution',
                                  required=True)
    appointment = fields.Many2One(
        'gnuhealth.appointment', 'Appointment',
        domain=[('patient', '=', Eval('patient'))], depends=['patient'],
        help='Enter or select the appointment related to this encounter',
        states=STATES)
    next_appointment = fields.Many2One(
        'gnuhealth.appointment', 'Next Appointment',
        domain=['OR', ['AND', ('patient', '=', Eval('patient')),
                       ('state', '=', 'confirmed')], ('state', '=', 'free')],
        depends=['patient'],
        states=SIGNED_STATES)
    signed_by = fields.Many2One(
        'gnuhealth.healthprofessional', 'Signed By', readonly=True,
        states=SIGNED_VISIBLE,
        help="Health Professional that finished the patient evaluation")
    sign_time = fields.DateTime('Sign time', readonly=True,
                                states=SIGNED_VISIBLE)
    components = fields.One2Many('gnuhealth.encounter.component', 'encounter',
                                 'Components')
    summary = fields.Function(fields.Text('Summary'), 'get_encounter_summary')
    # Patient identifier fields
    upi = fields.Function(fields.Char('UPI'), 'get_person_patient_field')
    medical_record_num = fields.Function(
        fields.Char('Medical Record Number'),
        'get_person_patient_field')
    sex_display = fields.Function(fields.Char('Sex'),
                                  'get_person_patient_field')
    age = fields.Function(fields.Char('Age'), 'get_person_patient_field')
    crypto_enabled = fields.Function(fields.Boolean('Crypto Enabled'),
                                     'get_crypto_enabled')

    @classmethod
    def __setup__(cls):
        super(PatientEncounter, cls).__setup__()
        cls._error_messages.update({
            'health_professional_warning': 'No health professional '
            'associated with this user',
            'end_date_before_start': 'End time "%(end_time)s" BEFORE'
            ' start time "%(start_time)s"',
            'end_date_required': 'End time is required for finishing',
            'unsigned_components': 'There are unsigned components.'
                                   # 'This encounter cannot be signed'
        })

        cls._buttons.update({
            'set_done': {'invisible': Not(Equal(Eval('state'), 'in_progress'))},
            'sign_finish': {'invisible': Not(Equal(Eval('state'), 'done'))},
            'add_component': {'readonly': Or(Greater(0, Eval('id', -1)),
                                             In(Eval('state'),
                                                ['done', 'signed', 'invalid'])),
                              'invisible': Equal(Eval('state'), 'signed')}
        })

    @classmethod
    @ModelView.button
    def sign_finish(cls, encounters):
        signing_hp = HealthProfessional().get_health_professional()
        if not signing_hp:
            cls.raise_user_error('health_professional_warning')
        #ToDO: set all the not-done components to DONE as well and sign
        # the unsigned ones

        cls.write(encounters, {
            'state': 'signed',
            'signed_by': signing_hp,
            'sign_time': datetime.now()
        })

    @classmethod
    @ModelView.button
    def set_done(cls, encounters):
        # Change the state of the evaluation to "Done"
        save_data = {'state': 'done'}
        for encounter in encounters:
            if not encounter.end_time:
                cls.raise_user_error('end_date_required')
            for comp in encounter.components:
                if not comp.signed_by:
                    cls.raise_user_error('unsigned_components')
            #     save_data.update(end_time=encounter.end_time)
            #     break
            # else:

        cls.write(encounters, save_data)

    @classmethod
    @ModelView.button_action(
        'health_encounter.health_wizard_encounter_edit_component')
    def add_component(cls, components, *a, **k):
        hp = HealthProfessional.get_health_professional()
        if not hp:
            cls.raise_user_error('health_professional_warning')

    @staticmethod
    def default_start_time():
        return datetime.now()

    @staticmethod
    def default_institution():
        return HealthInstitution().get_institution()

    @staticmethod
    def default_state():
        return 'in_progress'

    def get_crypto_enabled(self, name):
        return False

    def get_rec_name(self, name):
        localstart = utils.localtime(self.start_time)
        line = ['EV%05d' % self.id, self.patient.name.name,
                '(%s /MRN:%s)' % (self.upi, self.medical_record_num),
                self.sex_display, self.age, 'on %s' % localstart.ctime()]
        return ' '.join(line)

    def get_person_patient_field(self, name):
        if name in ['upi', 'sex_display', 'medical_record_num']:
            return getattr(self.patient.name, name)
        if name in ['age']:
            return getattr(self.patient, name)
        return ''

    def get_encounter_summary(self, name):
        summary_texts = []
        for component in self.components:
            real_component = component.union_unshard(component.id)
            summary_texts.append(real_component.report_info)
        return '\n\n'.join(summary_texts)
