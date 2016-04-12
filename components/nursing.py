# -*- coding: utf-8 -*-

from trytond.model import fields
from .base import BaseComponent, SIGNED_STATES


METRIC_CONV = {
    'length': (1 / 2.54),
    'weight': 2.20462262
}


URI_COMBOS = {
    'default': ('normal', 'trace', '+', '++', '+++', '++++'),
    'nitrite': ('normal', 'trace', 'small', 'moderate', 'large', 'large+')
}


class EncounterAnthro(BaseComponent):
    'Anthropometry'
    __name__ = 'gnuhealth.encounter.anthropometry'

    weight = fields.Float('Weight', help='Weight in Kilos',
                          states=SIGNED_STATES)
    height = fields.Float('Height', help='Height in centimeters, eg 175',
                          states=SIGNED_STATES)

    bmi = fields.Float(
        'Body Mass Index',
        readonly=True,
        states=SIGNED_STATES)

    head_circumference = fields.Float(
        'Head Circumference',
        help='Head circumference',
        states=SIGNED_STATES)

    abdominal_circ = fields.Float('Waist', states=SIGNED_STATES)
    hip = fields.Float('Hip', help='Hip circumference in centimeters, eg 100',
                       states=SIGNED_STATES)

    whr = fields.Float(
        'WHR', help='Waist to hip ratio', readonly=True,
        states=SIGNED_STATES)

    head_circumference = fields.Float(
        'Head Circumference',
        help='Head circumference',
        states=SIGNED_STATES)

    # calculate BMI
    @fields.depends('weight', 'height', 'bmi')
    def on_change_with_bmi(self):
        if self.height and self.weight:
            if (self.height > 0):
                return self.weight / ((self.height / 100) ** 2)
        return 0

    # Calculate WH ratio
    @fields.depends('abdominal_circ', 'hip', 'whr')
    def on_change_with_whr(self):
        waist = self.abdominal_circ
        hip = self.hip
        if (waist and hip > 0):
            whr = waist / hip
        else:
            whr = 0
        return whr

    @classmethod
    def get_critical_info_fields(cls):
        '''
        return the list of field names that are used to calculate
        the critical_info summary field
        '''
        return ['weight', 'height', 'hip', 'abdominal_circ']

    def make_critical_info(self):
        citxt = []
        if self.weight and self.height:
            citxt.extend([u'W: %5.2f' % self.weight, 'kg,',
                          u'H: %5.1f' % self.height, 'cm',
                          u'=', '(BMI) %5.2f' % self.bmi])
        else:
            if self.weight:
                citxt.append(u'Weight: %5.2f' % self.weight)
            if self.height:
                citxt.append(u'Height: %5.2f' % self.height)

        if self.abdominal_circ:
            citxt.append(u'Waist: %5.2fcm' % self.abdominal_circ)
        if self.hip:
            if self.abdominal_circ:
                citxt.append(u'x')
            citxt.append(u'Hip: %5.2fcm' % self.hip)
        if self.whr:
            citxt.append(u'= %5.2f' % self.whr)
        # return a single line, no more than 140 chars to describe the details
        # of what's happening in the measurements in this component
        return ' '.join(citxt)

    def get_report_info(self, name):
        lines = [(u'== Anthropometric Measurements ==',)]
        if self.height:
            lines.append(
                [u'* Height: %7.2fcm' % (self.height),
                 u'(%2.0fft %2.0fin)' %
                    divmod(self.height * METRIC_CONV['length'], 12)])
        if self.weight:
            lines.append(
                [u'* Weight: %7.2fkg' % (self.weight),
                 u'(%5.2flbs)' % (self.weight * METRIC_CONV['weight'])])
        if self.abdominal_circ:
            lines.append(
                [u'* Waist: %7.2f' % (self.abdominal_circ),
                 u'(%5.2fin)' % (self.abdominal_circ * METRIC_CONV['length'])])
        if self.hip:
            lines.append([u'* Hip: %7.2f' % (self.hip),
                          u'(%5.2fin)' % (self.hip * METRIC_CONV['length'])])
        if self.head_circumference:
            lines.append([u'* Head : %7.2f' % (self.head_circumference),
            u'(%5.2fin)' % (self.head_circumference * METRIC_CONV['length'])])

        if self.whr or self.bmi:
            lines.append(('',))
            if self.bmi:
                lines.append([u'* Body Mass Index: %7.2f' % (self.bmi)])
            if self.whr:
                lines.append([u'* Waist to Hip Ratio: %5.2f' % (self.whr)])
        if self.notes:
            lines.extend([(u'\n=== Notes ===',), (unicode(self.notes), )])
        return u'\n'.join([u' '.join(x) for x in lines])


