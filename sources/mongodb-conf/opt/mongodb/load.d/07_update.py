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

import math
from cstorage import get_storage
from caccount import caccount
from datetime import timedelta

logger = None
root = caccount(user="root", group="root")
storage = get_storage(account=root, namespace='object')

def init():
	logger.info(' + init')

def update():
	init()
	update_schedule()

def update_schedule():

	records = storage.find({'crecord_type': 'schedule'}, namespace='object', account=root)
	for record in records:
		kwargs = record.data['kwargs']
		cron = record.data['cron']

		#--mail
		if 'mail' in kwargs:
			mail = kwargs['mail']
			if mail:
				if 'sendMail' in mail and mail['sendMail']:
					record.data['exporting_mail'] = True
				if 'recipients' in mail:
					record.data['exporting_recipients'] = mail['recipients']
				if 'subject' in mail:
					record.data['exporting_subject'] = mail['subject']

		#--kwargs
		if 'account' in kwargs:
			record.data['exporting_account'] = kwargs['account']

		if 'task' in kwargs:
			record.data['exporting_task'] = kwargs['task']

		if 'method' in kwargs:
			record.data['exporting_method'] = kwargs['method']

		if 'owner' in kwargs:
			record.data['exporting_owner'] = kwargs['owner']

		if 'viewname' in kwargs:
			kwargs['viewName'] = kwargs['viewname']
			record.data['exporting_viewName'] = kwargs['viewname']
			del kwargs['viewname']

		if 'starttime' in kwargs:
			del kwargs['starttime']

		#if 'hour' in cron and 'minute':
		#	record.data['crontab_hours'] = '%i:%02d' % (int(cron['hour']),int(cron['minute']))

		if 'day_of_week' in cron:
			record.data['crontab_day_of_week'] = cron['day_of_week']

		if 'day' in cron:
			record.data['crontab_day'] = cron['day']

		if 'mouth' in cron:
			record.data['crontab_month'] = cron['month']

		if "every" in record.data:
			record.data['frequency'] = record.data['every']
			del record.data['every']

		if 'interval' in kwargs and kwargs['interval']:
			nbDays = timedelta(seconds=kwargs['interval']).days

			if nbDays >= 365:
				record.data['exporting_intervalLength'] = 31557600
				record.data['exporting_intervalUnit'] = int(nbDays/365)
			elif nbDays >= 30:
				record.data['exporting_intervalLength'] = 2629800
				record.data['exporting_intervalUnit'] = int(nbDays/30)
			elif nbDays >= 7:
				record.data['exporting_intervalLength'] = 604800
				record.data['exporting_intervalUnit'] = int(nbDays/7)
			else:
				record.data['exporting_intervalLength'] = 86400
				record.data['exporting_intervalUnit'] = math.floor(nbDays)

			record.data['exporting_interval'] = True

		record.data['kwargs'] = kwargs
		storage.put(record)