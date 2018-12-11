import os
import json
import socket
import requests
from re import sub
from glob import glob 
from random import choice
from sys import exit, argv, stdout
from time import clock, time, sleep
from os import system, getenv, path, environ, getpid

import ROOT as root

_sname = 'fileutil'
_host = socket.gethostname()                                     # where we're running
_is_t3 = (_host.startswith('t3') and _host.endswith('mit.edu'))  # are we on the T3?
_user = getenv('USER')                                           # user running the task
_to_hdfs = True                                                  # should we cache on hdfs instead of local
_users = ['snarayan', 'bmaier', 'dhsu', 'ceballos', 'ballen']    # MIT T3 PandaAnalysis users 
_report_server = 'http://' + os.environ['SUBMIT_REPORT']         # where to send reports

def _validate_file(p):
    if not path.isfile(p):
        return False
    ftest = root.TFile(p)
    if bool(ftest) and not(ftest.IsZombie()):
        print(_sname+'._validate_file', '%s is a good file'%p)
        return True 
    return False

def request_data(xrd_path, first_attempt):
    # print(_sname+'.request_data', xrd_path)

    panda_id = xrd_path.split('/')[-1].split('_')[-1].replace('.root', '')
    input_path = 'input_%s.root'%panda_id

    if 'scratch' in xrd_path:
        local_path = xrd_path.replace('root://t3serv006.mit.edu/', '/mnt/hadoop')
    else:
        local_path = xrd_path.replace('root://xrootd.cmsaf.mit.edu/', '/mnt/hadoop/cms')

    # if we're on the T3, only attempt to access the local data once, otherwise go for T2
    if first_attempt or not _is_t3:
        # first see if data is already present - if so, great!
        if _validate_file(local_path):
            print(_sname+'.request_data', 'Using local file %s'%local_path)
            return local_path 

        if _is_t3:
            for user in _users:
                local_user_path = local_path.replace('paus', user)
                if _validate_file(local_user_path):
                    # tell server we're using this file
                    payload = {'path' : local_user_path, 
                               'bytes' : path.getsize(local_user_path)}
                    r = requests.post(_report_server+'/condor/requestdata', json=payload)
                    if r.status_code == 200:
                        print(_sname+'.request_data', 'return=%s'%(str(r).strip()))
                    else:
                        print(_sname+'.request_data', 'return=%s'%(str(r).strip()))
                    print(_sname+'.request_data', 'Using local user file %s'%local_path)
                    return local_user_path

    # ok now we have to copy the data in:
    xrdargs = ['xrdcopy', '-f', xrd_path]
    if not stdout.isatty():
        xrdargs.insert(1, '--nopbar')
    cache = _is_t3 and _to_hdfs
    if cache:
        input_path = local_path.replace('paus', _user) 
        parent = '/'.join(input_path.split('/')[:-1])
        if not path.isdir(parent):
            try:
                print(_sname+'.request_data', 'creating parent at '+parent)
                os.makedirs(parent)
                os.chmod(parent, 0777)
            except OSError as e:
                print(_sname+'.request_data', str(e))
                pass 
    xrdargs.append(input_path)
    xrdargs = ' '.join(xrdargs)
    print(_sname+'.request_data', xrdargs)
    ret = system(xrdargs)
    if ret:
        print(_sname+'.request_data', 'Failed to xrdcopy %s'%input_path)
        return None 
    if _validate_file(input_path):
        if cache:
            payload = {'path' : input_path, 
                       'bytes' : path.getsize(input_path)}
            r = requests.post(_report_server+'/condor/requestdata', json=payload)
            os.chmod(input_path, 0777)
        print(_sname+'.request_data', 'Successfully xrdcopied %s'%input_path)
        return input_path
    return None 
