"""This file stores the report models for health_encounter"""
#############################
# Author: Randy Burrell     #
# Date: 2016/10/11          #
#                           #
# Description: This file    #
# stores the report models  #
# for health_encounter      #
#############################

# from datetime import datetime, timedelta
# import pytz
# from trytond.pyson import Eval, PYSONEncoder, Date
# from trytond.transaction import Transaction
# from trytond.pool import Pool
from trytond.report import Report

__all__ = ('EncounterReport')

class EncounterReport(Report):
    '''This class is used to create reports for health_encounter'''
    __name__ = 'gnuhealth.encounter.report'
