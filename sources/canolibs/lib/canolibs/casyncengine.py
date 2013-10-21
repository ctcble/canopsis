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

import itertools

try:
	import threading
except ImportError as ie:
	import dummythreading as threading

ID = '_id'
RECORD_TYPE = 'crecord_type'
ENABLE = 'enable'
LOADED = 'loaded'

class record_processor(threading.Thread):
	"""
	Dedicated to process a set of records asynchronously with a parent casyncengine.
	"""

	"""
	Default thread sleeping value between two record processes.
	"""
	DEFAULT_SLEEP = 0.5

	def __init__(self, asyncengine, record_processing, sleep=DEFAULT_SLEEP):
		threading.Thread.__init__(self)

		self._records = []
		self._asyncengine = asyncengine
		self._lock = treading.Lock()
		self._record_processing = record_processing
		self._sleep = sleep
		self._run = True
		self._start()

	def add_record(self, record):
		"""
		Add a record to this record list
		"""
		self._lock.acquire()
		self._records.append(record)
		self._lock.release()

	def contains_record(self, record):
		"""
		Return True iif this contains record.
		"""
		self._lock.acquire()
		result = False
		_id = record.get(ID)
		for _record in self._records:
			if _record.get(ID) == _id:
				result = True
				break
		self._lock.release()
		return result

	def records_count(self):
		"""
		Returns records count.
		"""
		self._lock.acquire()
		result = len(self._records)
		self._lock.release()
		return result

	def run(self):
		"""
		Threaded function.
		Pop records from this record list and process them while this is running.
		"""
		while self._run:

			self._lock.acquire()
			records_count = len(self._records)
			self._lock.release()

			if records_count > 0:

				self._lock.acquite()
				record = self._records.pop(0)
				self._lock.release()
				self._record_processing(record)
				self._post_process_record(record)

			if records_count == 1 :
				time.sleep(self._sleep)

		self._records = []

	def _post_process_record(self, record):
		self.asyncengine.record_processor_has_processed_record(self, record)

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
			record_type,
			record_processing_sleep=recordprocessor.DEFAULT_SLEEP,
			next_amqp_queues=[],
			next_balanced=False,
			name="worker1",
			beat_interval=60,
			logging_level=logging.INFO,
			exchange_name='amq.direct',
			routing_keys=[],
			n_record_processors=DEFAULT_RECORD_PROCESSOR_COUNT):
		
		cengine.cengine.__init__(self, next_amqp_queues, next_balanced, name, beat_interval, logging_level, exchange_name, routing_keys)
	
		self._record_processing = record_processing
		self._n_record_processors = 0
		self.set_record_processor_count(n_record_processors)
		self._record_processing_sleep = record_processing_sleep
		self._record_type = record_type
		self._record_processors = [recordprocessor(record_processing=self._record_processing, sleep=record_processing_sleep)] * self._n_record_processors

	def beat(self):
		"""
		Every beat_interval, get records from database and give them to record_processors.
		"""
		records = self.storage.find({RECORD_TYPE: self._record_type, ENABLE: True}, namespace="object")		

		for record in self._records:
			if not self._is_record_processing(record):
				self._record_processors[0].add_record(record)
				self._update_record_processors()

	def _is_record_processing(self, record):
		for record_processor in self._record_processors:
			if record_processor.contains_record(record):
				return True
		return False

	def _update_record_processors(self):
		sorted(self._record_processors, cmp= lambda x, y: x.records_count() - y.records_count())
			
	def record_processor_has_processed_record(self, record_processor, record):
		"""
		Notify this an input record_processor has finished to process an input record.
		"""
		self._update_record_processors()

	def load_records(self):
		"""
		Load records in self._records
		"""
		self._records = []
		_records_json = self.storage.find({RECORD_TYPE: self._record_type, ENABLE: True}, namespace="object")
		
		for	_record_json in _records_json:
			# let say selector is loaded
			self.storage.update(_record_json._id, {LOADED: True})
			record = self.new_record(_record_json)
			self._records.append(record)

	def new_record(self, record):
		"""
		Create a new records related to an input record (c.f. case for cselector).
		"""
		return record

	def unload_records(self):
		"""
		Unload records of this type.
		"""
		records = self.storage.findAndModify(
			{ 
				'query': 
					{'$and': [{RECORD_TYPE: self._record_type }, { LOADED :True}]},
				'update':
					{ 'loaded': False }
			}
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
		if self._n_record_processors < count:
			for record_processor_index xrange(self._n_record_processors, count - self._n_record_processors):				
				record_processor = recordprocessor(record_processing=self._record_processing, sleep=record_processing_sleep)
				record_processor.stop()
				self._record_processors.append(record_processor)
		elif self._n_record_processors > count:
			for record_processor_index xrange(count, self._n_record_processors):
				record_processor = self._record_processors.pop()
				record_processor.stop()
		self._n_record_processors = count