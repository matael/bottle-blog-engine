#!/usr/bin/env python
#-*- encoding: utf-8 -*-
from settings import *
import sys
import os
import codecs
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
        HTTPResponse,\
        response

#Uncomment to run in a WSGI server
#os.chdir(os.path.dirname(__file__))

application = Bottle()
debug(True)

def create_url(filename):
    """ Extract a correct URL from a filename """
    fragments = (filename.rstrip('.mkd')).split('-')
    url = '{}/{}'.format('/'.join(fragments[:3]),'-'.join(fragments[3:]))
    return url


@application.route('/static/<filename:path>')
def static(filename):
    """ Serve static files """
    print 'Root: {}/static/'.format(ROOT_PATH)
    print 'Filename: {}'.format(filename)
    return static_file(filename, root='{}/static/'.format(ROOT_PATH))


@application.error(500)
@application.error(404)
def errors(code):
    """ Handler for errors"""
    print 'Error: %s' % code
#    return 'Oops, something went wrong...'
    return template("templates/error.html", code=code)


@application.route('/')
def home():
    """ Homepage view """
    contents_lists = {'posts':[], 'breves':[]}
    for k in contents_lists.keys():
        items_list = os.listdir(k)
        items_list.sort()
        items_list.reverse()
        reading = []
        for i in items_list[:HOMEPAGE_LIMIT]:
            current_file = codecs.open("{}/{}".format(k,i),'r', encoding='utf8')
            line = current_file.readline()
            while line!="\n":
                reading.append(line)
                line = current_file.readline()
            reading = yaml.load(''.join(reading))
            reading['url'] = create_url(i)
            line = current_file.readline()
            slug = []
            while line!="~\n":
                slug.append(line)
                line = current_file.readline()
            reading['slug'] = markdown(''.join(slug))
            current_file.close()
            (contents_lists[k]).append(reading)
            reading = []

    return template('templates/home.html', contents_lists = contents_lists)


@application.route('/<type:re:[p|b]>/<month:int>/<day:int>/<year:int>/<name>')
def view_post(type, day, month, year, name):
    """ Returns a post identified by its name above """
    filename = "{}-{}-{}-{}.mkd".format(str(month).zfill(2),str(day).zfill(2),str(year).zfill(2),name)

    # type of content determination
    if type == 'p': type='post'
    else: type='breve'

    # source file fetching & processing
    try:
        source_file = codecs.open("{}s/{}".format(type,filename),'r', encoding='utf8')
        text = source_file.readlines()
        source_file.close()
    except IOError: # means source_file does not exists
        raise HTTPError(404, output="The post you've requested does not exist")
    meta_brut = []
    line = text[0]
    while line != "\n":
        meta_brut.append(text.pop(0))
        line = text[0]
    meta = yaml.load(''.join(meta_brut))
#    meta['date'] = FORMAT_DATE.format(month, day, year)
    text.pop(text.index("~\n"))
    text = markdown(''.join(text))

    # output
    return template('templates/{}.html'.format(type), text=text, meta=meta, disqus=DISQUS)


@application.get('/post')
def new_post():
    return template('templates/new.html')

@application.post('/post')
def do_post():
    expected_username   = ADMIN_USERNAME
    expected_password   = ADMIN_PASSWORD
    supplied_username   = request.forms.get('username')
    supplied_password   = request.forms.get('password')
    supplied_title      = request.forms.get('title')
    supplied_author     = request.forms.get('author')
    supplied_tags       = request.forms.get('tags')
    supplied_summary    = request.forms.get('summary')
    supplied_markdown   = request.forms.get('content')

    if not expected_username or not expected_password:
        raise Exception('Invalid server configuration. Unable to continue.')
    else:
        if supplied_username == expected_username and supplied_password == expected_password:
            from datetime import datetime
            now = datetime.now()
            yaml_filename = now.strftime("%Y-%m-%d_%H-%M.yml")
            markdown_filename = now.strftime("%Y-%m-%d_%H-%M.mkd")
            post_date = now.strftime(DATE_FORMAT)
            response.content_type = 'text/plain; charset=UTF8'
            post_data = {
                'title'     : supplied_title,
                'author'    : supplied_author,
                'date'      : post_date,
                'tags'      : supplied_tags,
                'summary'   : supplied_summary,
                'content'   : markdown_filename
            }
            yaml_data = yaml.dump(post_data,default_flow_style=False)
            return '{}:\n{}\n\n{}:\n{}'.format(yaml_filename,yaml_data,markdown_filename,supplied_markdown)
            #return 'Title: {}\nAuthor: {}\nDate:{}\nTags:{}\n\nContent:\n{}'.format(supplied_title,supplied_author,supplied_date,supplied_tags,supplied_content)
        else:
            return 'Invalid username or password.'

@application.route('/c/<name>')
def view_category(name):
    """ List all articles published under a given category """
    matches = {'posts':[], 'breves':[]}# list of matching breves/posts
    reading = [] # just handy list for metadata reading

    # processing
    for k in matches.keys():
        for f in os.listdir("{}/".format(k)):
            current_file = codecs.open("{}/{}".format(k,f),'r', encoding='utf8')
            line = current_file.readline()
            while line!="\n":
                reading.append(line)
                line = current_file.readline()
            current_file.close()
            reading = yaml.load(''.join(reading))
            try:
                if name in reading['tags']:
                    (matches[k]).append((re.sub(r'-','/',f).rstrip('.mkd'),\
                                         (re.sub(r'\d+-\d+-\d+-','',f)).rstrip('.mkd')))
            except KeyError:
                pass
            reading = []
    if matches['posts'] == [] and matches['breves'] == []: # avoid strange behaviour when category isn't found
        return template("templates/category.html", category=name)
    return template("templates/category.html", category=name, matches=matches)


@application.route('/<name>')
def page_view(name):
    """ Return a markdown interpreted page """
    try:
        source_file = codecs.open("pages/{}.mkd".format(name),'r', encoding='utf8')
    except IOError: # means source_file does not exists
        raise HTTPError(404, output="The page you've requested does not exist")

    # processing and template
    return template("templates/page.html", content=markdown(source_file.read()), name=name)


@application.route('/archives')
def archives():
    """ Power an archive page """
    contents_lists = {'posts':[], 'breves':[]}
    for k in contents_lists.keys():
        items_list = os.listdir(k)
        items_list.sort()
        items_list.reverse()
        reading = []
        for i in items_list:
            current_file = codecs.open("{}/{}".format(k,i),'r', encoding='utf8')
            line = current_file.readline()
            while line!="\n":
                reading.append(line)
                line = current_file.readline()
            reading = yaml.load(''.join(reading))
            reading['url'] = create_url(i)
            current_file.close()
            (contents_lists[k]).append(reading)
            reading = []

    return template('templates/archives.html', contents_lists = contents_lists)



def main():
    """ Run the application

    Use : 
        $ python app.py
    """
    run(application, host='0.0.0.0', port=8080)
    return 0

if __name__ == '__main__':
    main()

