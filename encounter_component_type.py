
from trytond.model import ModelView, ModelSQL, fields

__all__ = ['EncounterComponentType', 'UnknownEncounterComponentType']


class UnknownEncounterComponentType(Exception):
    pass


class EncounterComponentType(ModelSQL, ModelView):
    '''Encounter Component
    Stores encounter component type definitions. The Encounter models
    and views use this model to determine which components are available
    '''
    __name__ = 'gnuhealth.encounter.component_type'
    name = fields.Char('Type Name')
    code = fields.Char('Code', size=15,
                       help="Short name Displayed in the first column of the"
                       "encounter. Maximum 15 characters")
    model = fields.Char('Model name', help='e.g. gnuhealth.encounter.clinical',
                        required=True)
    view_form = fields.Char('View name', required=True,
                            help='full xml id of view, e.g. module.xml_id')
    ordering = fields.Integer('Display order')
    active = fields.Boolean('Active')

    @classmethod
    def __setup__(cls):
        super(EncounterComponentType, cls).__setup__()
        cls._order = [('ordering', 'ASC'), ('name', 'ASC')]

    @classmethod
    def register_type(cls, model_class, view):
        # first check if it was previously registered and deactivated
        registration = cls.search([('model', '=', model_class.__name__),
                                   ('view_form', '=', view)])
        if registration:
            registration = cls.browse(registration)
            if not registration.active:
                cls.write(registration, {'active': True})
        else:
            cdata = {'model': model_class.__name__, 'view_form': view}
            cdata['name'] = ''.join(filter(
                None,
                model_class.__doc__.split('\n'))[:1])
            cdata['code'] = cdata['name'][:15]

            # we need to create the registration
            cls.create([cdata])
        return True

    @classmethod
    def get_selection_list(cls):
        '''returns a list of active Encounter component types in a tuple
        of (id, Name, Code, model)'''
        try:
            return cls._component_type_list
        except AttributeError:
            pass
        ectypes = cls.search_read(
            [('active', '=', True)],
            fields_names=['id', 'name', 'code', 'model'],
            order=[('ordering', 'ASC'), ('name', 'ASC')])
        cls._component_type_list = [(x['id'], x['name'], x['code'], x['model'])
                                    for x in ectypes]
        return cls._component_type_list

    @classmethod
    def get_view_name(cls, ids):
        '''returns the name of the view used to edit/display a
        component type'''
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        # ids = map(int, ids)
        forms = cls.read(ids, fields_names=['view_form'])
        if forms:
            return forms[0]['view_form']
        return None
