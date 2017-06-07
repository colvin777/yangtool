#!/usr/bin/env python
# encoding: utf-8
'''
code.convert2yang -- shortdesc

code.convert2yang is a description

It defines classes_and_methods

@author:     haoweizh

@copyright:  2017 nokia. All rights reserved.

@license:    license

@contact:    Haowei.a.Zhang@alcatel-sbell.com.cn
@deffield    updated: Updated
'''

import sys
import os
import platform
import traceback
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
try:
    import ConfigParser
except ImportError as e:
    import configparser
import logging.handlers
from lxml import etree
from io import BytesIO
import time
import convertThread
import Queue
#import string
#from functools import partial
#from optparse import OptionParser

__all__ = []
__version__ = 0.1
__date__ = '2017-05-12'
__updated__ = '2017-05-12'

DEBUG = 0
TESTRUN = 0
PROFILE = 0

inpath = ''
out = None
tool = None
logger = None

topModule = []

xslTruple = ('CE','HE','ICloud','SBC','SE')

class paramsOut():
    #__slots__ = ['outPathDir', 'inpath', 'libPath', 'xslPath', 'python', 'pyang']
    def __init__(self, _outPathDir, remove = False):
        self._outPathDir = _outPathDir
        self.remove = remove
    @property
    def outPathDir(self):
        if (os.path.exists(self._outPathDir)):
            if self.remove:
                for root, dirs, files in os.walk(self._outPathDir, topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))

        else:
            os.makedirs(self._outPathDir)
        return self._outPathDir
    @outPathDir.setter
    def outPathDir(self, value):pass
#         if (os.path.exists(value)):pass
#         else:
#             os.makedirs(self._outPathDir)
    @outPathDir.deleter      
    def outPathDir(self):pass
class checkfile():
    def __init__(self, filepath, info):
        self.filepath = filepath
        if not os.path.exists(filepath):
            logger.error(info.format(self.inpath))
            raise RuntimeError(info.format(self.inpath))
            
               
class envTool():
    #__slots__ = ['python', 'pyang']
    def __init__(self):pass
    
    def __setattr__(self, attr, value):
        if (attr == 'python'):
            if(value == '' or not os.path.exists(value)):
                self.__dict__['python'] = os.environ.get("PATH_TO_CONVERT2YANG_PYTHON") if \
                os.environ.get('PATH_TO_CONVERT2YANG_PYTHON') is not None \
                  else sys.executable
            else:
                self.__dict__['python'] = value
        elif (attr == 'pyang'):
            if(value == '' or not os.path.exists(value)):
                self.__dict__['pyang'] = os.environ.get('PYANGPATH') if \
                os.environ.get('PYANGPATH') is not None else False
                assert self.__dict__['pyang'] is not False, "could not find path to pyang"
            else:
                self.__dict__['pyang'] = value
        elif (attr == 'libPathDir'):
            if(value == '' or not os.path.exists(value)):
                self.__dict__['libPathDir'] = os.environ.get('YANG_MODPATH4') if \
                os.environ.get('YANG_MODPATHs') is not None else False
                
                if self.__dict__['libPathDir'] is None and value == '':
                    msg = "please give a directory listed of directories to search for imported modules"
                    logger.error(msg)
                    raise RuntimeError(msg)
                else:
                    msg = 'Invalid the lib ({0}) specified, please give a directory listed of directories to search for imported modules'.format(value)
                    logger.error(msg)
                    raise RuntimeError(msg)
                
#                 assert self.__dict__['libPathDir'] is not False, "could not find lib yang path to pyang"
            else:
                self.__dict__['libPathDir'] = value
        elif (attr == 'xslPathDir'):
            if(value == '' or not os.path.exists(value)):
                self.__dict__['xslPathDir'] = os.environ.get('XSL_PATH') 
                if self.__dict__['xslPathDir'] is None and value == '':
                    msg = "please give a directory contained xslt template"
                    logger.error(msg)
                    raise RuntimeError(msg)
                else:
                    msg = 'Invalid the xslt template path({0}) specified, please check again'.format(value)
                    logger.error(msg)
                    raise RuntimeError(msg)
               
#                 assert self.__dict__['xslPathDir'] is not False, "could not find XSL template path to pyang"
            else:
                self.__dict__['xslPathDir'] = value
    def __getattribute__(self, name):
        return getattr(self, name)
