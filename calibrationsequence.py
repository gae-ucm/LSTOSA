#!/usr/bin/env python2.7
from osa.utils.standardhandle import output, verbose, warning, error, stringify, gettag

__all__ = ["calibrationsequence"]

def calibrationsequence(args):
    tag = gettag()
    # This is the python interface to run sorcerer with the -c option for calibration
    # args: <RUN>    
    import sys
    import subprocess
    from os.path import join
    from osa.utils import options, cliopts
    from osa.reports import report
    from osa.jobs.job import historylevel

    pedestal_output_file = args[0]
    calibration_output_file = args[1]
    run_ped = args[2]
    run_cal = args[3]
    print("DEBUG")
   
    historyfile = join(options.directory, 'sequence_' + options.tel_id + '_' + run_cal + '.history')
    level, rc = historylevel(historyfile, 'CALIBRATION')
    verbose(tag, "Going to level {0}".format(level))
    print("historyfile:",historyfile, run_ped)
    print("DEBUG2")
    print("PEDESTAL directory:",options.directory, options.tel_id)
    print("level & rc:",level, rc)
#    exit()
    if level == 2:
        rc = drs4_pedestal(run_ped, pedestal_output_file, historyfile)
        level -=1
        verbose(tag, "Going to level {0}".format(level))
    if level == 1:
        rc = calibrate(run_cal, pedestal_output_file, calibration_output_file, historyfile)
        level -=1
        verbose(tag, "Going to level {0}".format(level))
    if level == 0:
        verbose(tag, "Job for sequence {0} finished without fatal errors".format(run_ped))
    return rc

##############################################################################
#
# DRS4 pedestal
#
##############################################################################
def drs4_pedestal(run_ped, pedestal_output_file, historyfile):
    tag = gettag()
    from sys import exit
    from os.path import join
    import subprocess
    from osa.configs.config import cfg
    from osa.reports.report import history
    from register import register_run_concept_files
    from osa.utils.utils import lstdate_to_dir

    sequencetextfile = join(options.directory, 'sequence_' + options.tel_id + '_' + run_ped+ '.txt')
    bindir = cfg.get('LSTOSA', 'LSTCHAINDIR')
    daqdir = cfg.get(options.tel_id, 'RAWDIR')
    #carddir = cfg.get('LSTOSA', 'CARDDIR')
    inputcard = cfg.get(options.tel_id, 'CALIBRATIONCONFIGCARD')
    #configcard = join(carddir, inputcard)
    commandargs = [cfg.get('PROGRAM', 'PEDESTAL')]
   
    nightdir = lstdate_to_dir(options.date)
 
    input_file = join(cfg.get('LST1','RAWDIR'),nightdir,
            'LST-1.1.Run{0}.'.format(run_ped)+'0000{0}{1}'.format(cfg.get('LSTOSA','FITSSUFFIX'),cfg.get('LSTOSA','COMPRESSEDSUFFIX')))
    
    
    max_events = cfg.get('LSTOSA', 'MAX_PED_EVENTS')

    commandargs.append('--input_file=' +  input_file)
#    commandargs.append( input_file)
    commandargs.append('--output_file=' + pedestal_output_file )
 #   commandargs.append( pedestal_output_file )
    commandargs.append('--max_events='+ max_events)

    print("COMAND for pedestal:",commandargs)
    commandconcept = 'drs4_pedestal'
    pedestalfile = 'drs4_pedestal'
    try:
        verbose(tag, "Executing \"{0}\"".format(stringify(commandargs)))
        rc = subprocess.call(commandargs)
    #except OSError as (ValueError, NameError):
    except OSError as ValueError:
        history(run_ped, commandconcept, pedestal_output_file, inputcard, ValueError, historyfile)
        error(tag, "Could not execute \"{0}\", {1}".format(stringify(commandargs), NameError), ValueError)
    except subprocess.CalledProcessError as Error:
        error(tag, Error, rc)
    else:
        history(run_ped, commandconcept, pedestal_output_file, inputcard, rc, historyfile)

    """ Error handling, for now no nonfatal errors are implemented for CALIBRATION """
  
    if rc != 0:
        exit(rc)
    return rc

