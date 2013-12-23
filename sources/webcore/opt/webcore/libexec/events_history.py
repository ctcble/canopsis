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
	print start
	print stop
	return events_history(	start=start,
							stop=stop,
							filter=request.params.get('filter', default=None))

def events_history(start, stop, filter):
	def add_start_stop_params_to_filter(filter, start, stop):
		print "add_start_stop_params_to_filter"

		print start
		print stop

		start = int(start)
		stop = int(stop)

		filter = json.loads(filter)
		print "load ok"
		if filter.keys()[0] == "$and":
			filter["$and"].append({"timestamp": { "$gt": start }})
			filter["$and"].append({"timestamp": { "$lt": stop }})
			return json.dumps(filter)
		else:
			new_filter = { "$and" : []}
			new_filter["$and"].append(filter)
			new_filter["$and"].append({"timestamp": { "$gt": start }})
			new_filter["$and"].append({"timestamp": { "$lt": stop }})
			return json.dumps(new_filter)

	if filter is None:
		filter_events = '{"event_type": { "$nin" : ["calendar","check"] } }'
		filter_events_history = '{"event_type": { "$in" : ["calendar","check"] } }'
		filter_events = add_start_stop_params_to_filter(filter_events, start, stop)
		filter_events_history = add_start_stop_params_to_filter(filter_events_history, start, stop)
	else:
		filter_events = '{ "$and" : [ {"event_type": { "$nin" : ["calendar","check"] } }, ' + filter + ' ] }'
		filter_events_history = '{ "$and" : [ {"event_type": { "$in" : ["calendar","check"] } }, ' + filter + ' ] }'
		filter_events = add_start_stop_params_to_filter(filter_events, start, stop)
		filter_events_history = add_start_stop_params_to_filter(filter_events_history, start, stop)


	print filter_events
	print filter_events_history

	events_request = rest_get("events", filter=filter_events)
	history_request = rest_get("events_history", filter=filter_events_history)

	for event in history_request["data"]:
		event["rk"]
		# del event["rk"]
		events_request["data"].append(event)

	events_request["total"] += history_request["total"]
	print events_request["total"]

	return events_request