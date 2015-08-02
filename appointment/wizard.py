# from trytond.model import ModelView, fields
from trytond.wizard import (Wizard, StateAction)
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.pyson import PYSONEncoder


class OneAppointmentWizard(Wizard):

    def __init__(self, sessionid):
        super(OneAppointmentWizard, self).__init__(sessionid)
        tact = Transaction()
        active_id = tact.context.get('active_id')
        try:
            appointment = Pool().get(
                'gnuhealth.appointment').browse([active_id])[0]
        except:
            self.raise_user_error('no_record_selected')
        self._appt_data = {'active_id': active_id, 'obj': appointment}

    @classmethod
    def __setup__(cls):
        super(OneAppointmentWizard, cls).__setup__()
        cls._error_messages.update({
            'no_record_selected': 'You need to select an Appointment record',
        })


class CreateAppointmentEncounter(OneAppointmentWizard):
    'Create Appointment Encounter'
    __name__ = 'gnuhealth.appointment.encounter_wizard'

    start_state = 'goto_encounter'
    goto_encounter = StateAction('health_encounter.actwin_appt_encounter')

    def do_goto_encounter(self, action):

        pool = Pool()
        appt_id = Transaction().context.get('active_id')

        try:
            appointment = pool.get(
                'gnuhealth.appointment').browse([appt_id])[0]
        except:
            self.raise_user_error('no_record_selected')

        patient = appointment.patient.id
        # TODO: Check appointment.service and add relevant form to encounter?
        # Does the encounter already exist?
        encounter = pool.get('gnuhealth.encounter').search([
            ('appointment', '=', appointment.id)])
        if encounter:
            rd = {'active_id': encounter[0].id}
            action['res_id'] = rd['active_id']
        else:
            institution = appointment.institution.id
            rd = {}

            action['pyson_domain'] = PYSONEncoder().encode([
                ('appointment', '=', appt_id),
                ('patient', '=', patient),
                ('institution', '=', institution),
            ])
            action['pyson_context'] = PYSONEncoder().encode({
                'appointment': appt_id,
                'patient': patient,
                'institution': institution
            })

        return action, rd
