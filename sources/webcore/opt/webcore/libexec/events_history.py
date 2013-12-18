#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --------------------------------
# Copyright (c) 2011 "Capensis" [http://www.capensis.com]
#
# This file is part of Canopsis.
#
# Canopsis is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Canopsis is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Canopsis.  If not, see <http://www.gnu.org/licenses/>.
# ---------------------------------

import sys
import os
import logging
import json
import gevent
from datetime import datetime
from dateutil.rrule import *
from time import mktime as mktime

import bottle
from bottle import route, get, delete, put, request
from bottle import HTTPError, post, static_file, response

logger = logging.getLogger('events_history')

from libexec.rest import *

#########################################################################

@get('/events_history/:start/:stop')
def events_history_route(start, stop):
	print "events_history_route"
	return events_history(	start=start,
							stop=stop,
							filter=request.params.get('filter', default=None))

def events_history(start, stop, filter):
	print "event history@begin"

	if filter is None:
		filter_events = "{'event_type': { '$nin' : ['calendar','check'] } }"
		filter_events_history = "{'event_type': { '$in' : ['calendar','check'] } } } }"
	else:
		filter_events = "{ $and { %s , {'event_type': { '$nin' : ['calendar','check'] } } } }".format(filter)
		filter_events_history = "{ $and { %s , {'event_type': { '$in' : ['calendar','check'] } } } }".format(filter)

	history_request = rest_get("events_history", filter=filter_events_history)
	events_request = rest_get("events", filter=filter_events)

	print "event history1"
	print history_request
	print "event history2"
	print events_request


# http://stackoverflow.com/questions/14463087/is-it-possible-rename-fields-in-the-outputs-of-a-mongo-query-in-pymongo
# db.article.aggregate(
# { $project : {
#     title : 1 ,
#     page_views : "$pageViews" ,
#     bar : "$other.foo"
# }} );`
	#requeter events en transformant _id en rk
	#requeter history
	#joindre les 2 tableaux