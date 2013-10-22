#!/usr/bin/env python
#--------------------------------
# Copyright (c) 2013 "Capensis" [http://www.capensis.com]
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

import multiprocessing
import time
import Queue
import logging
import os, sys
from cinit import cinit
import traceback
import cevent
import cengine
from cstorage import get_storage
from caccount import caccount

import itertools

try:
	import threading
except ImportError as ie:
	import dummythreading as threading

ID = '_id'
RECORD_TYPE = 'crecord_type'
ENABLE = 'enable'
LOADED = 'loaded'

class recordprocessor(threading.Thread):
	"""
	Dedicated to process a set of records asynchronously with a parent casyncengine.
	"""

	"""
	Default thread sleeping value between two record processes.
	"""
	DEFAULT_SLEEP = 0.1
	DEFAULT_RECORD_COUNT_PER_PROCESSING = 3

	def __init__(self, asyncengine, record_processing, record_count_per_processing=DEFAULT_RECORD_COUNT_PER_PROCESSING, sleep=DEFAULT_SLEEP):
		threading.Thread.__init__(self)
		
		self._asyncengine = asyncengine		
		self._record_processing = record_processing
		self._record_count_per_processing = record_count_per_processing
		self._sleep = sleep

		self._run = True
		self.start()

	def set_record_processing_count_per_processing(self, record_count_per_processing):
		self._record_count_per_processing = record_count_per_processing

	def run(self):
		"""
		Threaded function.
		Pop records from this record list and process them while this is running.
		"""
		while self._run:
			
			records = self._asyncengine.pop_records(self._record_count_per_processing)

			if len(records) > 0:
				for record in records:							
					self._record_processing(record)
					self.asyncengine.processed_record(self, record)
			else:
				time.sleep(self._sleep)		

	def stop(self):
		"""
		Stop this process.
		"""
		self._run = False

class casyncengine(cengine.cengine):
	"""
	Engine specialised in asynchronous record processing. Manages a list of record_processors with one record processing function.
	Records to process are given equally to processors.
	The number of processors is modifiable at runtime.
	"""

	DEFAULT_RECORD_PROCESSOR_COUNT = 1

	def __init__(self,
			record_processing,
			record_type_name,
			record_processing_sleep=recordprocessor.DEFAULT_SLEEP,
			record_processor_count=DEFAULT_RECORD_PROCESSOR_COUNT,
			next_amqp_queues=[],
			next_balanced=False,
			name="worker1",
			beat_interval=60,
			logging_level=logging.INFO,
			exchange_name='amq.direct',
			routing_keys=[]):
		
		cengine.cengine.__init__(self, next_amqp_queues, next_balanced, name, beat_interval, logging_level, exchange_name, routing_keys)
	
		self._lock = threading.Lock()
		self._records = []
		self._record_processing = record_processing
		self._record_processing_sleep = record_processing_sleep
		self._record_type_name = record_type_name		
		self._record_processors = []
		self.set_record_processor_count(record_processor_count)

		self._processed_records = self._beat_processed_records = 0

	def pre_run(self):
		self.storage = get_storage(namespace='object', account=caccount(user="root", group="root"))

	def pop_records(self, count=1):
		"""
		Return poped records.
		"""		
		
		result = []

		if count == -1 :
			count = len(self._records)
		self._lock.acquire()
		result = self._records[0: count]
		self._records = self._records[count:]
		self._lock.release()
		
		return result

	def beat(self):
		"""
		Every beat_interval, get records from database and give them to record_processors.
		"""
		self._beat_processed_records = 0
		self.load_records()
	
	def processed_record(self, record_processor, record):
		"""
		Notify this an input record_processor has finished to process an input record.
		"""
		self._processed_records += 1
		self._beat_processed_records += 1		

	def load_records(self):
		"""
		Load records in self._records
		"""
		_records_json = self.storage.find({RECORD_TYPE: self._record_type_name, ENABLE: True}, namespace="object")
		
		for	_record_json in _records_json:
			# let say selector is loaded
			self.storage.update(_record_json._id, {LOADED: True})
			record = self._get_record(_record_json)
			sel._try_to_add_record(record)
			
	def _try_to_add_record(self, record):
		_id = record.get(ID)
		toAdd = True
		self._lock.acquire()
		for _record in self._records:
			if _record.get(ID)==_id:
				toAdd = False
				break
		if toAdd:
			self._records.append(record)
		self._lock.release()

	def _get_record(self, record):
		"""
		Create a new records related to an input record (c.f. case for cselector).
		"""
		return record

	def unload_records(self):
		"""
		Unload records of this type.
		"""
		self.storage.findAndModify(
			{ 
				'query': 
					{'$and': [{RECORD_TYPE: self._record_type_name }, { LOADED :True}]},
				'update':
					{ 'loaded': False }
			},
			namespace="object")
		self.logger.debug('%i configuration unloaded' % len(records))

	def post_run(self):
		"""
		Unload records at the end of run function.
		"""
		self.unload_records()

	def set_record_processor_count(self, count):
		"""
		Change the record processors list size.
		"""
		if count < 1:
			raise Exception('new record processor count must be greater than 0: %s' % count)
		record_processor_count = len(self._record_processors)
		if record_processor_count < count:
			for record_processor_index in xrange(record_processor_count, count - record_processor_count):				
				record_processor = recordprocessor(asyncengine=self, record_processing=self._record_processing, sleep=self._record_processing_sleep)
				record_processor.stop()
				self._record_processors.append(record_processor)
		elif record_processor_count > count:			
			for record_processor_index in xrange(record_processor_count - count):
				record_processor = self._record_processors.pop()
				record_processor.stop()

	def get_record_processors(self):
		return self._record_processors