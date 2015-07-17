
import re
from trytond.wizard import (Wizard, StateView, Button, StateTransition)
from trytond.pool import Pool
from trytond.model import ModelView, fields
from trytond.transaction import Transaction
from trytond.pyson import Eval, Bool, Not
from .base import EncounterComponent
from ..encounter_component_type import (EncounterComponentType,
                                        UnknownEncounterComponentType)
from datetime import datetime


def model2dict(record, fields=None, with_one2many=True):
    '''rudimentary utility that copies fields from a record into a dict'''
    out = {}
    if fields is None:
        pass  # ToDo: Process record._fields to get a sensible list
    field_names = fields[:]
    if 'id' not in field_names:
        field_names.insert(0, 'id')

    for field_name in field_names:
        field = record._fields[field_name]
        value = getattr(record, field_name, None)
        if field._type in ('many2one', 'reference'):
            if value:
                out[field_name] = value.id
            else:
                out[field_name] = value
        elif field._type in ('one2many',):
            if with_one2many and value:
                out[field_name] = [x.id for x in value]
            elif with_one2many:
                out[field_name] = []
        else:
            out[field_name] = value
    return out


class ChooseComponentTypeView(ModelView):
    'Choose Component'
    __name__ = 'gnuhealth.encounter.component_chooser'
    component_type = fields.Selection('component_type_selection',
                                      'Component Type', required=True)

    @classmethod
    def component_type_selection(cls):
        triple = EncounterComponentType.get_selection_list()
        return [x[:2] for x in triple]


class ComponentStateView(StateView):
    '''use this StateView to get the boilerplate that sets up the
    appropriate instance of the component for creation or editing.'''
    def __init__(self, model_name, view_id):
        buttons = [
            Button('Cancel', 'end', 'tryton-cancel',
                   states={'invisible': Bool(Eval('signed_by'))}),
            Button('Save', 'save_x', 'tryton-save', default=True,
                   states={'invisible': Bool(Eval('signed_by'))}),
            Button('Sign', 'sign_x', 'health-certify', states={
                   'invisible': Bool(Eval('signed_by'))}),
            Button('Close', 'close_x', 'tryton-close',
                   states={'invisible': Not(Bool(Eval('signed_by')))})
        ]
        super(ComponentStateView, self).__init__(model_name, view_id, buttons)

    def get_defaults(self, wiz, state_name, fields):
        _real_comp = wiz._component_data['obj']
        return model2dict(_real_comp, fields)


class CStateView(ComponentStateView):  # initialise a StateView from DB
    def __init__(self, component_type_id):
        mvd = EncounterComponentType.read([int(component_type_id)],
                                          fields_names=['model', 'view_form'])
        super(CStateView, self).__init__(mvd[0]['model'], mvd[0]['view_form'])


class EditComponentWizard(Wizard):
    'Edit Component'
    __name__ = 'gnuhealth.encounter.component_editor.wizard'
    start = StateTransition()
    selector = StateView(
        'gnuhealth.encounter.component_chooser',
        'health_encounter.health_form_component_chooser', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Next', 'selected', 'tryton-ok', default=True)
        ]
    )
    selected = StateTransition()
    save_x = StateTransition()
    sign_x = StateTransition()
    close_x = StateTransition()
    _component_data = {}

    def __init__(self, sessionid):
        tact = Transaction()
        active_model = tact.context.get('active_model')
        active_id = tact.context.get('active_id')
        txtonly = re.compile('([A-Za-z]+)')
        fix = lambda x: '_'.join([p.lower() for p in txtonly.findall(x)])
        component_types = dict([(x[0], fix(x[2])) for x in
                                EncounterComponentType.get_selection_list()])

        self._component_data = {'model': active_model, 'active_id': active_id,
                                'typenames': component_types}
        real_component = None
        if active_model != 'gnuhealth.encounter':
            real_component = EncounterComponent.union_unshard(active_id)
            self._make_component_state_view(False, real_component.__name__)
            self._component_data['obj'] = real_component
        super(EditComponentWizard, self).__init__(sessionid)
        # setattr(self, statename, real_component)

    def _make_component_state_view(self, component_type_id, model_name=None):
        component_view = None

        if not component_type_id and model_name:
            cvm = EncounterComponentType.search([('model', '=', model_name)])
            try:
                component_type_id = cvm[0]
            except IndexError:  # there is no component type for this model
                raise UnknownEncounterComponentType(model_name)

        # if 'component' not in self.states:
        component_view = CStateView(component_type_id)
        self.states['component'] = component_view
        return 'component'

    def transition_start(self):
        if self._component_data['model'] == 'gnuhealth.encounter':
            return 'selector'
        else:
            return 'component'

    def transition_selected(self):
        statename = self._make_component_state_view(
            self.selector.component_type)
        state = self.states[statename]
        ComponentModel = Pool().get(state.model_name)
        encounter_id = self._component_data['active_id']
        component_data = {'encounter': encounter_id}
        view = state.get_view()
        field_names = view['fields'].keys()
        if 'id' in field_names:
            del field_names[field_names.index['id']]
        component_data.update(ComponentModel.default_get(field_names))

        real_component = ComponentModel(**component_data)
        setattr(self, statename, real_component)
        self._component_data.update(obj=real_component)
        return statename

    def transition_sign_x(self):
        state_name = 'component'
        state_model = getattr(self, state_name)
        pool = Pool()
        if not getattr(state_model, '_values', False):
            state_model._values = {}
        HealthProf = pool.get('gnuhealth.healthprofessional')
        healthprof = HealthProf.get_health_professional()
        state_model.signed_by = healthprof
        state_model.sign_time = datetime.now()
        return self.transition_save_x()

    def transition_save_x(self):
        model = self._component_data['model']
        component = None
        state_name = 'component'
        if model != 'gnuhealth.encounter':
            compid = self._component_data['active_id']
            component = EncounterComponent.union_unshard(compid)
        state_model = getattr(self, state_name)
        state_model.critical_info = state_model.make_critical_info()
        if component:
            component._values = state_model._values
            component.save()
        else:
            state_model.save()
        next_state = 'end'
        return next_state

    def transition_close_x(self):
        return 'end'
