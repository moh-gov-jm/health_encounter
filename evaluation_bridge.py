# Stuff that translates evaluations to encounters
import sys
from datetime import timedelta
from trytond.modules.health.health import HealthInstitution
from proteus import Model, config as pconfig
from getpass import getpass

DELAY = timedelta(0, 120)  # artificial 2 minute delay
HERE = None

def reductor(ev):
    def real_reductor(a, b):
        if a and isinstance(a, (str, unicode)):
            return (getattr(ev, a) and a) or (getattr(ev, b) and b)
        else:
            return b

    return real_reductor

def get_institution():
    global HERE
    if not HERE:
        Company = Model.get('company.company')
        company = Company(1)
        HealthInstitution = Model.get('gnuhealth.institution')
        institution, = HealthInstitution.find([('name', '=', company.party.id)])
        HERE = institution.id
    return HERE


def Id(val):
    if val and hasattr(val, 'id'):
        return val.id
    else:
        return val

def make_encounter(ev):
    '''returns a tuple with an encounter dict and a list of
    component dicts .

    ({encounter_data}, [{component0}, {component1}])
    '''
    start_time = ev.evaluation_start
    end_time = ev.evaluation_endtime
    insti = ev.institution
    if not insti:
        insti = get_institution()
    if end_time and end_time <= start_time:
        end_time = start_time + DELAY
    encounter = {
        'patient': Id(ev.patient),
        'start_time': start_time,
        'end_time': end_time,
        'state': 'signed' if ev.state=='done' else ev.state,
        'appointment': Id(ev.evaluation_date),
        'next_appointment': Id(ev.next_evaluation),
        'signed_by': Id(ev.signed_by),
        'sign_time': end_time,
        'institution': Id(insti),
        'primary_complaint': ev.chief_complaint,
        'fvty': ev.first_visit_this_year}
    components = []
    if ev.weight or ev.height or ev.abdominal_circ or ev.hip:
        comp = {
            'model': 'gnuhealth.encounter.anthropometry',
            'weight': ev.weight,
            'height': ev.height,
            'bmi': ev.bmi,
            'head_circumference': ev.head_circumference,
            'abdominal_circ': ev.abdominal_circ,
            'hip': ev.hip,
            'whr': ev.whr}
        components.append(comp)
    reducer = reductor(ev)
    ambu_fields = ['dehydration', 'temperature', 'osat', 'bpm',
                   'respiratory_rate', 'cholesterol_total', 'glycemia',
                   'ldl', 'hdl', 'tag', 'hba1c', 'systolic', 'diastolic',
                   'notes_complaint']

    if reduce(reducer, ambu_fields):
        ambu_fields = ambu_fields[1:-1]
        comp = {'model': 'gnuhealth.encounter.ambulatory',
                'notes': ev.notes_complaint}
        comp.update([(field, getattr(ev, field)) for field in ambu_fields])
        if ev.dehydration:
            comp.update(dehydration='moderate')
        components.append(comp)

    mental_fields = ['judgment', 'tremor', 'violent', 'mood', 'orientation',
                     'knowledge_current_events', 'abstraction', 'memory',
                     'vocabulary', 'calculation_ability', 'object_recognition',
                     'praxis']

    if reduce(reducer, mental_fields):
        mental_fields.extend(['loc', 'loc_eyes', 'loc_verbal', 'loc_motor'])
        del mental_fields[0]
        comp = {'model': 'gnuhealth.encounter.mental_status',
                'judgement': ev.judgment}
        comp.update([(fld, getattr(ev, fld)) for fld in mental_fields])
        components.append(comp)

    clinical_fields = ['diagnosis', 'info_diagnosis', 'directions',
                       'diagnostic_hypothesis', 'secondary_conditions',
                       'signs_and_symptoms']
    if reduce(reducer, clinical_fields):
        comp = {'model': 'gnuhealth.encounter.clinical'}
                # 'diagnosis': Id(ev.diagnosis)}
        if ev.diagnosis:  # regular properly coded evaluation
            comp.update(diagnosis=Id(ev.diagnosis))
            for comp_field, ev_field in [
                    ('diagnostic_hypothesis', 'diagnostic_hypothesis'),
                    ('secondary_conditions', 'secondary_conditions'),
                    ('signs_symptoms', 'signs_and_symptoms')]:
                ev_fld_data = getattr(ev, ev_field)
                if ev_fld_data:
                    comp[comp_field] = [('add',
                                        [x.id for x in ev_fld_data])]
        else:  # we have to figure it out from the DDx and 2ndary
            ddx = ev.diagnostic_hypothesis
            if len(ddx) == 1:  # single DDx and no presumptive?
                comp.update(diagnosis=Id(ddx[0].pathology))  # ,
                            # newly_diagnosed=ddx[0].first_diagnosis)
            elif len(ddx) > 1:  # convert the rest to secondary conditions
                comp.update(
                    secondary_conditions=[
                        ('create', [{'pathology': Id(x.pathology),
                                     'comments':x.comments}
                                     # 'newly_diagnosed': x.first_diagnosis}
                                    for x in ddx]
                        )
                    ]
                )

        comp_notes = filter(None, [ev.info_diagnosis, ev.notes])
        comp['notes'] = '\n'.join(comp_notes)
        comp['treatment_plan'] = ev.directions
        components.append(comp)

    if ev.actions:
        comp = {'model': 'gnuhealth.encounter.procedures',
                'procedures': [('add',
                                [x.id for x in ev.actions])]}
        components.append(comp)

    for comp in components:
        comp.update(
            performed_by=Id(ev.healthprof),
            signed_by=Id(ev.signed_by),
            start_time=start_time,
            end_time=end_time,
            sign_time=end_time
        )
    return (encounter, components)


def create_encounter(ev, pool):
    encd, comps = make_encounter(ev)
    # first setup the encounter object
    Encounter = pool.get('gnuhealth.encounter')

    enc_list = Encounter.create([encd], {})
    enc = enc_list[0]
    for x in comps:
        model_name = x.pop('model')
        model = pool.get(model_name)
        x.update(encounter=enc)
        model.create([x], {})
    ev.encounter = Encounter(enc)
    ev.save()
    return enc


def convert_remaining_evaluations(db, passwd, conffile):
    # setup proteus config
    cfg = pconfig.set_trytond(db, user='admin', password=passwd,
                              config_file=conffile)
    Evaluation = Model.get('gnuhealth.patient.evaluation')
    the_evals = Evaluation.find([('encounter', '=', None)])
    encounters = []
    bad_evals = []
    for eva in the_evals:
        try:
            encounters.append(create_encounter(eva, Model))
        except:
            bad_evals.append(eva)

    print '%d Encounters created.' % len(encounters)
    if bad_evals:
        print 'Some evaluations failed to convert (%d)' % len(bad_evals)

    return encounters, bad_evals

usage = """
%s <config_file> <database_name>

Converts Evaluations to Encounters

<config_file> = full path to trytond.conf
<database_name> = name of database to import evaluations
"""


if __name__ == '__main__':
    usages = usage % (sys.argv[0], )
    if len(sys.argv) < 3:
        print usages
    elif sys.argv[1] in ['--help', '-h', '-?']:
        print usages
    else:
        conffile, dbname = sys.argv[1:3]
        dbpwd = getpass('Enter admin password: ')
        e,b = convert_remaining_evaluations(dbname, dbpwd, conffile)
