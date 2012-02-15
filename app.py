#!/usr/bin/env python
#-*- encoding: utf-8 -*-
import sys
import os
from markdown import markdown
from bottle import\
        Bottle,\
        run,\
        route,\
        template,\
        static_file,\
        error,\
        debug,\
        request,\
        redirect

# Uncomment to run in a WSGI server
#os.chdir(os.path.dirname(__file__))

application = Bottle()
debug(True)    


def main():
    run(application, host='0.0.0.0', port=8080)
    return 0

if __name__ == '__main__': main()

