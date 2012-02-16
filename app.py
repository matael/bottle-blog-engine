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
        HTTPError,\
        HTTPResponse

# Uncomment to run in a WSGI server
#os.chdir(os.path.dirname(__file__))

application = Bottle()
debug(True)

@application.route('/static/<filename:path>')
def static(filename):
    """ Serve static files """
    return static_file(filename, root='{}/static'.format(ROOT_PATH))


@application.error(500)
@application.error(404)
def errors(code):
    """ Handler for errors"""
    return template("templates/error.html", code=code)


@application.route('/')
def home():
    """ Homepage view """
    posts_list = os.listdir("{0}/posts/".format(ROOT_PATH))
    posts_list.sort()
    posts_list.reverse()
    reading = []
    contents_list = []
    for p in posts_list:
        current_file = open("posts/{}".format(p),'r')
        line = current_file.readline()
        while line!="\n":
            reading.append(line)
            line = current_file.readline()
        current_file.close()
        reading = yaml.load(''.join(reading))
        contents_list.append({'title':reading['title'],'url':re.sub(r'-','/',p).rstrip(".mkd"),'meta':reading})
        reading = []

    return template('templates/home.html', contents_list = contents_list)


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


@application.route('/c/<name>')
def view_category(name):
    """ List all articles published under a given category """
    matches = {'posts':[], 'breves':[]}# list of matching breves/posts
    reading = [] # just handy list for metadata reading

    # processing for posts
    for k in matches.keys():
        for f in os.listdir("{}/".format(k)):
            current_file = open("{}/{}".format(k,f),'r')
            line = current_file.readline()
            while line!="\n":
                reading.append(line)
                line = current_file.readline()
            current_file.close()
            reading = yaml.load(''.join(reading))
            if name in reading['tags']:
                (matches[k]).append((re.sub(r'-','/',f).rstrip('.mkd'),\
                                     (re.sub(r'\d+-\d+-\d+-','',f)).rstrip('.mkd')))
            reading = []
    if matches['posts'] == [] and matches['breves'] == []: # avoid strange behaviour when category isn't found
        return template("templates/category.html", category=name)
    return template("templates/category.html", category=name, matches=matches)


@application.route('/<name>')
def page_view(name):
    """ Return a markdown interpreted page """
    try:
        source_file = open("pages/{}.mkd".format(name),'r')
    except IOError: # means source_file does not exists
        raise HTTPError(404, output="The page you've requested does not exist")

    # processing and template
    return template("templates/page.html", content=markdown(source_file.read()), name=name)


def main():
    """ Run the application

    Use : 
        $ python app.py
    """
    run(application, host='0.0.0.0', port=8080)
    return 0

if __name__ == '__main__':
    main()

