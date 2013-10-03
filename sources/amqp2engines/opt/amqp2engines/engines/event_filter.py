#!/usr/bin/env python
#--------------------------------
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

from cengine import cengine
from cengine import DROP

from caccount import caccount
from cstorage import get_storage
import cevent
import logging
import cmfilter
import ast

import time
from datetime import datetime



NAME='event_filter'

class engine(cengine):

	def __init__(self, *args, **kargs):
		cengine.__init__(self, name=NAME, *args, **kargs)
		self.account = caccount(user="root", group="root")


	def pre_run(self):
		self.drop_event_count = 0
		self.pass_event_count = 0
		self.beat()


	def work(self, event, *xargs, **kwargs):		

		default_action = 'pass'

		event_str = str(event)

		default_action = self.configuration.get('default_action', 'pass')

		#When list configuration then check black and white lists depending on json configuration
		for filterItem in self.configuration.get('rules', []):

			action = filterItem.get('action')

			name = filterItem.get('name', 'no_name')
		
			# Try filter rules on current event
			if cmfilter.check(filterItem['mfilter'], event):
				if action == 'pass':
					self.logger.debug("Event '%s' passed by rule '%s'" % (event_str, name))
					self.pass_event_count += 1
					return event

				elif action == 'drop':
					self.logger.debug("Event '%s' dropped by rule '%s'" % (event_str, name))
					self.drop_event_count += 1
					return DROP

				else:
					self.logger.warning("Unknown action '%s'" % action)
	
		# No rules matched
		if default_action == 'drop':
			self.logger.debug("Event '%s' dropped by default action" % (event_str))
			self.drop_event_count += 1
			return DROP
		
		self.logger.debug("Event '%s' passed by default action" % (event_str))
		self.pass_event_count += 1

		return event
		

	def beat(self, *args, **kargs):
		# Configuration reload for realtime ui changes handling

		self.configuration = { 'rules' : [], 'default_action': 'pass'}

		self.storage = get_storage(logging_level=logging.DEBUG, account=self.account)	
		try:
			records = self.storage.find({'crecord_type':'rule'}, sort="priority")

			for record in records:
				record_dump = record.dump()
				record_dump["mfilter"] = ast.literal_eval(record_dump["mfilter"])
				self.configuration['rules'].append(record_dump)

			self.send_stat_event()

		except Exception, e:
			self.logger.warning(str(e))

	def send_stat_event(self):
	# Send AMQP Event for drop metrics
		event = cevent.forger(
			connector = "cengine",
			connector_name = "engine",
			event_type = "check",
			source_type="resource",
			resource=self.amqp_queue + '_data',
			state=0,
			state_type=1,
			output="%s event dropped since %s" % (self.drop_event_count, self.beat_interval),
			perf_data_array=[
								{'metric': 'drop_event' , 'value': self.drop_event_count, 'type': 'COUNTER' },
								{'metric': 'pass_event' , 'value': self.pass_event_count, 'type': 'COUNTER' }
							]
		)

		rk = cevent.get_routingkey(event)
		self.amqp.publish(event, rk, self.amqp.exchange_name_events)

		self.drop_event_count = 0				
		self.pass_event_count = 0