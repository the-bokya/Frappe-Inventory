import frappe
from frappe.query_builder.functions import Count, Sum, Abs, Max
from datetime import datetime

# Method for moving average valuation
# def get_last_stock_and_valuation(item, warehouse):
# ledger_entries_d = frappe.qb.DocType("Stock Ledger Entry")
# """
# This query gets the moving average and the warehouse stock
# The warehouse stock can also be obtained from the most recent
# stock ledger entry for the item & warehouse. If there's no cancellation
# this aggregate query will return the same stock quantity imo.
# TODO: Test both.
# """
# query = (
# frappe.qb.from_(ledger_entries_d)
# .select(
# (
# Sum((ledger_entries_d.incoming_rate - ledger_entries_d.outgoing_rate) * Abs(ledger_entries_d.quantity_change))
# / Sum(ledger_entries_d.quantity_change),
# ),
# Count(ledger_entries_d.quantity_change),
# Sum(ledger_entries_d.quantity_change),
# )
# .where(ledger_entries_d.item == item)
# .where(ledger_entries_d.warehouse == warehouse)
# )
# print(query)
# stock, valuation, number_of_entries = query.run()[0]
# #result = query.run()
# #print(result)
# if number_of_entries == None or valuation == None:
# stock, valuation = 0, 0
# return stock, valuation


def get_last_stock_and_valuation(item, warehouse):
	ledger_entries_d = frappe.qb.DocType("Stock Ledger Entry")
	"""
	Stock and valuation using the latest Stock Ledger Entry's
	valuation rate.
	"""
	query = (
		frappe.qb.from_(ledger_entries_d)
		.select(ledger_entries_d.final_quantity, ledger_entries_d.stock_balance, ledger_entries_d.valuation_rate)
		.where(ledger_entries_d.item == item)
		.where(ledger_entries_d.warehouse == warehouse)
		.orderby(ledger_entries_d.transaction_datetime, order=frappe.query_builder.Order.desc)
		.orderby(ledger_entries_d.creation, order=frappe.query_builder.Order.desc)
		.limit(1)
	)
	result = query.run()

	if len(result):
		stock, stock_balance, valuation_rate = result[0]
	else:
		stock, stock_balance, valuation_rate = 0, 0, 0

	return stock, stock_balance, valuation_rate


def get_stock_ledger():
	ledger_entries_d = frappe.qb.DocType("Stock Ledger Entry")
	query = (
		frappe.qb.from_(ledger_entries_d)
		.select(
			ledger_entries_d.transaction_datetime.as_("Transaction Timestamp"),
			ledger_entries_d.final_quantity.as_("Final Quantity"),
			ledger_entries_d.item.as_("Item"),
			ledger_entries_d.parent_stock_entry.as_("Stock Entry"),
			ledger_entries_d.stock_balance.as_("Stock Balance"),
			ledger_entries_d.quantity_change.as_("Quantity Change"),
			ledger_entries_d.valuation_rate.as_("Valuation Rate"),
			ledger_entries_d.incoming_rate.as_("Incoming Rate"),
			ledger_entries_d.outgoing_rate.as_("Outgoing Rate"),
			ledger_entries_d.warehouse.as_("Warehouse")
		)
		.orderby(ledger_entries_d.transaction_datetime, order=frappe.query_builder.Order.asc)
		.orderby(ledger_entries_d.creation, order=frappe.query_builder.Order.asc)
	)
	return query.run(as_dict=True)