##############################################################################
#
# calibrate 
#
##############################################################################
def calibrate(calibration_run_id, pedestal_file, calibration_output_file, historyfile):
    tag = gettag()
    from sys import exit
    from os.path import join
    import subprocess
    from osa.configs.config import cfg
    from osa.reports.report import history
    from register import register_run_concept_files
    from osa.utils.utils import lstdate_to_dir

    #sequencetextfile = join(options.directory, 'sequence_' + options.tel_id + '_' + run + '.txt')
    bindir = cfg.get('LSTOSA', 'LSTCHAINDIR')
    daqdir = cfg.get(options.tel_id, 'RAWDIR')
    #carddir = cfg.get('LSTOSA', 'CARDDIR')
    inputcard = cfg.get(options.tel_id, 'CALIBRATIONCONFIGCARD')
    #configcard = join(carddir, inputcard)
    commandargs = [cfg.get('PROGRAM', 'CALIBRATION')]

    nightdir = lstdate_to_dir(options.date)
    calibration_data_file = join(cfg.get('LST1','RAWDIR'),nightdir,
            'LST-1.1.Run{0}.'.format(calibration_run_id)+'0000{0}{1}'.format(cfg.get('LSTOSA','FITSSUFFIX'),cfg.get('LSTOSA','COMPRESSEDSUFFIX')))


    calib_config_file = cfg.get('LSTOSA','CALIBCONFIGFILE')


    flat_field_sample_size   = cfg.get('LSTOSA', 'FLATFIELDCALCULATORSAMPLESIZE')
    pedestal_cal_sample_size = cfg.get('LSTOSA', 'PEDESTALCALCULATORSAMPLESIZE')  
    event_source_max_events  = cfg.get('LSTOSA', 'EVENTSOURCEMAXEVENTS')      

#    calibration_version = cfg.get('LSTOSA', 'CALIBRATION_VERSION')  #def: 0
#    n_events_statistics = cfg.get('LSTOSA', 'STATISTICS')  #def: 10000
#    calibration_base_dir = cfg.get('LSTOSA', 'CALIB_BASE_DIRECTORY')  #def: '/fefs/aswg/data/real'
#    calculate_time_run = cfg.get('LSTOSA', 'CALCULATE_TIME_RUN')  #def: '1625'

    commandargs.append('--input_file=' + calibration_data_file)
    commandargs.append('--output_file=' + calibration_output_file)

    commandargs.append('--pedestal_file=' + pedestal_file)
    commandargs.append('--FlatFieldCalculator.sample_size=' + flat_field_sample_size)
    commandargs.append('--PedestalCalculator.sample_size=' + pedestal_cal_sample_size)
    commandargs.append('--EventSource.max_events=' + event_source_max_events)
    commandargs.append('--config=' + calib_config_file)

    '''
    optional.add_argument('--ff_calibration', help="Perform the charge calibration (yes/no)",type=str, default='yes')
    optional.add_argument('--tel_id', help="telescope id. Default = 1", type=int, default=1)
    '''

    print("COMAND for calib:",commandargs)
    commandconcept = 'calibration'
    calibrationfile = 'new_calib'
    try:
        verbose(tag, "Executing \"{0}\"".format(stringify(commandargs)))
        rc = subprocess.call(commandargs)
    #except OSError as (ValueError, NameError):
    except OSError as ValueError:
        history(calibration_run_id, commandconcept, calibrationfile, inputcard, ValueError, historyfile)
        error(tag, "Could not execute \"{0}\", {1}".format(stringify(commandargs), NameError), ValueError)
    except subprocess.CalledProcessError as Error:
        error(tag, Error, rc)
    else:
        history(calibration_run_id, commandconcept, calibrationfile, inputcard, rc, historyfile)

    """ Error handling, for now no nonfatal errors are implemented for CALIBRATION """
    if rc != 0:
        exit(rc)
    return rc
   
##############################################################################
#
# MAIN
#
##############################################################################
if __name__ == '__main__':
    tag = gettag()
    import sys
    from osa.utils import options, cliopts
    # Set the options through cli parsing
    args = cliopts.calibrationsequencecliparsing(sys.argv[0])
    # Run the routine
    rc = calibrationsequence(args)
    sys.exit(rc)