=====================================

Health Encounter Scenario

=====================================


=====================================

General Setup

=====================================


Imports::

    >>> import coverage

    >>> from random import randrange

    >>> from datetime import datetime, timedelta

    >>> from dateutil.relativedelta import relativedelta

    >>> from decimal import Decimal

    >>> from proteus import config, Model, Wizard

    >>> from trytond.modules.health_disease_notification.tests.database_config import set_up_datebase

    >>> from trytond.modules.health_jamaica.tryton_utils import random_bool, random_id



Create database::



    >>> COV = coverage.Coverage()

    >>> COV.start()

    >>> CONFIG = set_up_datebase()

    >>> CONFIG.pool.test = True



Get Patient::



    >>> Patient = Model.get('gnuhealth.patient')

    >>> HealthProfessional = Model.get('gnuhealth.healthprofessional')

    >>> Institution = Model.get('gnuhealth.institution')

    >>> institution, = Institution.find([('id', '=', random_id(randrange(25, 89)))])

    >>> patient, = Patient.find([('id', '=', '1')])

    >>> healthprof, = HealthProfessional.find([('id', '=', '1')])



Create Appointment::



    >>> Appointment = Model.get('gnuhealth.appointment')

    >>> appointment = Appointment()

    >>> appointment.patient = patient

    >>> appointment.type = 'ambulatory'

    >>> Specialty = Model.get('gnuhealth.specialty')

    >>> specialty, = Specialty.find([('id', '=', random_id(40))])

    >>> appointment.speciality = specialty

    >>> appointment.appointment_date = datetime.now()

    >>> appointment.save()

    >>> appointment.is_today
    True

    >>> appointment_next = Appointment()

    >>> appointment_next.patient = patient

    >>> appointment_next.type = 'ambulatory'

    >>> Specialty = Model.get('gnuhealth.specialty')

    >>> specialty, = Specialty.find([('code', '=', 'BIOCHEM')])

    >>> appointment_next.speciality = specialty

    >>> appointment_next.appointment_date = datetime.now() + timedelta(days=30)

    >>> appointment_next.save()

    >>> appointment_next.is_today
    False


Create Encounter::



    >>> appointment.state
    u'confirmed'

    >>> appointment.click('client_arrived')

    >>> appointment.tree_color
    'blue'

    >>> appointment_next.tree_color
    'black'

    >>> appointment.state
    u'arrived'

    >>> encounter_num = appointment.click('start_encounter')

    >>> Encounter = Model.get('gnuhealth.encounter')

    >>> encounter = Encounter()

    >>> encounter.appointment = appointment

    >>> encounter.patient = appointment.patient

    >>> encounter.start_time = datetime.now()

    >>> encounter.save()

    >>> encounter.primary_complaint = 'Fever, Headache, Muscle-ache'

    >>> Institution = Model.get('gnuhealth.institution')

    >>> institution, = Institution.find([('id', '=', '1')])

    >>> encounter.institution = institution

    >>> encounter.next_appointment = appointment_next

    >>> encounter.fvyt = random_bool()

    >>> Encounter_Ambulatory = Model.get('gnuhealth.encounter.ambulatory')

    >>> component_amb = Encounter_Ambulatory()

    >>> component_amb.systolic = 180

    >>> component_amb.diastolic = 88

    >>> component_amb.bpm = 80

    >>> component_amb.respiratory_rate = 35

    >>> component_amb.osat = 25

    >>> component_amb.temperature = 31

    >>> component_amb.childbearing_age = random_bool()

    >>> component_amb.pregnant = random_bool()

    >>> component_amb.lmp = datetime.now() + timedelta(days=-25)

    >>> component_amb.glucose = 5

    >>> component_amb.uri_ph = Decimal(3)

    >>> component_amb.uri_specific_gravity = Decimal(9)

    >>> component_amb.uri_protein = 'neg'

    >>> component_amb.uri_blood = '++'

    >>> component_amb.uri_glucose = '++++'

    >>> component_amb.uri_nitrite = 'trace'

    >>> component_amb.uri_bilirubin = '+++'

    >>> component_amb.uri_leuko = '++'

    >>> component_amb.uri_ketone = '+++'

    >>> component_amb.uri_urobili = '+'

    >>> component_amb.malnutrition = random_bool()

    >>> component_amb.dehydration = 'mild'

    >>> component_amb.encounter = encounter

    >>> component_amb.save()

    >>> Healthprof = Model.get('gnuhealth.healthprofessional')

    >>> healthprof, = Healthprof.find([('id', '=', '1')])

    >>> component_amb.signed_by = healthprof

    >>> component_amb.sign_time = datetime.now()

    >>> component_amb.save()

    >>> Encounter_Anth = Model.get('gnuhealth.encounter.anthropometry')

    >>> component_anth = Encounter_Anth()

    >>> component_anth.weight = Decimal(90)

    >>> component_anth.height = Decimal(170)

    >>> component_anth.head_circumference = Decimal(30)

    >>> component_anth.abdominal_circ = Decimal(35)

    >>> component_anth.hip = Decimal(50)

    >>> component_anth.whr = Decimal(1.5)

    >>> component_anth.signed_by = healthprof

    >>> component_anth.sign_time = datetime.now()

    >>> component_anth.encounter = encounter

    >>> component_anth.save()

    >>> Encounter_Mental_Stat = Model.get('gnuhealth.encounter.mental_status')

    >>> component_mental_stat = Encounter_Mental_Stat()

    >>> component_mental_stat.loc = 5

    >>> component_mental_stat.loc_eyes = '4'

    >>> component_mental_stat.loc_verbal = '2'

    >>> component_mental_stat.loc_motor = '6'

    >>> component_mental_stat.tremor = random_bool()

    >>> component_mental_stat.violent = random_bool()

    >>> component_mental_stat.mood = 'n'

    >>> component_mental_stat.orientation = random_bool()

    >>> component_mental_stat.memory = random_bool()

    >>> component_mental_stat.knowledge_current_events = random_bool()

    >>> component_mental_stat.judgement = random_bool()

    >>> component_mental_stat.abstraction = random_bool()

    >>> component_mental_stat.vocabulary = random_bool()

    >>> component_mental_stat.calculation_ability = random_bool()

    >>> component_mental_stat.object_recognition = random_bool()

    >>> component_mental_stat.praxis = random_bool()

    >>> component_mental_stat.signed_by = healthprof

    >>> component_mental_stat.sign_time = datetime.now()

    >>> component_mental_stat.encounter = encounter

    >>> component_mental_stat.save()

    >>> encounter.end_time = datetime.now() + timedelta(minutes=30)

    >>> encounter.save()

    >>> encounter.click('set_done')

    >>> encounter.click('sign_finish')

    >>> appointment.save()

    >>> len(appointment.state_changes) == 3
    True

    >>> appointment.state_changes[0].target_state
    u'done'

    >>> encounter.upi == None
    False

    >>> COV.stop()

    >>> COV.save()

    >>> report = COV.html_report()
