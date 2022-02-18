import os, sys, traceback, re, json, threading, time, shutil, platform
from datetime import datetime
from flask import request, render_template, jsonify, redirect, send_file

from .plugin import P, logger, package_name, ModelSetting, LogicModuleBase, scheduler, app, SystemModelSetting, path_data
name = 'user'
from .task_xml import Task

class LogicUser(LogicModuleBase):
    db_default = {
        f'{name}_db_version' : '1',
        f'{name}_auto_start' : 'False',
        f'{name}_interval' : '120',
        f'{name}_updated_tvheadend' : 'No File',
        f'{name}_updated_klive' : 'No File',
        f'{name}_updated_hdhomerun' : 'No File',
    }

    def __init__(self, P):
        super(LogicUser, self).__init__(P, 'setting')
        self.name = name

    def process_menu(self, sub, req):
        arg = P.ModelSetting.to_dict()
        arg['sub'] = self.name
        try:
            ddns = SystemModelSetting.get('ddns')  
            arg['ddns'] = ddns
            apikey = None
            if SystemModelSetting.get_bool('auth_use_apikey'):
                apikey = SystemModelSetting.get('auth_apikey')
            for tmp in ['tvheadend', 'klive', 'hdhomerun', 'all']:
                arg[tmp] = f'{ddns}/{package_name}/api/{name}/{tmp}'
                if apikey is not None:
                    arg[tmp] += '?apikey=' + apikey

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
            if sub == 'command':
                command = req.form['command']
                logger.debug(command)
                if command == 'make':
                    self.task_interface(req.form['arg1'], 'manual')
                    ret = {'ret':'success', 'msg':'생성을 시작합니다.'}
            return jsonify(ret)
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            return jsonify({'ret':'danger', 'msg':str(e)})
    
    def process_api(self, sub, req):
        try:
            if sub == 'all':
                filename = os.path.join(os.path.dirname(__file__), 'file', f'xmltv_{sub}2.xml')
            else:
                filename = os.path.join(path_data, 'output', f'xmltv_{sub}2.xml')
            if not os.path.exists(filename):
                LogicNormal.make_xml(sub)
            logger.warning(filename)
            return send_file(filename, mimetype='application/xml')
        except Exception as e: 
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            

    def scheduler_function(self):
        th = self.task_interface('all', 'scheduler')        
        th.join()

    #########################################################

    def task_interface(self, *args):
        def func(*args):
            func = Task.start
            time.sleep(1)
            if app.config['config']['use_celery']:
                result = Task.start.apply_async(args)
                ret = result.get()
            else:
                ret = Task.start(args)
        th = threading.Thread(target=func, args=args)
        th.setDaemon(True)
        th.start()
        return th
        #th.join()

        logger.warning(args)
        
