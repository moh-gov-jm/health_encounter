
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


def get_component_modelview(component_type_id, model_name=None):
        if component_type_id:
            # mvd = model view data
            mvd = EncounterComponentType.read(
                [int(component_type_id)], fields_names=['model', 'view_form'])
        elif model_name:
            mvd = EncounterComponentType.search_read(
                [('model', '=', model_name)],
                fields_names=['model', 'view_form'])
        else:
            mvd = []

        try:
            return (mvd[0]['model'], mvd[0]['view_form'])
        except IndexError:  # there is no component type for this model
            raise UnknownEncounterComponentType(model_name)

txtonly = re.compile('([A-Za-z]+)')
name_fix = lambda x: '_'.join([p.lower() for p in txtonly.findall(x)])


class ChooseComponentTypeView(ModelView):
    'Choose Component'
    __name__ = 'gnuhealth.encounter.component_chooser'
    component_type = fields.Selection('component_type_selection',
                                      'Component Type', required=True,
                                      sort=False)

    @classmethod
    def component_type_selection(cls):
        triple = EncounterComponentType.get_selection_list()
        return [(name_fix(x[2]), x[1]) for x in triple]


class ComponentStateView(StateView):
    '''use this StateView to get the boilerplate that sets up the
    appropriate instance of the component for creation or editing.'''
    def __init__(self, component_type_id=None, model_name=None):
        self.current_model_view = (
            'gnuhealth.encounter.component',
            'health_encounter.health_view_form_encounter_component')
        buttons = [
            Button('Si_gn', 'sign_x', 'health-certify', states={
                   'invisible': Bool(Eval('signed_by'))}),
            Button('Cancel', 'end', 'tryton-cancel',
                   states={'invisible': Bool(Eval('signed_by'))}),
            Button('_Save', 'save_x', 'tryton-save', default=True,
                   states={'invisible': Bool(Eval('signed_by'))}),
            Button('Close', 'close_x', 'tryton-close',
                   states={'invisible': Not(Bool(Eval('signed_by')))})
        ]

        # launch me with the combined model and associated view
        super(ComponentStateView, self).__init__(
            'gnuhealth.encounter.component',
            'health_encounter.health_view_form_encounter_component', buttons)

        if component_type_id or model_name:
            self.set_modelview(component_type_id, model_name)

    def get_defaults(self, wiz, state_name, fields):
        _real_comp_data = wiz._component_data.get('obj_data', False)
        if _real_comp_data:
            return _real_comp_data
        else:
            _real_comp = wiz._component_data['obj']
            return model2dict(_real_comp, fields)

    def _get_model(self):
        return self.current_model_view[0]

    def _set_model(self, val):
        # ignores the value this for the sake of the inherited __init__ call
        pass

    def _get_view_id(self):
        return self.current_model_view[1]

    def _set_view_id(self, val):
        # ignores the value this for the sake of the inherited __init__ call
        pass
    model_name = property(_get_model, _set_model)
    view = property(_get_view_id, _set_view_id)

    def set_modelview(self, type_id, model_name=None):
        tact = Transaction()
        print "Fetching model, transaction.context = %s" % repr(tact.context)
        self.current_model_view = get_component_modelview(type_id, model_name)


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

    @classmethod
    def __setup__(cls):
        super(EditComponentWizard, cls).__setup__()
        # fetch the component types and create a ComponentStateView for each
        component_types = [(x[0], name_fix(x[2]), x[3]) for x in
                           EncounterComponentType.get_selection_list()]

        cls._component_model_map = {}
        for type_id, type_name, type_model in component_types:
            setattr(cls, type_name, ComponentStateView(type_id))
            cls._component_model_map[type_model] = type_name

    def __init__(self, sessionid):
        super(EditComponentWizard, self).__init__(sessionid)
        tact = Transaction()
        active_model = tact.context.get('active_model')
        active_id = tact.context.get('active_id')

        self._component_data = {'model': active_model, 'active_id': active_id,
                                'obj_data': None, 'selected_component': None}
        real_component = None
        if active_model != 'gnuhealth.encounter':  # open button was clicked
            real_component = EncounterComponent.union_unshard(active_id)
            try:
                sc = self._component_model_map[real_component.__name__]
            except IndexError:
                raise UnknownEncounterComponentType(real_component.__name__)
                sc = None
            self._component_data['selected_component'] = sc
            self._component_data['obj'] = real_component
        elif getattr(self.selector, 'component_type', False):
            # maybe we came here via the add component and now we're saving huh
            self._component_data[
                'selected_component'] = self.selector.component_type

    def transition_start(self):
        if self._component_data['model'] == 'gnuhealth.encounter':
            return 'selector'
        else:
            return self._component_data['selected_component']

    def transition_selected(self):
        state_name = self.selector.component_type
        state = self.states[state_name]
        component_model = Pool().get(state.model_name)
        encounter_id = self._component_data['active_id']
        component_data = {'encounter': encounter_id}
        view = state.get_view()
        field_names = view['fields'].keys()
        if 'id' in field_names:
            del field_names[field_names.index['id']]
        component_data.update(component_model.default_get(field_names))
        real_component = component_model(**component_data)
        setattr(self, 'component', real_component)
        self._component_data.update(obj=real_component,
                                    obj_data=component_data,
                                    selected_component=state_name)
        return state_name

    def transition_sign_x(self):
        state_name = self._component_data['selected_component']
        state_model = getattr(self, state_name)
        pool = Pool()
        if not getattr(state_model, '_values', False):
            state_model._values = {}
        healthprof_model = pool.get('gnuhealth.healthprofessional')
        healthprof = healthprof_model.get_health_professional()
        state_model.signed_by = healthprof
        state_model.sign_time = datetime.now()
        return self.transition_save_x()

    def transition_save_x(self):
        model = self._component_data['model']
        component = None
        state_name = self._component_data['selected_component']
        if model != 'gnuhealth.encounter':
            compid = self._component_data['active_id']
            component = EncounterComponent.union_unshard(compid)
        state_model = getattr(self, state_name)
        state_model.pre_save()
        if component:
            component._values = state_model._values
            component.save()
        else:
            state_model.save()
        next_state = 'end'
        return next_state

    def transition_close_x(self):
        return 'end'
