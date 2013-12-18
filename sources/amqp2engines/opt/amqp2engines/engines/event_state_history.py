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
from caccount import caccount
from crecord import crecord
from cstorage import get_storage

import cevent
import logging
import threading

NAME='event_state_history'

class engine(cengine):
	"""
		Event state history engine.
		this engine stores the event permanently when its status changes. This allows to get every changes that happened to an event from the API.
	"""

	def __init__(self, *args, **kwargs):
		super(engine, self).__init__(name=NAME, *args, **kwargs)

		self.account = caccount(user='root', group='root')
		self.storage = get_storage(namespace='events_history', logging_level=logging.DEBUG, account=self.account)

	def beat(self):
		pass

	def work(self, event, *args, **kwargs):
		event_types = ['calendar','check']

		if event["event_type"] in event_types:
			stored_event = event
			stored_event["rk"] = stored_event["_id"]
			stored_event.pop("_id", None)

			#TODO state type soft or hard in configuration

			self.storage.put(crecord(stored_event))

		return event