#         object.__getattribute__(self, name)
        #return self.__dict__[name]
      

class convert():
    global tool
    global out
    def __init__(self): pass
    def convertBwYangAndYin(self, fomat, inputfileName, outputfileName):
        sys.stdout.write('#'+'->'+"\b\b")
        sys.stdout.flush()
        if (os.path.exists(outputfileName)):
            os.remove(outputfileName)
        #logger.debug(tool.pyang, tool.python, fomat, outputfileName, tool.libPathDir, inputfileName)
        cmd = "%s " % tool.python
        cmd += "%s " % tool.pyang
        cmd += " -f %s " %fomat
        cmd += " -o %s" % outputfileName
        cmd += " -p %s" % tool.libPathDir
        cmd += " %s" % inputfileName
#         cmd += " --strict"
        if(fomat == 'yang') and not (inputfileName.endswith('gw-platform.yin') or inputfileName.endswith('_index_.yin')):
            cmd += " --yang-remove-unused-imports"
        else:
            cmd += " --trim-yin"
        logger.debug('pyang command: %s' % cmd)
        
        import subprocess
        
#         status = os.system(cmd)
        try:
            output1 = subprocess.check_output(cmd, stderr=subprocess.STDOUT,shell=True)
            logger.debug(output1)
        except Exception as e:
            logger.error(e.output)
            logger.error("Execution failed: %s", e)
            print('\n' + e.output)
            print >>sys.stderr, "Execution failed:", e
            raise e
        
        return outputfileName
    
class split_yin():
    '''
    classdocs
    '''


    def __init__(self, inputFilePath, tool, netype):
        '''
        Constructor
        '''
        self.inputFilePath = inputFilePath
        #self.xsltfile = tool.xslPathDir
        #self.xslfileName = netype+'.xsl'
        self.xsltfilePath = os.path.join(tool.xslPathDir, 'style-'+netype+'.xsl')
        
    def splitByxslt(self):  
        tree = etree.parse(self.inputFilePath) 
        xslt_root = etree.parse(self.xsltfilePath)  
        transform = etree.XSLT(xslt_root)
        result_tree = str(transform(tree))
        flag, belong_to = self.filter(result_tree)
        return flag, belong_to, result_tree
    
    def filter(self, neXml):
        belong_to = None
        root = etree.XML(neXml) 
        expr = "//*[local-name() = $name]"
        lst = root.xpath(expr, name = "container")
        lsl = root.xpath(expr, name = "list")
        lsm = root.xpath(expr, name = "module") 
        lssm = root.xpath(expr, name = "submodule")
        lsb = root.xpath(expr, name = "belongs-to")
        if len(lsb) > 0:
            belong_to = lsb[0].get('module')
            if(belong_to == 'ALUYangExtensions'):
                return False, belong_to
        return len(lst) == 0 and len(lsl) == 0 and len(lsm) == 0 and len(lssm) > 0, belong_to
        
class handleyin():
    global out
    def __init__(self):
        self.yinOriginPath = paramsOut(os.path.join(out.outPathDir, 'temp'), True).outPathDir
    def handle(self, top):
        try:
            if os.path.isfile(top):
                belong_to = None
                outYinPath = self.traslate(os.path.basename(top), os.path.dirname(top))
            #===================================================================
            # if this yang is submodule, deal with module 
            #===================================================================
                tree = etree.parse(outYinPath)
                expr = "//*[local-name() = $name]"
                lsb = tree.xpath(expr, name = "belongs-to")
                if len(lsb) > 0:
                    belong_to = lsb[0].get('module')
                if belong_to is not None:
                    self.traslate(belong_to+'.yang', os.path.dirname(top))
                 
            for root, dirs, files in os.walk(top, topdown=False):
                for name in files:
                    if name.endswith('.yang'):
                        self.traslate(name, root)
                    
                    
        #=======================================================================
        # deal with top Module
        #=======================================================================
        
            for mo in topModule:
                outYinPath = self.traslate(os.path.basename(mo), os.path.dirname(mo))
        except Exception as e:
            raise e
        return self.yinOriginPath
    
    
    def traslate(self, name, directory):
        if name.endswith('.yang'):
            yin = name.split('.')[0]+'.yin'
            outOriginYin = os.path.join(self.yinOriginPath, yin)
            if (os.path.exists(outOriginYin)):
                os.remove(outOriginYin)
            do = convert()
            try:
                return do.convertBwYangAndYin('yin', os.path.join(directory, name), outOriginYin)
            except Exception as e:
                raise e
         
        
