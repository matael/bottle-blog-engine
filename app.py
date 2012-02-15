#!/usr/bin/env python
#-*- encoding: utf-8 -*-
from settings import *
import sys
import os
from markdown import markdown
from bottle import\
        Bottle,\
        run,\
        route,\
        jinja2_template as template,\
        static_file,\
        error,\
        debug,\
        request,\
        redirect

# Uncomment to run in a WSGI server
#os.chdir(os.path.dirname(__file__))

application = Bottle()
debug(True)

@application.route('/static/<filename:path>')
def static(filename):
    """ Serve static files """
    return static_file(filename, root='{}/static'.format(ROOT_PATH))


@application.route('/')
def home():
    """ Homepage view """
    posts_list = os.listdir("{0}/posts".format(ROOT_PATH))
    posts_list.sort()
    posts_list.reverse()
    return template('templates/home.html', posts_list=posts_list)


def main():
    run(application, host='0.0.0.0', port=8080)
    return 0

if __name__ == '__main__': main()

