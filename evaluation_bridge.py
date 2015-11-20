# Stuff that translates evaluations to encounters


def reductor(ev):
    def real_reductor(a, b):
        return getattr(ev, a) or getattr(ev, b)


def make_encounter(ev):
    '''returns a tuple with an encounter dict and a list of
    component dicts .

    ({encounter_data}, [{component0}, {component1}])
    '''
    start_time = ev.evaluation_start
    end_time = ev.evaluation_endtime
    encounter = {
        'patient': ev.patient,
        'start_time': start_time,
        'end_time': end_time,
        'state': ev.state,
        'appointment': ev.evaluation_date,
        'next_appointment': ev.next_evaluation,
        'signed_by': ev.signed_by,
        'sign_time': ev.write_date,
        'institution': ev.institution,
        'primary_complaint': ev.chief_complaint, 
        'fvty': ev.first_visit_this_year}
    components = []
    if ev.weight or ev.height or ev.abdominal_circ or ev.hip:
        comp = {
            'model': 'gnuhealth.encounter.anthropometry',
            'weight': ev.weight,
            'height': ev.height,
            'bmi': ev.bmi,
            'head_circumfrence': ev.head_circumfrence,
            'abdominal_circ': ev.abdominal_circ,
            'hip': ev.hip,
            'whr': ev.whr}
        components.append(comp)
    reducer = reductor(ev)
    ambu_fields = ['dehydration', 'temperature', 'osat', 'bpm',
                   'respiratory_rate', 'cholesterol_total', 'glycemia',
                   'ldl', 'hdl', 'tag', 'hba1c', 'systolic', 'diastolic']

    if reduce(reducer, ambu_fields, False):
        comp = {'model': 'gnuhealth.encounter.ambulatory'}
        comp.update([(field, getattr(ev, field)) for field in ambu_fields])
        if ev.dehydration:
            comp.update(dehydration='moderate')
        components.append(comp)

    mental_fields = ['judgment', 'tremor', 'violent', 'mood', 'orientation',
                     'knowledge_current_events', 'abstraction', 'memory',
                     'vocabulary', 'calculation_ability', 'object_recognition',
                     'praxis']

    if reduce(reducer, mental_fields, False):
        mental_fields.extend(['loc', 'loc_eyes', 'loc_verbal', 'loc_motor'])
        del mental_fields[0]
        comp = {'model': 'gnuhealth.encounter.mental_status',
                'judgement': ev.judgment}
        comp.update([(fld, getattr(ev, fld)) for fld in mental_fields])
        components.append(comp)

    for comp in components:
        comp.update(
            performed_by=ev.healthprof,
            signed_by=ev.signed_by,
            start_time=start_time,
            end_time=end_time
        )
    return (encounter, components)
