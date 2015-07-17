from datetime import datetime
from trytond.model import ModelView, ModelSQL, fields, UnionMixin
from trytond.pyson import Eval, Bool, Not
from trytond.pool import Pool
from trytond.modules.health_jamaica import tryton_utils as utils
from ..encounter_component_type import EncounterComponentType


SIGNED_STATES = {'readonly': Bool(Eval('signed_by'))}
SIGNED_VISIBLE = {'invisible': Not(Bool(Eval('signed_by')))}


class BaseComponent(ModelSQL, ModelView):
    '''All components should inherit from this class. It's not a real
    model as it is not registered in the pool. It defines the fields
    needed for a model to be a valid component. '''
    encounter = fields.Many2One('gnuhealth.encounter', 'Encounter',
                                readonly=True, required=True)
    start_time = fields.DateTime('Start', required=True, states=SIGNED_STATES)
    end_time = fields.DateTime('Finish', states=SIGNED_STATES)
    sign_time = fields.DateTime('Signed', readonly=True, states=SIGNED_VISIBLE)
    signed_by = fields.Many2One('gnuhealth.healthprofessional', 'Signed by',
                                readonly=True, states=SIGNED_VISIBLE)
    performed_by = fields.Many2One('gnuhealth.healthprofessional', 'Clinician',
                                   states=SIGNED_STATES)
    warning = fields.Boolean(
        'Warning',
        help="Check this box to alert the supervisor about this session."
        " It will be shown in red in the encounter",
        states=SIGNED_STATES)
    notes = fields.Text('Notes', states=SIGNED_STATES)
    critical_info = fields.Char('Summary', readonly=True,
                                depends=['notes'])
    report_info = fields.Function(fields.Text('Report'), 'get_report_info')
    is_union_comp = fields.Function(fields.Boolean('Unified component'),
                                    'get_is_union')

    @classmethod
    def __setup__(cls):
        super(BaseComponent, cls).__setup__()
        cls._order = [('start_time', 'ASC')]
        cls._order_name = 'start_time'
        cls.critical_info.depends = cls.get_critical_info_fields()

    @staticmethod
    def default_performed_by():
        HealthProfessional = Pool().get('gnuhealth.healthprofessional')
        return HealthProfessional.get_health_professional()

    @classmethod
    def get_critical_info_fields(cls):
        '''
        return the list of field names that are used to calculate
        the critical_info summary field
        '''
        return ['notes']

    def make_critical_info(self):
        # return a single line, no more than 140 chars to describe the details
        # of what's happening in the measurements in this component
        return ""

    def get_report_info(self, name):
        # return details of the data contained in this component as plain text
        # no length limit
        return ""

    def get_is_union(self, name):
        return False

    @classmethod
    def pre_sign(cls, components):
        '''sets the healthprof and the sign_time for the current instance'''
        health_prof_model = Pool().get('gnuhealth.healthprofessional')
        signtime = datetime.now()
        for comp in components:
            comp.signed_by = health_prof_model.get_health_professional()
            comp.sign_time = signtime

    def on_change_with_critical_info(self, *arg, **kwarg):
        return self.make_critical_info()

    @staticmethod
    def default_start_time():
        return datetime.now()

    @classmethod
    @ModelView.button
    def mark_done(cls, components):
        pass
        # save the component and set the state to done

    # @classmethod
    # def view_header_get(cls, value, view_type=None):

    #     print '*'*70
    #     print 'Value = %s \n--------------\nview-type = %s' %(repr(value), repr(view_type))
    #     print 'Context = %s' % repr(Transaction().context)
    #     print '*'*70
    #     return super(BaseComponent, cls).view_header_get(value, view_type)


class EncounterComponent(UnionMixin, BaseComponent):
    '''Component
    The unionized encounter component. This is the model to which the
    encounter points its One2Many field. '''
    __name__ = 'gnuhealth.encounter.component'
    component_type = fields.Function(fields.Char('Type'),
                                     'get_component_type_name')
    start_time_time = fields.Function(fields.Time('Start'),
                                      'get_start_time_time')

    @classmethod
    def __setup__(cls):
        super(EncounterComponent, cls).__setup__()

        if hasattr(cls, '_buttons'):
            pass
        else:
            cls._buttons = {}

        cls._buttons['btn_open'] = {'readonly': Eval(False)}

    @classmethod
    def __register__(cls, module_name):
        # TableHandler = backend.get('TableHandler')
        super(ModelSQL, cls).__register__(module_name)
        return

    @staticmethod
    def union_models():
        thelist = EncounterComponentType.get_selection_list()
        return [x[3] for x in thelist]

    def get_start_time_time(self, name):
        # return self.start_time.strftime('%H:%M')
        return utils.localtime(self.start_time).time()

    def get_component_type_name(self, name):
        id_names = EncounterComponentType.get_selection_list()
        title_index = self.id % len(id_names)
        return id_names[title_index][2]

    def get_report_info(self, name):
        real_component = self.union_unshard(self.id)
        return real_component.get_report_info(name)

    def get_is_union(self, name):
        return True

    @classmethod
    @ModelView.button_action(
        'health_encounter.health_wizard_encounter_edit_component')
    def btn_open(cls, components, *a, **k):
        pass
