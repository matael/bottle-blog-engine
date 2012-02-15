#!/usr/bin/env python
#-*- encoding: utf-8 -*-
from settings import *
import sys
import os
import yaml
import re
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
        redirect,\
        HTTPError

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
    posts_list = os.listdir("{0}/posts/".format(ROOT_PATH))
    posts_list.sort()
    posts_list.reverse()
    return template('templates/home.html', posts_list=posts_list)


@application.route('/<type:re:[p|b]>/<month:int>/<day:int>/<year:int>/<name>')
def view_post(type, day, month, year, name):
    """ Returns a post identified by its name above """
    filename = "{}-{}-{}-{}.mkd".format(month,day,year,name)

    # type of content determination
    if type == 'p': type='post'
    else: type='breve'

    # source file fetching & processing
    try:
        source_file = open("{}s/{}".format(type,filename),'r')
    except IOError: # means source_file does not exists
        raise HTTPError(404, output="The post you've requested does not exist")
    meta_brut = []
    line = source_file.readline()
    while line != "\n":
        meta_brut.append(line)
        line = source_file.readline()
    meta = yaml.load(''.join(meta_brut))
    text = markdown(re.sub(r'~\n', '', source_file.read()))
    source_file.close()
   
    # output
    return template('templates/{}.html'.format(type), text=text, meta=meta)



def main():
    """ Run the application

    Use : 
        $ python app.py
    """
    run(application, host='0.0.0.0', port=8080)
    return 0

if __name__ == '__main__':
    main()

