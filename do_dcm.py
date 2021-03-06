import argparse
import os, subprocess
import shutil


niidir = '/data/MBDU/ABCD/BIDS/NKI_script/MID/'
raw_location = '/data/MBDU/ABCDraw'

dcm2niidir = '/home/kondylisjg/temp/dcm2niix_3-Jan-2018_lnx'
dcm2niix = dcm2niidir + '/dcm2niix'

def gen_directories(subject):
    os.makedirs(niidir + '/sub-' + subject + '/ses-1/func')
    os.mkdir(niidir + '/sub-' + subject + '/ses-1/anat')
    os.mkdir(niidir + '/sub-' + subject + '/ses-1/rest')
    os.mkdir(niidir + '/sub-' + subject + '/tmp')
    os.mkdir(niidir + '/sub-' + subject + '/tmp/niix')


def get_niix_directory(subject, epi):
    if epi == "MID" or epi == "NBack" or epi == "SST":
        return niidir + '/sub-' + subject + '/ses-1/func'
    elif epi == "T1" or epi == "T2":
        return niidir + '/sub-' + subject + '/ses-1/anat'
    elif epi == "Rest":
        return niidir + '/sub-' + subject + '/ses-1/rest'
    else:
        print ("ERROR for niix directory!! wrong epi: %s" % epi)


def copy_events(subject, epi, run):
    this_run = '_Run'+str(run)+'_'
    source = raw_location + '/' + epi + this_run + 'events/'
    if not os.path.isdir(source):
        return
    event_file = [f for f in os.listdir(source) if subject in f]
    if not event_file:
        return
    output_dir = get_niix_directory(subject, epi)
    shutil.copy2(source + event_file[0], output_dir)


def json_fixup(subject, epi):
    curr_dir = os.getcwd()
    output_dir = get_niix_directory(subject, epi)
    os.chdir(output_dir)
    for json in os.listdir('.'):
        if json.endswith('.json'):
            # file name format: Subject_ses-1_task-nameoftask_...we want nameoftask
            task_name = json.split('_')[2].split('-')[1]
            is_taskname = subprocess.check_output(['jq', '.TaskName', json])
            if is_taskname.strip() == 'null':
                os.system('jq \'. |= . + {"TaskName": \"\'' + task_name + '\'\"}\' ' + json + ' > temp.json')
                os.remove(json)
                os.rename('temp.json', json)
    os.chdir(curr_dir)


def call_dcm2niix(subject, epi, run):
    target = niidir + '/sub-' + subject + '/tmp'
    curr_dir = os.getcwd()
    if epi == "T":
        epi += str(run)
        source = raw_location + '/' + epi
        tar_ext = 'anat'
    else:
        this_run = '_Run'+str(run)+'_'
        source = raw_location + '/' + epi + this_run + 'EPI'
        tar_ext = 'func'
    if not os.path.isdir(source):
        return

    # Untar files..
    tgz_file = [f for f in os.listdir(source) if subject in f]
    if not tgz_file:
        return
    subprocess.check_call(['/usr/bin/tar', '-xvzf', source + '/' + tgz_file[0], '-C', target])
    # Source of dcm2niix is target of untar, place nii files in new target
    source = target + '/sub-' + subject + '/ses-baselineYear1Arm1/' + tar_ext
    try:
        subprocess.check_call([dcm2niix, '-o', target + '/niix', '-f', subject + '_func_%p', source])
    except:
        print("ERROR!! dcm2niix failed\n")
        return True
    # Remove untared raw files
    shutil.rmtree(target + '/sub-' + subject)
    # Rename files
    os.chdir(target + '/niix')
    output_dir = get_niix_directory(subject, epi)
    for files in os.listdir('.'):
        _, ext = os.path.splitext(files)
        if epi != "T1" and epi != "T2":
            os.rename(files,
                      output_dir + '/sub-' + subject + '_ses-1_task-'+epi.lower()+'_run-'+str(run)+'_bold' + ext)
        else:
            os.rename(files,
                      output_dir + '/sub-' + subject + '_ses-1_' + epi + 'w' + ext)
    # Switch back to original directory
    os.chdir(curr_dir)
    return False


# subject = "NDAR_INV007W6H7B"
# Siemens:
# subject = "NDARINVPKD1XX0E"
# subject = "NDARINVPNUJ3TUX"
# subject = "NDAR_INVUGKWA479"
# GE:
# subject = "NDAR_INV0191C80U"

epis = ['MID', 'NBack', 'SST', 'Rest', 'T']
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='This script works on already downloaded raw zipped data; it untars raw data, applies dcm2niix and stores results in per subject directories')
    parser.add_argument('--line', type=int, default=0, help='Line to process from subject file')
    args = parser.parse_args()

    # Pick the subject on the line given as input to the script
    with open('image03_subjects.txt', 'r') as f:
        for i, line in enumerate(f):
            if i == args.line:
                subject = line.strip()
                break
    try:
        subject
    except:
        exit(0)
    gen_directories(subject)
    for epi in epis:
        for run in range(1, 5):
            fail = call_dcm2niix(subject, epi, run)
            if not fail:
                copy_events(subject, epi, run)
            else:
                failed = get_niix_directory(subject, epi) + '/FAILED'
                if os.path.isfile(failed):
                    mode = 'a'
                else:
                    mode = 'w'
                with open(failed, mode) as f:
                    f.write('dcm2niix failed task %s run %d\n' % (epi, run))
        json_fixup(subject, 'MID')
        json_fixup(subject, 'Rest')
    # Remove the temporary directory we stored untared data etc..
    shutil.rmtree(niidir + '/sub-' + subject + '/tmp')
