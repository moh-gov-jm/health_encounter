# Health Encounter

## Introduction

This Python package is a Tryton module that is desiged to work with GNU Health.

It is intended to replace the default Evaluations interface in GNU Health.
Installing it will replace the links to the Evaluation in both Patient and 
Appointment. However, the Evaluation reports have not yet been updated. 

It is very much a work in progress. Please see below for the reasoning behind 
its design. 

## Installation

No installer yet. Please copy or symlink the health_encounter folder within the
repository into the trytond/modules/ folder. After that, update any module in
tryton and then it will show up in the modules list for installation.

You need at least the health module from GNU Health and its dependencies in
order to install this.

## Design Idea

We have broken down the Evaluation into smaller pieces. Each piece is represented by its own model. All the different pieces follow some basic patterns that allow us to re-combine them using the UnionMixin mixin in Tryton 3.4.

In this module, *Evaluation* is called *Encounter* and you can add *Components* to the encounter. This base module comes with three types of Components. 

* Anthropometry : Height, weight, and other measurements
* Nursing (Ambulatory) : Vital signs, Glucose and Lipids
* Clinical : Signs and Symptoms, Diagnosis, DDx

Each Component that makes up an Encounter can be signed by a different health professional. The encounter itself can then be signed by the supervisor.

This should probably be defined in a workflow. Help needed here.

This module with its associated models were designed to solve a few specific 
problems : 

1. When a patient is handled by different health professionals, there is only 
one signature on the evaluation
2. It is difficult to have a supervisory view on the evaluation since we will 
want the performer to sign the evaluation. To do this with the current design, the performer would have to be notified of supervisor approval so she could sign
the evaluation or, the supervisor would sign it.
3. We want to use the Appointment:Evaluation concept to manage all patient interactions
4. We have many different services in Primary care. Using the components concept, we can make specialised forms for a variety of services. They can then be mixed and matched as needed.
5. There are times when serial readings of vital signs are done in what is effectively a single encounter.

## Further Development

This is by no means complete. Nor do we think it's quite ready for production. There is a lot of testing to be done and we are currently trying it out with real doctors in real clinics. 

### Automatic update of patient data

Certain patient information is useful to have during a regular consultation.
Much of this information is collected in the `Critical Information` box.
Appropriate components should push updates to this section as necessary.

### Data Import and *Evaluation Robot*

In order to use this in production, we will have to develop an import routine to get data out of Evaluations into Encounters and Components

Currently, an Evaluation record can be entirely represented using the base components. Because of this, and because other things in GNU Health are related
to Evaluations, the idea is to use a *Robot* to create Evaluation records
every time an Encounter is created.

### Additional Components

* Would be nice to have at least one part of the **Opthalmology** module show itself as a component
* A few **dental** related Components

### Health Encounter Crypto

This module is still at the concept stage. However, it is intended to add the digest and signature fields and functions to Encounter and Components.

## Component Development

To develop a new Component type. There are a few steps one will have to take. 

1. Define a model that inherits from `health_encounter.components.base.BaseComponent` (this should probably be at a more shallow location)
2. Define a form for your model that inherits from `health_encounter.health_view_form_encounter_component`
3. Define an EncounterComponentType (`gnuhealth.encounter.component_type`) record for your new type. See components/components.xml line 20 for an example

Your view-form doesn't have to ineherit from the base form, but things may be more uniform if it does.
