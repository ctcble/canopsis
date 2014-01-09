#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import time
import logging

from ctools import parse_perfdata
from ctools import Str2Number
from datetime import datetime

from cengine import cengine
from camqp import camqp
from md5 import md5

from cstorage import get_storage
from caccount import caccount
import pymongo

NAME="perfstore2"

METRIC_CONTENT_LIMIT = 1000

class engine(cengine):
	def __init__(self, *args, **kargs):
		cengine.__init__(self, name=NAME, *args, **kargs)

		self.beat_interval = 10
		self.perfstore_cache = {}

	def create_amqp_queue(self):
		super(engine, self).create_amqp_queue()

	def pre_run(self):
		self.storage = get_storage(account=caccount(user='root', group='root'))
		self.backend = self.storage.get_backend('metrics')
		self.time = time.time()
		self.logger.setLevel(logging.DEBUG)
		self.event_count = 0

	def post_run(self):
		pass

	def beat(self):
		count = 0
		
		perfstore_cache = self.perfstore_cache
		self.perfstore_cache = {}
		for rk, metric in perfstore_cache:
			count += 1
			for item in perfstore_cache[(rk,metric)]:
				self.backend.save(item)
		self.logger.debug('metrics saved %s' % (count))

	def work(self, event, *args, **kargs):
		## Get perfdata
		perf_data = event.get('perf_data', None)
		perf_data_array = event.get('perf_data_array', [])

		if not perf_data_array:
			perf_data_array = []

		### Parse perfdata (old ugly csv style parsing)
		if perf_data:
			self.logger.debug(' + perf_data: %s', perf_data)

			try:
				perf_data_array = parse_perfdata(perf_data)

			except Exception, err:
				self.logger.error("Impossible to parse: %s ('%s')" % (perf_data, err))

		self.logger.debug(' + perf_data_array: %s', perf_data_array)

		### Add status informations
		if event['event_type'] in ['check', 'selector', 'sla']:
			state = int(event['state'])
			state_type = int(event['state_type'])
			state_extra = 0

			# Multiplex state
			cps_state = state * 100 + state_type * 10 + state_extra

			perf_data_array.append({
				"metric": "cps_state",
				"value": cps_state
			})
        
        # allow working on this uniq array
		event['perf_data_array'] = perf_data_array

        # Noothing else to do with this event perfdata empty
		if not perf_data_array:
			return event

		# Clean perfdata keys
		for index, perf_data in enumerate(event['perf_data_array']):
			new_perf_data = {}

			for key in perf_data:
				if perf_data[key] != None:
					new_perf_data[key] = perf_data[key]

			event['perf_data_array'][index] = new_perf_data

		"""
		metrics looks like :
		[ {'min': 0.0, 'metric': u'rta', 'value': 0.097, 'warn': 100.0, 'crit': 500.0, 'unit': u'ms'}, {'min': 0.0, 'metric': u'pl', 'value': 0.0, 'warn': 20.0, 'crit': 60.0, 'unit': u'%'} ]
        """

		for perf in perf_data_array:
			metric = perf['metric']
			value = perf['value']
            
			value = Str2Number(value)
			if value == None:
				self.logger.warning("Invalid value: '%s' (%s: %s)" % (value, event['rk'], metric))
				continue


			dtype = perf.get('type', None)
			unit = perf.get('unit', None)

			if unit:
				unit = str(unit)

			vmin  = perf.get('min', None)
			vmax  = perf.get('max', None)
			vwarn = perf.get('warn', None)
			vcrit = perf.get('crit', None)
			retention = perf.get('retention', None)

			if vmin:
				vmin = Str2Number(vmin)
			if vmax:
				vmax = Str2Number(vmax)
			if vwarn:
				vwarn = Str2Number(vwarn)
			if vcrit:
				vcrit = Str2Number(vcrit)

		

			self.logger.debug(" + Put metric '%s' (%s %s (%s))  @ timestamp %s ..." % (metric, value, unit, dtype, event['timestamp']))

			new_values = {
				'type'		: dtype,
				'min'		: vmin,
				'max'		: vmax,
				'thd_warn'	: vwarn,
				'thd_crit'	: vcrit,
				'co'		: event['component'],
				're'		: event['resource'],
				'unit'		: unit,
			}
			
			metric_info = {'rk': event['rk'], 'me': metric}
		
			# This dictionary is for metrics db selection purpose
			query = metric_info.copy()
			 
						
			# Gets previous metric information from db
			self.logger.debug('finding query : %s' % (metric_info))
			# This dictionary is for cache purposes
			if (event['rk'], metric) in self.perfstore_cache:
				last_values = self.perfstore_cache[(event['rk'], metric)][-1]
			else:
				self.perfstore_cache[(event['rk'], metric)] = []
				last_values = self.backend.find_one(metric_info, sort=[('ts_max', pymongo.DESCENDING)])

			# Dictionnary that will set mongodb document to new values
			keys_set = {'ts_max' : event['timestamp']}

			# Define whether or not a new document have to be insterted
			insert_document = True
			
			if not last_values:
				# No previous document exists for this metric
				last_values = metric_info
				self.logger.debug('no previous values found for identified metric. will create empty values')
			else:
				# Is previous document full
				if last_values['values_count'] < METRIC_CONTENT_LIMIT:
					# update query can retrieve 
					keys_set['_id'] 	= last_values['_id']
					insert_document = False

				else:
					# Then a new one is beeing created 
					last_values = metric_info


			for metric_key in new_values:
				# Is it an intersting key to store 
				if new_values[metric_key] != None:	
				 	# if no information about metric or size limit exeeded  new metric document id created 
					if metric_key not in last_values or last_values[metric_key] != new_values[metric_key]:
						# Keys to store
						keys_set[metric_key] = new_values[metric_key]
						
			str_timestamp = str(event['timestamp']).replace('.','')
	
			# Insert or update
			if insert_document:
				# Metric document meta information defined here

				keys_set['rk'] 		= event['rk']
				keys_set['me'] 		= metric
				keys_set['ts_min'] 	= event['timestamp']
				keys_set['value'] 	= {str_timestamp: value}	
				keys_set['values_count'] = 1
				self.backend.insert(keys_set)
				self.logger.debug('Metric values inserted')
				# add to cache
				self.perfstore_cache[(event['rk'], metric)].append(last_values)
			else:
						
				keys_set['value'][str_timestamp] = value
				keys_set['values_count'] += 1
				self.logger.debug('Metric values updated')


			self.logger.debug('last values updated for metric %s on document %s @ %s' % (metric, event['rk'], time.time() - self.time))
			self.event_count += 1
			
