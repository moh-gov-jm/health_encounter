from trytond.wizard import Wizard
from trytond.transaction import Transaction
from trytond.pool import Pool


class OneEncounterWizard(Wizard):
    '''
    Base class for wizards that start from the encounter form_action
    '''
    def __init__(self, sessionid):
        super(OneEncounterWizard, self).__init__(sessionid)
        tact = Transaction()
        active_id = tact.context.get('active_id')
        try:
            encounter = Pool().get(
                'gnuhealth.encounter').browse([active_id])[0]
        except:
            encounter = None
            self.raise_user_error('no_record_selected')
        self._enctr_data = {'active_id': active_id, 'obj': encounter}

    @classmethod
    def __setup__(cls):
        super(OneEncounterWizard, cls).__setup__()
        cls._error_messages.update({
            'no_record_selected': 'You need to select an Encounter',
        })

    def _get_active_encounter(self):
        '''
        returns the tuple (encounter_id, encounter) for the active
        object
        '''
        return (self._enctr_data['active_id'], self._enctr_data['obj'])