class removeAll():
    def __init__(self):pass
    def removeFileAndDir(self, path):
        if(os.path.exists(path)):
            for root, dirs, files in os.walk(path, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))  
        os.rmdir(path)
class handleYang():
    global inpath 
    global tool
    global out
    global DEBUG
    def __init__(self, neType):
        self.neType = neType
        self.yinPath = out.outPathDir
        self.nePath = paramsOut(os.path.join(out.outPathDir, self.neType)).outPathDir
        self.yintempDir = paramsOut(os.path.join(out.outPathDir, self.neType, 'temp'), True).outPathDir
        #print(self.yinPath)
    #===========================================================================
    # input is file or dir
    #===========================================================================
        
    def handle(self, top):
        listRY = {}
        for entry in os.listdir(top):
            if str(entry).endswith('.yin'):
                outtempYin = os.path.join(self.yintempDir, entry)
                outyin = os.path.join(top, entry)
                split = split_yin(outyin, tool, self.neType)
                isEmpty,belong_to, newXml = split.splitByxslt()
                if isEmpty is False:
                    f = BytesIO(newXml.encode())
                    tree = etree.parse(f)
                    tree.write(outtempYin)
                else:
                    if belong_to != None:
                        listRY[entry.split('.')[0]] = belong_to
                

                    
        logger.debug(listRY)
        
        for mo in listRY.keys():
            modulePath  = os.path.join(self.yintempDir, listRY[mo]+'.yin')
            logger.debug('remove include module path : %s' % modulePath)
#             print('remove include module path : %s' % modulePath)
            #root = None
            checkfile(modulePath, 'when split yang, need its module:{0}, please make sure this module is valid')
            self.removeTag(modulePath, 'include', 'module', mo)
#             root = etree.parse(modulePath)
#             expr = "//*[local-name() = $name]"
#             lsms = root.xpath(expr, name = "include")
#             for s in lsms:
#                 if(s.get('module') == str(mo)):
#                     s.getparent().remove(s) 
#             os.remove(modulePath)
#             root.write(modulePath)
        
        #=======================================================================
        # check module is empty or not
        #=======================================================================
#         time.sleep(30)
        removeTopModule = True
        moduleList = list(set(listRY.values()))
        logger.debug('start check module is empty or not!')
        for mo in moduleList:
            logger.debug('check module path : %s' % mo)
            deleteMo = False
            modulePath  = os.path.join(self.yintempDir, mo+'.yin')
            root = etree.parse(modulePath)
            expr = "//*[local-name() = $name]"
            lsms = root.xpath(expr, name = "include")
#             for s in lsms:
            logger.debug('module path is %s' % modulePath)
            if len(lsms) ==0 or lsms is None:
                deleteMo = True
            elif len(lsms) == 1:
                if lsms[0].get('module') == mo+'-common':
                    deleteMo = True
                    commonSubModuePath  = os.path.join(self.yintempDir, mo+'-common'+'.yin')
                    if os.path.exists(commonSubModuePath):
                        os.remove(commonSubModuePath)
            logger.debug('status is %s' % deleteMo)   
            if deleteMo:
                removeTopModule = False
                os.remove(modulePath)
                logger.debug('delete module is %s' % modulePath)
                self.removeTag(os.path.join(self.yintempDir, 'gw-platform.yin'), 'import', 'module', mo)
                self.removeTag(os.path.join(self.yintempDir, '_index_.yin'), 'import', 'module', mo)
                   
        logger.debug('finish check module!') 
        if removeTopModule:
            os.remove(os.path.join(self.yintempDir, 'gw-platform.yin'))
            os.remove(os.path.join(self.yintempDir, '_index_.yin'))   
                
                
        for root, dirs, files in os.walk(self.yintempDir, topdown=False):
            for name in files:
                if name.endswith('.yin'):
                    yang = name.split('.')[0]+'.yang'
                    outyang = os.path.join(self.nePath, yang)
                    do = convert()
                    do.convertBwYangAndYin('yang', os.path.join(root, name), outyang)
        
        if DEBUG == 0:
            removeAll().removeFileAndDir(self.yintempDir)
            for entry in os.listdir(self.nePath):
                if str(entry).endswith('.yin'):
                    os.remove(os.path.join())

        
    def removeTag(self, path, tag, AttributeName, value):
        reWrite = False
        root = etree.parse(path)
        expr = "//*[local-name() = $name]"
        lsms = root.xpath(expr, name =tag )
        for s in lsms:
            if(s.get(AttributeName) == value):
                reWrite = True
                logger.debug('remove tag is %s' % s.get(AttributeName))
                s.getparent().remove(s) 
        if reWrite:
#             os.remove(path)
            root.write(path) 
    
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type is None:
            pass
        else:
            logger.error(exc_value)
            raise RuntimeError(exc_value)
                            
def concurrentConvert(neType, originPath):
    try:
        with handleYang(neType) as handle:
            handle.handle(originPath)
    except Exception as e:
        raise e
#     handle = handleYang(neType)
#     handle.handle(originPath)

def checkTopModule(topPath):
    platformMod = False
    indexMod = False
    platformModDir = None
    indexModDir = None
    if os.path.isfile(topPath):
        return False,platformModDir, indexModDir
    for root, dirs, files in os.walk(topPath, topdown=False):
        for f in files:
            if f == 'gw-platform.yang':
                platformMod = True
                platformModDir = os.path.join(root, 'gw-platform.yang')
            elif f == '_index_.yang':
                indexMod = True
                indexModDir  =os.path.join(root, '_index_.yang')
    return platformMod and indexMod, platformModDir, indexModDir

def main(argv=None):
    
    '''
    Main function for the convert2yang start-up.

    Called with command-line arguments:
        *    --config *<file>*
        *    --section *<section>*
        *    --verbose

    Where:

        *<file>* specifies the path to the configuration file.

        *<section>* specifies the section within that config file.

        *verbose* generates more information in the log files.

    The process listens for REST API invocations and checks them. Errors are
    displayed to stdout and logged.
    '''

    start = time.time()
    global inpath 
    global tool
    global out
    global DEBUG
    global logger 
    global topModule
    
    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = 'v{0}'.format(__version__)
    program_build_date = str(__updated__)
    program_version_message = 'Convert YANG Tool {0} ({1})'.format(program_version,
                                                         program_build_date)
    if (__import__('__main__').__doc__ is not None):
        program_shortdesc = __import__('__main__').__doc__.split('\n')[1]
    else:
        program_shortdesc = 'Running in test harness'
    program_license = '''{0}

  Created  on {1}.
  Copyright 2015 Metaswitch Networks Ltd. All rights reserved.

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
'''.format(program_shortdesc, str(__date__))
    '''Command line options.'''


    try:
        #----------------------------------------------------------------------
        # Setup argument parser so we can parse the command-line.
        #----------------------------------------------------------------------
        parser = ArgumentParser(description=program_license,
                                formatter_class=ArgumentDefaultsHelpFormatter)
        parser.add_argument('-v', '--verbose',
                            dest='verbose',
                            action='count',
                            help='set verbosity level')
        parser.add_argument('-V', '--version',
                            action='version',
                            version=program_version_message,
                            help='Display version information')
        
        parser.add_argument('-i', '--input',
                            dest='inpath',
                            default='None',
                            help='Specify the YANG file or directory')
        
        parser.add_argument('-o', '--output',
                            dest='outpath',
                            default='None',
                            help='Specify directory to store splited yang')
        
        parser.add_argument('-p', '--libpath',
                            dest='libpath',
                            default='None',
                            help="""
                                path is a colon (:) separated list of directories to search for imported modules. This option may be given multiple times.
                                The following directories are always added to the search path: 
                                1. current directory
                                2. config this parameter use libpath in yangtool.conf, for example libpath=../../yang-source
                                3.  $YANG_MODPATH
                                """)
        
        parser.add_argument('-x', '--xslpath',
                            dest='xslpath',
                            default='None',
                            help='Specify path contained xsl template file ' \
                            'The following directories are always added to the search path:'\
                            '1. config this parameter use xslpath in yangtool.conf, for example xslpath=../../yang-source/xslt-file '\
                            '2. $XSL_PATH')
        
        
        parser.add_argument('-d', '--debug',
                            dest='debug',
                            default='None',
                            help='set debug parameter, 0 means non-debug, 1 means debug')
        
        parser.add_argument('-c', '--config',
                            dest='config',
                            default='../../logs/convert2yang.log',
                            help='Use this config file.',
                            metavar='<file>')
        
        parser.add_argument('-s', '--section',
                            dest='section',
                            default='default',
                            metavar='<section>',
                            help='section to use in the config file')
      
        #----------------------------------------------------------------------
        # Process arguments received.
        #----------------------------------------------------------------------
        args = parser.parse_args()
        verbose = args.verbose
        config_file = args.config
        config_section = args.section
        
        inpath = args.inpath
        outpath = args.outpath
        libpath = args.libpath
        xslpath = args.xslpath
        debug = args.debug
        
        #----------------------------------------------------------------------
        # Now read the config file, using command-line supplied values as
        # overrides.
        #----------------------------------------------------------------------
        config = None
        defaults = {
                   }
        overrides = {}
        try:
            config = ConfigParser.SafeConfigParser(defaults)
        except Exception:
            config = configparser.ConfigParser()
        config.read(config_file)
        
        log_file = config.get(config_section, 'log_file', vars=overrides)
      
        logger = logging.getLogger('convert2yang')
        print('Logfile: {0}'.format(log_file))
        
        if verbose > 1:
            print('Verbose mode on')
            logger.setLevel(logging.DEBUG)
        else:
            print('Verbose mode off')
            logger.setLevel(logging.INFO)
        handler = logging.handlers.RotatingFileHandler(log_file,
                                                       maxBytes=1000000,
                                                       backupCount=10)
        if (platform.system() == 'Windows'):
            date_format = '%Y-%m-%d %H:%M:%S'
        else:
            date_format = '%Y-%m-%d %H:%M:%S.%f %z'
        formatter = logging.Formatter('%(asctime)s %(name)s - '
                                      '%(levelname)s - %(message)s',
                                      date_format)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.info('Started')
        
        #----------------------------------------------------------------------
        # extract the values we want.
        #----------------------------------------------------------------------
        
        tool = envTool()
        if outpath == 'None':
            outpath = config.get(config_section,
                                  'outpath',
                                  vars=overrides)
        out = paramsOut(outpath)
        
        if libpath == 'None':
            tool.libPathDir = config.get(config_section,
                                     'libpath',
                                     vars=overrides)
        else:
            tool.libPathDir =libpath
            
        if xslpath == 'None':
            tool.xslPathDir = config.get(config_section,
                                      'xslpath',
                                      vars=overrides)
        else:
            tool.xslPathDir = xslpath
        
        tool.python = config.get(config_section,
                                      'python',
                                      vars=overrides)
        
        tool.pyang = config.get(config_section,
                                      'pyang',
                                      vars=overrides)
        
        if debug == 'None':
            DEBUG = int(config.get(config_section,
                                      'DEBUG',
                                      vars=overrides))
        else:
            DEBUG = int(debug)
        #----------------------------------------------------------------------
        # Finally we have enough info to start a proper flow trace.
        #----------------------------------------------------------------------
        

        #----------------------------------------------------------------------
        # Log the details of the configuration.
        #----------------------------------------------------------------------
        logger.info('python path = {0}'.format(tool.python))
        logger.info('pyang path = {0}'.format(tool.pyang))
        logger.info('Log file = {0}'.format(log_file))
        logger.info('input path = {0}'.format(inpath))
        logger.info('output path = {0}'.format(out.outPathDir))
        logger.info('lib path = {0}'.format(tool.libPathDir))
        logger.info('xsl path = {0}'.format(tool.xslPathDir))
      

        #----------------------------------------------------------------------
        # Perform some basic error checking on the config.