class EncounterAmbulatory(BaseComponent):
    'Ambulatory'
    __name__ = 'gnuhealth.encounter.ambulatory'

    # Vital Signs
    systolic = fields.Integer('Systolic Pressure', states=SIGNED_STATES)
    diastolic = fields.Integer('Diastolic Pressure', states=SIGNED_STATES)
    bpm = fields.Integer(
        'Heart Rate',
        help='Heart rate expressed in beats per minute', states=SIGNED_STATES)
    respiratory_rate = fields.Integer(
        'Respiratory Rate',
        help='Respiratory rate expressed in breaths per minute',
        states=SIGNED_STATES)
    osat = fields.Integer(
        'Oxygen Saturation',
        help='Oxygen Saturation(arterial).', states=SIGNED_STATES)
    temperature = fields.Float(
        u'Temperature (°C)', digits=(4, 2),
        help='Temperature in degrees celsius', states=SIGNED_STATES)
    pregnant = fields.Boolean('Pregnant', states=SIGNED_STATES)
    lmp = fields.Date('Last Menstrual Period',
                      help='Date last menstrual period started')
    glucose = fields.Float(
        'Glucose (mmol/l)', digits=(5, 2),
        help='mmol/l. Reading from glucose meter', states=SIGNED_STATES)
    uri_ph = fields.Numeric('pH', digits=(1, 1), states=SIGNED_STATES)
    uri_specific_gravity = fields.Numeric('Specific Gravity',
                                          digits=(1, 3), states=SIGNED_STATES)
    uri_protein = fields.Selection(
        'uri_selection', 'Protein', states=SIGNED_STATES)
    uri_blood = fields.Selection(
        'uri_selection', 'Blood', states=SIGNED_STATES)
    uri_glucose = fields.Selection(
        'uri_selection', 'Glucose', states=SIGNED_STATES)
    uri_nitrite = fields.Selection(
        'uri_selection', 'Nitrite', states=SIGNED_STATES)
    uri_bilirubin = fields.Selection(
        'uri_selection', 'Bilirubin', states=SIGNED_STATES)
    uri_leuko = fields.Selection(
        'uri_selection', 'Leukocytes', states=SIGNED_STATES)
    uri_ketone = fields.Selection(
        'uri_selection', 'Ketone', states=SIGNED_STATES)
    uri_urobili = fields.Selection(
        'uri_selection', 'Urobilinogen', states=SIGNED_STATES)

    malnutrition = fields.Boolean(
        'Malnourished',
        help='Check this box if the patient show signs of malnutrition. If'
        ' associated  to a disease, please encode the correspondent disease'
        ' on the patient disease history. For example, Moderate'
        ' protein-energy malnutrition, E44.0 in ICD-10 coding',
        states=SIGNED_STATES)

    dehydration = fields.Selection(
        [(None, 'No'), ('mild', 'Mild'), ('moderate', 'Moderate'),
         ('severe', 'Severe')],
        'Dehydration', sort=False,
        help='If the patient show signs of dehydration.',
        states=SIGNED_STATES)

    @classmethod
    def get_critical_info_fields(cls):
        '''
        return the list of field names that are used to calculate
        the critical_info summary field
        '''
        return ['temperature', 'dehydration', 'systolic', 'diastolic',
                'bpm', 'respiratory_rate', 'osat']

    def make_critical_info(self):
        line = []
        if self.dehydration:
            line.append(u'DHy-%s' % self.dehydration)
            # ToDo: Find proper code for dehydrated
        if self.temperature:
            line.append(u'%4.2f°C' % self.temperature)
        if self.systolic and self.diastolic:
            line.append(u'bp %3.0f/%3.0f' % (self.systolic, self.diastolic))
        if self.bpm:
            line.append(u'P %dbpm' % self.bpm)
        if self.respiratory_rate:
            line.append(u'R %d' % self.respiratory_rate)
        if self.osat:
            line.append(u'O2 %d' % self.osat)
        return u", ".join(line)

    def get_report_info(self, name):
        lines = [[u'== Vital Signs ==']]
        if self.dehydration:
            lines.append((u'* Dehydrated:', self.dehydration))
        if self.malnutrition:
            lines.append((u'* Malnourished',))
        if self.temperature:
            lines.append((u'* Temperature:', u'%4.2f°C' % self.temperature))
        if self.systolic and self.diastolic:
            lines.append((u'* Blood Pressure:',
                          u'%3.0f/%3.0f' % (self.systolic, self.diastolic)))
        if self.bpm:
            lines.append((u'* Heart Rate:', '%dbpm' % self.bpm, ))
        if self.respiratory_rate:
            lines.append(('* Respiratory Rate: %d' % self.respiratory_rate, ))
        if self.osat:
            lines.append((u'* Oxygen Saturation: %d' % self.osat, ))

        # ToDo: Put in the urine dipstick fields

        if self.notes:
            lines.extend([[u'\n=== Notes ==='], [unicode(self.notes)]])
        return u'\n'.join([u' '.join(x) for x in lines])

    @staticmethod
    def uri_selection():
        return [(x, x) for x in URI_COMBOS['default']]
