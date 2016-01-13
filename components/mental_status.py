from trytond.model import fields
from .base import BaseComponent, SIGNED_STATES as STATES

DASHER = ('-' * 15, )  # minimal text based spacer line
LOC = {  # Level of Consciousness - Used to calculate Glasgow score
    'eyes': [
        ('4', 'Opens eyes spontaneously'),
        ('3', 'Opens eyes in response to voice'),
        ('2', 'Opens eyes in response to painful stimuli'),
        ('1', 'Does not Open Eyes')],
    'verbal': [
        ('5', 'Oriented, converses normally'),
        ('4', 'Confused, disoriented'),
        ('3', 'Utters inappropriate words'),
        ('2', 'Incomprehensible sounds'),
        ('1', 'Makes no sounds')],
    'motor': [
        ('6', 'Obeys commands'),
        ('5', 'Localizes painful stimuli'),
        ('4', 'Flexion / Withdrawal to painful stimuli'),
        ('3', 'Abnormal flexion to painful stimuli (decorticate response)'),
        ('2', 'Extension to painful stimuli - decerebrate response -'),
        ('1', 'Makes no movement')]
}
MOODS = [(None, ''), ('n', 'Normal'), ('s', 'Sad'), ('f', 'Fear'),
         ('r', 'Rage'), ('h', 'Happy'), ('d', 'Disgust'), ('e', 'Euphoria'),
         ('fl', 'Flat')]


def get_val(select_list, key, default=None):
    return dict(select_list).get(str(key), default)


class EncounterMentalStatus(BaseComponent):
    'Mental Status'
    __name__ = 'gnuhealth.encounter.mental_status'
    loc = fields.Integer(
        'Glasgow',
        help='Level of Consciousness - on Glasgow Coma Scale :  < 9 severe -'
        ' 9-12 Moderate, > 13 minor',
        states=STATES)
    loc_eyes = fields.Selection(LOC['eyes'], 'Glasgow - Eyes', sort=False,
                                states=STATES)
    loc_verbal = fields.Selection(LOC['verbal'], 'Glasgow - Verbal',
                                  sort=False, states=STATES)
    loc_motor = fields.Selection(LOC['motor'], 'Glasgow - Motor', sort=False,
                                 states=STATES)

    tremor = fields.Boolean(
        'Tremor',
        help='If associated  to a disease, please encode it on the patient'
        ' disease history',
        states=STATES)

    violent = fields.Boolean(
        'Violent Behaviour',
        help='Check this box if the patient is aggressive or violent at the'
        ' moment',
        states=STATES)

    mood = fields.Selection(MOODS, 'Mood', sort=False, states=STATES)

    orientation = fields.Boolean(
        'Disoriented',
        help='Check this box if the patient is disoriented in time and/or'
        ' space',
        states=STATES)

    memory = fields.Boolean(
        'Memory Problems',
        help='Check this box if the patient has problems in short or long'
        ' term memory',
        states=STATES)

    knowledge_current_events = fields.Boolean(
        'Knowledge of Current Events',
        help='Check this box if the patient can not respond to public'
        ' notorious events',
        states=STATES)

    judgement = fields.Boolean(
        'Judgement off',
        help='Check this box if the patient can not interpret basic scenario'
        ' solutions',
        states=STATES)

    abstraction = fields.Boolean(
        'Abstract Reasoning Difficult',
        help='Check this box if the patient presents abnormalities in'
        ' abstract reasoning',
        states=STATES)

    vocabulary = fields.Boolean(
        'Vocabulary',
        help='Check this box if the patient lacks basic intellectual capacity,'
        ' when she/he can not describe elementary objects',
        states=STATES)

    calculation_ability = fields.Boolean(
        'Calculation Inbility',
        help='Check this box if the patient can not do simple arithmetic'
        ' problems',
        states=STATES)

    object_recognition = fields.Boolean(
        'Object Recognition',
        help='Check this box if the patient suffers from any sort of gnosia'
        ' disorders, such as agnosia, prosopagnosia ...',
        states=STATES)

    praxis = fields.Boolean(
        'Praxis',
        help='Check this box if the patient is unable to make voluntary'
        'movements',
        states=STATES)

    @staticmethod
    def default_loc_eyes():
        return '4'

    @staticmethod
    def default_loc_verbal():
        return '5'

    @staticmethod
    def default_loc_motor():
        return '6'

    @staticmethod
    def default_loc():
        return 15

    @fields.depends('loc_verbal', 'loc_motor', 'loc_eyes')
    def on_change_with_loc(self):
        # if self.loc_motor and self.loc_eyes and self.loc_verbal:
        return int(self.loc_motor) + int(self.loc_eyes) + int(self.loc_verbal)

    def make_critical_info(self):
        '''returns that single line summary of the component data'''
        out = [u'Glasgow:', unicode(self.loc)]
        if self.violent:
            out.insert(0, u'Violent;')
        if self.praxis:
            out.append(u'Praxis')
        return u' '.join(out)

    def get_report_info(self, name):
        lines = [(u'== Mental Status ==',)]
        if self.violent:
            lines.append((u'Violent:', u'YES'))
        lines.append((
            u'Glasgow scale:', str(self.loc),
            u' = %s(%s) + %s(%s) + %s(%s)' % (
                get_val(LOC['eyes'], self.loc_eyes), self.loc_eyes,
                get_val(LOC['verbal'], self.loc_verbal), self.loc_verbal,
                get_val(LOC['motor'], self.loc_motor), self.loc_motor)
        ))
        if self.mood:
            lines.append((u'Mood:', get_val(MOODS, self.mood)))
        checks = [('orientation', u'Disoriented'),
                  ('memory', u'Has memory problems'),
                  ('knowledge_current_events',
                   u'Little or no knowledge of current events'),
                  ('judgement', u'Cannot interpret basic scenarios'),
                  ('abstraction', u'Abnormalities in abstract reasoning'),
                  ('vocabulary', u'Lacks basic intellectual capacity'),
                  ('calculation_ability', u'Cannot do simple math'),
                  ('object_recognition', u'Object recognition problems'),
                  ('praxis', u'Unable to make voultary movements')]
        notestext = str(self.notes)
        if notestext:
            lines.append((u'=== Notes ===',))
            lines.append((notestext,))
        for k, val in checks:
            if getattr(self, k):
                lines.append((val,))
        return u'\n'.join([u' '.join(x) for x in lines])
