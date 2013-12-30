//need:app/lib/view/cperfstoreValueConsumerWidget.js
/*
 * Copyright (c) 2011 "Capensis" [http://www.capensis.com]
 *
 * This file is part of Canopsis.
 *
 * Canopsis is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Canopsis is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with Canopsis.  If not, see <http://www.gnu.org/licenses/>.
 */

Ext.define('canopsis.lib.view.cwidgetGraph', {
	extend: 'canopsis.lib.view.cperfstoreValueConsumerWidget',

	logAuthor: '[widgets][graph]',
	layout: 'vbox',

	time_window: global.commonTs.day,
	time_window_offset: 0,

	initComponent: function() {
		this.callParent(arguments);

		this.setChartOptions();
		this.series = {};

		this.chart = undefined;

		this.on('boxready', this.createChart, this);
		this.on('resize', this.renderChart, this);
	},

	afterContainerRender: function() {
		this.callParent(arguments);

		if(this.chart !== undefined) {
			this.renderChart();
		}
	},

	setChartOptions: function() {
		var me = this;
		var now = Ext.Date.now();

		this.options = {
			cwidget: function() {
				return me;
			},

			crosshair: {
				mode: 'x'
			},

			selection: {
				mode: 'x'
			},

			grid: {
				borderWidth: {
					top: 0,
					bottom: 0,
					right: 0,
					left: 0
				},
				hoverable: true,
				clickable: true
			},

			xaxis: {
				min: now - this.time_window * 1000,
				max: now
			},
			yaxis: {},

			xaxes: [],
			yaxes: [],

			legend: {}
		};
	},

	createChart: function() {
		log.debug('Create chart:');
		log.dump(this.series);
		log.dump(this.options);

		this.plotcontainer = $('#' + this.wcontainerId);

		/* create the main chart */
		this.chart = $.plot(this.plotcontainer, this.getSeriesConf(), this.options);
	},

	renderChart: function() {
		log.debug('Rendering chart');

		this.chart.setData(this.getSeriesConf());
		this.chart.setupGrid();
		this.chart.draw();
	},

	destroyChart: function() {
		this.chart.destroy();
	},

	getSeriesConf: function() {
		var series = [];

		Ext.Object.each(this.series, function(serieId, serie) {
			series.push(serie);
		});

		return series;
	},

	getSerieForNode: function(nodeid) {
		var node = this.nodesByID[nodeid];

		var serie = {
			node: node,
			label: node.label,
			data: [],
			last_timestamp: -1,
			xaxis: 1,
			yaxis: node.yAxis,
		};

		return serie;
	},

	addPoint: function(serieId, value) {
		this.series[serieId].data.push(Ext.clone(value));
	},

	shiftSerie: function(serieId) {
		void(serieId);
		return;
	},

	doRefresh: function(from, to) {
		this.refreshNodes(from, to);
	},

	onRefresh: function(data, from, to) {
		this.callParent(arguments);

		log.debug('Received data:');
		log.dump(data);

		if(data.length > 0) {
			for(var i = 0; i < data.length; i++) {
				var info = data[i];
				var node = this.nodesByID[info.node];
				var serieId = info.node + '.' + node.metrics[0];

				/* create the serie if it doesn't exist */
				if(!(serieId in this.series) || this.series[serieId] === undefined) {
					log.debug('Create serie: ' + serieId);

					this.series[serieId] = this.getSerieForNode(info.node);
				}

				/* add data to the serie */
				for(var j = 0; j < info.values.length; j++) {
					var value = info.values[j];

					this.addPoint(serieId, value);
				}

				/* shifting serie */
				this.shiftSerie(serieId);
			}
		}

		if(this.reportMode || this.exportMode) {
			this.options.xaxis.min = from;
			this.options.xaxis.max = to;
		}
		else {
			this.options.xaxis.min = to - (this.time_window + this.time_window_offset) * 1000;
			this.options.xaxis.max = to - this.time_window_offset * 1000;
		}

		this.destroyChart();
		this.createChart();
		this.renderChart();
	}
});