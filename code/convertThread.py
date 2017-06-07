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


import threading,traceback,sys  
import inspect
import ctypes
  
class catchThreadExcpetion(threading.Thread): 
    '''The timer class is derived from the class threading.Thread'''  
    def __init__(self, bucket, funcName, *args):  
        threading.Thread.__init__(self)  
        self.args = args  
        self.funcName = funcName  
        self.exitcode = 0  
        self.bucket = bucket
        self.exception = None  
        self.exc_traceback = ''  
      
    def run(self): 
        '''Overwrite run() method, put what you want the thread do here'''  
        try:  
            self._run()  
        except Exception as e:  
            self.exitcode = 1       
            self.exception = e  
            self.exc_traceback = ''.join(traceback.format_exception(*sys.exc_info()))
            self.bucket.put(sys.exc_info())
      
    def _run(self):  
        try:  
            self.funcName(*(self.args))   
        except Exception as e:  
            raise e 
        
     
    def _async_raise(self,tid, exctype):
        """raises the exception, performs cleanup if needed"""
        tid = ctypes.c_long(tid)
        if not inspect.isclass(exctype):
            exctype = type(exctype)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise SystemError("PyThreadState_SetAsyncExc failed") 
    
    def stop_thread(self,thread):
        self._async_raise(thread.ident, SystemExit)