#         #----------------------------------------------------------------------
#         if ():
#             logger.error('Invalid ****({0}).format(vel_port))
#             logger.warning('Invalid ****({0}).format(vel_port))
#                                              
#             raise RuntimeError('Invalid ****({0}).format(vel_port))
# 

        
        #----------------------------------------------------------------------
        # Load up the input path, if it exists.
        #----------------------------------------------------------------------
        if inpath == 'None':
            inpath = config.get(config_section,
                                      'inpath',
                                      vars=overrides)
      
        if not os.path.exists(inpath):
            logger.error('Specify the yang file or directory ({0}) not found. '
                           'No validation will be undertaken.'.format(inpath))
            raise RuntimeError('Invalid input the yang file or directory ({0}) '
                               'specified, please make sure it is exist!'.format(inpath))
        else:
            topMod, platMD, indexMD = checkTopModule(inpath)
            if not topMod:
                topModL, platMDL, indexMDL = checkTopModule(tool.libPathDir)
#                 print(topModL, platMDL, indexMDL)
#                 print(tool.libPathDir)
                if not topModL:
                    logger.error('Specify the gw-platform.yang and _index_.yang files not found in directory. ')
                    raise RuntimeError('Specify the gw-platform.yang and _index_.yang files not found in directory. ')
                else:
                    topModule = (platMDL, indexMDL)
            threads = []
            logger.debug('Loaded input file')
            yin = handleyin()
            originPath = None
            try:
                originPath = yin.handle(inpath)
            except Exception as e:
                return 1
            for xl in xslTruple:
                bucket = Queue.Queue()
                t = convertThread.catchThreadExcpetion(bucket, concurrentConvert,xl, originPath)
                threads.append(t)
