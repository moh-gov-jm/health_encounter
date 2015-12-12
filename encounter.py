
from datetime import datetime
from trytond.pool import Pool
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, Not, Equal, Or, Greater, In, Len
from trytond.modules.health import HealthInstitution, HealthProfessional
from . import utils


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
        'State', readonly=True, sort=False,
        states={'invisible': Equal(Eval('state'), 'signed')})
    patient = fields.Many2One('gnuhealth.patient', 'Patient', required=True,
                              states=STATES)
    primary_complaint = fields.Char('Primary complaint', states=STATES)
    start_time = fields.DateTime('Start', required=True, states=STATES)
    end_time = fields.DateTime('End', states=STATES)
    institution = fields.Many2One('gnuhealth.institution', 'Institution',
                                  required=True, states=STATES)
    appointment = fields.Many2One(
        'gnuhealth.appointment', 'Appointment',
        domain=[('patient', '=', Eval('patient'))], depends=['patient'],
        help='Enter or select the appointment related to this encounter',
        states=STATES)
    next_appointment = fields.Many2One(
        'gnuhealth.appointment', 'Next Appointment',
        # domain=[('patient', '=', Eval('patient'))],
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
    upi = fields.Function(fields.Char('UPI'), 'get_upi_mrn')
    medical_record_num = fields.Function(
        fields.Char('Medical Record Number'), 'get_upi_mrn')
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
            'set_done': {'invisible': Not(Equal(Eval('state'), 'in_progress')),
                         'readonly': Or(Greater(0, Eval('id', -1)),
                                        Greater(1, Len(Eval('components'))))},
            'sign_finish': {'invisible': Not(Equal(Eval('state'), 'done'))},
            'add_component': {'readonly': Or(Greater(0, Eval('id', -1)),
                                             In(Eval('state'),
                                                ['done', 'signed', 'invalid'])),
                              'invisible': Equal(Eval('state'), 'signed')}
        })

    @classmethod
    def create(cls, vlist):
        '''
        update appointment, set state = processing when encounter is
        first saved
        '''
        retval = super(PatientEncounter, cls).create(vlist)
        Appointment = Pool().get('gnuhealth.appointment')
        appointments = []
        for encounter in vlist:
            if encounter['appointment'] and not encounter.get('end_time'):
                appointments.append(encounter['appointment'])
        appts = Appointment.browse(appointments)
        Appointment.write(appts, {'state': 'processing'})
        return retval

    @classmethod
    @ModelView.button
    def sign_finish(cls, encounters):
        signing_hp = HealthProfessional().get_health_professional()
        if not signing_hp:
            cls.raise_user_error('health_professional_warning')
        #ToDO: set all the not-done components to DONE as well and sign
        # the unsigned ones
        for encounter in encounters:
            for comp in encounter.components:
                if not comp.signed_by:
                    cls.raise_user_error('unsigned_components')

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
        appointments = []  # appointments to be set to done
        for encounter in encounters:
            if not encounter.end_time:
                cls.raise_user_error('end_date_required')
            #     save_data.update(end_time=encounter.end_time)
            #     break
            # else:
            if encounter.appointment:
                appointments.append(encounter.appointment)

        cls.write(encounters, save_data)
        Appointment = Pool().get('gnuhealth.appointment')
        Appointment.write(appointments, {'state': 'done'})

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
        if name in ['sex_display']:
            sex = getattr(self.patient.name, name,
                          getattr(self.patient.name, 'sex', '?'))
            return len(sex) == 1 and sex.upper() or sex
        if name in ['age']:
            return getattr(self.patient, name)
        return ''

    def get_upi_mrn(self, name):
        if name == 'upi':
            return self.patient.get_patient_puid('puid')
        elif name == 'medical_record_num':
            return getattr(self.patient, 'medical_record_num', '')
        return ''

    def get_encounter_summary(self, name):
        summary_texts = []
        for component in self.components:
            real_component = component.union_unshard(component.id)
            summary_texts.append(real_component.report_info)
        return '\n\n'.join(summary_texts)

    def real_component(self, name=None):
        '''retuns the real component objects.
        Always returns a list of objects.
        If name not provided returns all real components
        name can be the name of the model or the shortname displayed
        on screen case insensitive.
        '''
        comps = [(x.component_type, x.union_unshard(x.id))
                 for x in self.components]
        typedict = {}
        real_comps = []
        # modeldict = {}
        for i, (comptype, comp) in enumerate(comps):
            typedict.setdefault(comptype.lower(), []).append(i)
            # modeldict # ToDo: Figure out how to get at the model
            # name from an instance
            real_comps.append(comp)
        if name:
            return [real_comps[i] for i in typedict.get(name, [])]
        else:
            return real_comps