def get_stock_balance():
	ledger_entries_d = frappe.qb.DocType("Stock Ledger Entry")

	# This one gets the latest ledger entry timestamp for each warehouse-item pair
	latest_entries_per_group = (
		frappe.qb.from_(ledger_entries_d)
		.select(ledger_entries_d.item,
				ledger_entries_d.warehouse,
				Max(ledger_entries_d.transaction_datetime).as_("timestamp"),
				Max(ledger_entries_d.creation).as_("creation"),
				)
		.groupby(ledger_entries_d.item, ledger_entries_d.warehouse)
	)

	# This join is able to get only the latest key-value pairs' fields
	query = (
		frappe.qb.from_(ledger_entries_d)
		.join(latest_entries_per_group)
		.on(
			(ledger_entries_d.warehouse == latest_entries_per_group.warehouse) &
			(ledger_entries_d.transaction_datetime == latest_entries_per_group.timestamp) &
			(ledger_entries_d.creation == latest_entries_per_group.creation) &
			(ledger_entries_d.item == latest_entries_per_group.item)
		)
		.select(
			ledger_entries_d.final_quantity.as_("Final Quantity"),
			ledger_entries_d.item.as_("Item"),
			ledger_entries_d.stock_balance.as_("Stock Balance"),
			ledger_entries_d.quantity_change.as_("Quantity Change"),
			ledger_entries_d.valuation_rate.as_("Valuation Rate"),
			ledger_entries_d.warehouse.as_("Warehouse")
		)
	)
	return query.run(as_dict=True)

def get_total_stock_balance_per_warehouse():
	ledger_entries_d = frappe.qb.DocType("Stock Ledger Entry")

	# This one gets the latest ledger entry timestamp for each warehouse-item pair
	latest_entries_per_group = (
		frappe.qb.from_(ledger_entries_d)
		.select(
				ledger_entries_d.warehouse,
				Max(ledger_entries_d.transaction_datetime).as_("timestamp"),
				Max(ledger_entries_d.creation).as_("creation"),
				)
		.groupby(ledger_entries_d.item, ledger_entries_d.warehouse)
	)

	# This join is able to get only the latest key-value pairs' fields
	query = (
		frappe.qb.from_(ledger_entries_d)
		.join(latest_entries_per_group)
		.on(
			(ledger_entries_d.warehouse == latest_entries_per_group.warehouse) &
			(ledger_entries_d.transaction_datetime == latest_entries_per_group.timestamp) &
			(ledger_entries_d.creation == latest_entries_per_group.creation)
		)
		.select(
			Sum(ledger_entries_d.final_quantity).as_("Final Quantity"),
			Sum(ledger_entries_d.stock_balance).as_("Stock Balance"),
			ledger_entries_d.warehouse.as_("Warehouse")
		)
		.groupby(ledger_entries_d.warehouse)
	)
	return query.run(as_dict=True)

# A bunch of helper functions to generate various DocTypes
# Mostly for testing

def generate_item(item_name, item_type):
	item = frappe.get_doc({"doctype": "Item"})
	item.name1 = item_name
	item.type = item_type
	return item


def generate_warehouse(warehouse_name):
	warehouse = frappe.get_doc({"doctype": "Warehouse"})
	warehouse.warehouse_name = warehouse_name
	warehouse.parent_warehouse = "All Warehouses"
	return warehouse


def generate_single_transaction(transaction_type, quantity, item_name, valuation_rate=None, destination_warehouse_name=None, source_warehouse_name=None):
	stock_entry = generate_stock_entry(transaction_type)
	stock_entry_item = generate_stock_entry_item(quantity, item_name, stock_entry, valuation_rate=valuation_rate,
												 destination_warehouse_name=destination_warehouse_name, source_warehouse_name=source_warehouse_name)
	stock_entry_item.submit()
	stock_entry.transactions.append(stock_entry_item)
	return stock_entry


def generate_stock_entry(transaction_type):
	stock_entry = frappe.get_doc({"doctype": "Stock Entry"})
	stock_entry.transaction_type = transaction_type
	stock_entry.stock_datetime = datetime.now()
	return stock_entry


def generate_stock_entry_item(quantity, item_name, parent_stock_entry, valuation_rate=None, destination_warehouse_name=None, source_warehouse_name=None):
	stock_entry_item = frappe.get_doc({"doctype": "Stock Entry Item"})
	if destination_warehouse_name:
		stock_entry_item.destination_warehouse = destination_warehouse_name
	if source_warehouse_name:
		stock_entry_item.source_warehouse = source_warehouse_name
	if valuation_rate:
		stock_entry_item.valuation_rate = valuation_rate
	stock_entry_item.quantity = quantity
	stock_entry_item.item = item_name
	stock_entry_item.parent = parent_stock_entry
	stock_entry_item.parenttype = "Stock Entry"
	stock_entry_item.parentfield = "transactions"
	return stock_entry_item