#                 t.start()
#                 t.join()
#                 try:
#                     t = threading.Thread(target=concurrentConvert,args=(xl, originPath))
#                     threads.append(t)
#                 except Exception as e:
#                     return 1
            for t in threads:
                t.setDaemon(True)
                t.start()
#                 t.join(0.1)
                
            while 1:
#                 t.join()
                if len(threads) == 0:
                    break;
                for t in threads:
                    bucket = t.bucket
                    try:
                        exc = bucket.get(block=False)
                    except Queue.Empty:
                        pass
                    else:
                        exc_type, exc_obj, exc_trace = exc
                        # deal with the exception
                        logger.error(exc_obj)
#                         for t in threads:
#                             t.stop_thread(t)
                        raise RuntimeError(exc_obj)
                    
                    if t.isAlive():
                        continue
                    else:
                        threads.remove(t)
                        break
            if not DEBUG:
                removeAll().removeFileAndDir(originPath)
        end = time.time()
        
        print('\n Finished! This task took %f minutes' % float((end-start)/60))
        logger.info('Finished! This task took {0} minutes'.format(str(float((end-start)/60))))
        
        return 0

    except KeyboardInterrupt:
        #----------------------------------------------------------------------
        # handle keyboard interrupt
        #----------------------------------------------------------------------
        logger.info('Exiting on keyboard interrupt!')
        return 0

    except Exception as e:
        #----------------------------------------------------------------------
        # Handle unexpected exceptions.
        #----------------------------------------------------------------------
        if DEBUG or TESTRUN:pass
#             print(e)
#             raise(e)
        indent = len(program_name) * ' '
        sys.stderr.write(program_name + ': ' + repr(e) + '\n')
        sys.stderr.write(indent + '  for help use --help\n')
        if DEBUG:
            sys.stderr.write(traceback.format_exc())
        logger.critical('Exiting because of exception: {0}'.format(e))
        logger.critical(traceback.format_exc())
        print('\nFailed to convert yang!')
        logger.error('Failed to convert yang!')
        return 2
    
#------------------------------------------------------------------------------
# MAIN SCRIPT ENTRY POINT.
#------------------------------------------------------------------------------
if __name__ == '__main__':
    if TESTRUN:
        #----------------------------------------------------------------------
        # Running tests - note that doctest comments haven't been included so
        # this is a hook for future improvements.
        #----------------------------------------------------------------------
        import doctest
        doctest.testmod()

    if PROFILE:
        #----------------------------------------------------------------------
        # Profiling performance.  Performance isn't expected to be a major
        # issue, but this should all work as expected.
        #----------------------------------------------------------------------
        import cProfile
        import pstats
        profile_filename = 'convert2yang_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open('convert2yang_profile_stats.txt', 'wb')
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)

    #--------------------------------------------------------------------------
    # Normal operation - call through to the main function.
    #--------------------------------------------------------------------------
    sys.exit(main())
