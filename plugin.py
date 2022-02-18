import os, sys, traceback, re
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, redirect
from framework import app, path_data, path_app_root, db, scheduler, SystemModelSetting, socketio, celery, get_logger
from plugin import LogicModuleBase, get_model_setting, Logic, default_route, PluginUtil

EPG_DATA_DB_BIND_KEY = 'epg2_data'

class P(object):
    package_name = __name__.split('.')[0]
    logger = get_logger(package_name)
    blueprint = Blueprint(package_name, package_name, url_prefix=f'/{package_name}', template_folder=os.path.join(os.path.dirname(__file__), 'templates'), static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    menu = {
        'main' : [package_name, u'EPG v2'],
        'sub' : [
            #['user', 'User'], ['maker', 'Maker'], ['manual', '매뉴얼'], ['log', u'로그']
            ['user', 'User'], ['maker', 'Maker'], ['log', u'로그']
        ], 
        'category' : 'tv',
        'sub2' : {
            'user' : [
                ['setting', '설정']
            ],
            'maker' : [
                ['setting', '설정']
            ],
            #'manual' : [
            #    ['README.md', 'README']
            #],
        }
    }  

    plugin_info = {
        'version' : '1.0.0.0',
        'name' : package_name,
        'category' : menu['category'],
        'icon' : '',
        'developer' : u'soju6jan',
        'description' : u'EPG',
        'home' : f'https://github.com/soju6jan/{package_name}',
        'more' : '',
    }
    ModelSetting = get_model_setting(package_name, logger)
    ModelSettingDATA = get_model_setting(EPG_DATA_DB_BIND_KEY, logger)
    logic = None
    module_list = None
    home_module = 'user'

    
from tool_base import d
logger = P.logger
package_name = P.package_name
ModelSetting = P.ModelSetting


def initialize():
    try:
        if os.path.exists(os.path.join(os.path.dirname(__file__), 'file', 'cred')) == False:
            del P.menu['sub'][1]

        app.config['SQLALCHEMY_BINDS'][P.package_name] = 'sqlite:///%s' % (os.path.join(path_data, 'db', '{package_name}.db'.format(package_name=P.package_name)))
        app.config['SQLALCHEMY_BINDS'][EPG_DATA_DB_BIND_KEY] = 'sqlite:///%s' % (os.path.join(os.path.dirname(__file__), 'file', f'{EPG_DATA_DB_BIND_KEY}.db'))

        PluginUtil.make_info_json(P.plugin_info, __file__)

        from .logic_user import LogicUser
        from .logic_maker import LogicMaker
        P.module_list = [LogicUser(P), LogicMaker(P)]
        P.logic = Logic(P)
        default_route(P)
    except Exception as e: 
        P.logger.error(f'Exception:{str(e)}')
        P.logger.error(traceback.format_exc())

initialize()

