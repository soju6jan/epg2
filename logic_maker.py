import os, sys, traceback, re, json, threading, time, shutil, platform
from datetime import datetime
from flask import request, render_template, jsonify, redirect

from .plugin import P, logger, package_name, ModelSetting, LogicModuleBase, scheduler, app, db
name = 'maker'
from .cli_make_sheet import CliMakeSheet
from .task_maker import Task

class LogicMaker(LogicModuleBase):
    db_default = {
        f'{name}_db_version' : '1',
        f'{name}_auto_start' : 'False',
        f'{name}_interval' : '120',
    }

    def __init__(self, P):
        super(LogicMaker, self).__init__(P, 'setting')
        self.name = name

    def process_menu(self, sub, req):
        arg = P.ModelSetting.to_dict()
        arg['sub'] = self.name
        try:
            arg['scheduler'] = str(scheduler.is_include(self.get_scheduler_name()))
            arg['is_running'] = str(scheduler.is_running(self.get_scheduler_name())) 
            return render_template(f'{package_name}_{name}_{sub}.html', arg=arg)
        except Exception as e:
            logger.error(f'Exception:{str(e)}')
            logger.error(traceback.format_exc())
            return render_template('sample.html', title=f"{package_name}/{name}/{sub}")

        
    def process_ajax(self, sub, req):
        try:
            ret = {}
            logger.debug(sub)
            logger.debug(req)
            if sub == 'command':
                command = req.form['command']
                logger.debug(command)
                if command == 'sheet':
                    ins = CliMakeSheet()
                    arg1 = req.form['arg1']
                    method_to_call = getattr(ins, arg1)
                    result = method_to_call()
                    logger.debug("종료")
            return jsonify(ret)
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            return jsonify({'ret':'danger', 'msg':str(e)})
    
    def scheduler_function(self):
        def func():
            
            func = Task.start
            time.sleep(1)
            if app.config['config']['use_celery']:
                result = Task.start.apply_async()
                ret = result.get()
            else:
                ret = Task.start()
        th = threading.Thread(target=func, args=())
        th.setDaemon(True)
        th.start()
        th.join()
    
    def plugin_load(self):
        data_db_default = {
            'updated_time' : ''
        }
        for key, value in data_db_default.items():
            if db.session.query(self.P.ModelSettingDATA).filter_by(key=key).count() == 0:
                db.session.add(self.P.ModelSettingDATA(key, value))

    #########################################################

    