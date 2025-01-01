# Copyright (c) 2025, Ayush Chaudhari and contributors
# For license information, please see license.txt

# import frappe
from frappe import _
from inventory.frappe_inventory.utils import get_stock_ledger


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
			"label": _("Transaction Timestamp"),
			"fieldname": "Transaction Timestamp",
			"fieldtype": "Datetime",
		},
		{
			"label": _("Stock Entry"),
			"fieldname": "Stock Entry",
			"fieldtype": "Link",
			"options": "Stock Entry",
		},
		{
			"label": _("Item"),
			"fieldname": "Item",
			"fieldtype": "Link",
			"options": "Item",
		},
		{
			"label": _("Warehouse"),
			"fieldname": "Warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
		},
		{
			"label": _("Quantity Change"),
			"fieldname": "Quantity Change",
			"fieldtype": "Int",
		},
		{
			"label": _("Final Quantity"),
			"fieldname": "Final Quantity",
			"fieldtype": "Int",
		},
		{
			"label": _("Valuation Rate"),
			"fieldname": "Valuation Rate",
			"fieldtype": "Currency",
		},
		{
			"label": _("Incoming Rate"),
			"fieldname": "Incoming Rate",
			"fieldtype": "Currency",
		},
		{
			"label": _("Outgoing Rate"),
			"fieldname": "Outgoing Rate",
			"fieldtype": "Currency",
		},
	]


def get_data() -> list[list]:
	"""Return data for the report.

	The report data is a list of rows, with each row being a list of cell values.
	"""
	return get_stock_ledger()
