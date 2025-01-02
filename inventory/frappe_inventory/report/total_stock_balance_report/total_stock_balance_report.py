# Copyright (c) 2025, Ayush Chaudhari and contributors
# For license information, please see license.txt

# import frappe
from frappe import _
from inventory.frappe_inventory.utils import get_total_stock_balance_per_warehouse

def execute(filters: dict | None = None):
	"""Return columns and data for the report.

	This is the main entry point for the report. It accepts the filters as a
	dictionary and should return columns and data. It is called by the framework
	every time the report is refreshed or a filter is updated.
	"""
	columns = get_columns()
	data = get_data()

	return columns, data


def get_columns() -> list[dict]:
	"""Return columns for the report.

	One field definition per column, just like a DocType field definition.
	"""
	return [
		{
			"label": _("Warehouse"),
			"fieldname": "Warehouse",
			"fieldtype": "Data",
		},
		{
			"label": _("Final Quantity"),
			"fieldname": "Final Quantity",
			"fieldtype": "Int",
		},
		{
			"label": _("Stock Balance"),
			"fieldname": "Stock Balance",
			"fieldtype": "Currency",
		},
	]


def get_data() -> list[list]:
	"""Return data for the report.

	The report data is a list of rows, with each row being a list of cell values.
	"""
	return get_total_stock_balance_per_warehouse()
