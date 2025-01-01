import frappe
from frappe.query_builder.functions import Count, Sum, Abs

# Method for moving average valuation
# def get_last_stock_and_valuation(item, warehouse):
#	 ledger_entries_d = frappe.qb.DocType("Stock Ledger Entry")
#	 """
#	 This query gets the moving average and the warehouse stock
#	 The warehouse stock can also be obtained from the most recent
#	 stock ledger entry for the item & warehouse. If there's no cancellation
#	 this aggregate query will return the same stock quantity imo.
#	 TODO: Test both.
#	 """
#	 query = (
#		 frappe.qb.from_(ledger_entries_d)
#		 .select(
#			 (
#				 Sum((ledger_entries_d.incoming_rate - ledger_entries_d.outgoing_rate) * Abs(ledger_entries_d.quantity_change))
#				 / Sum(ledger_entries_d.quantity_change),
#			 ),
#			 Count(ledger_entries_d.quantity_change),
#			 Sum(ledger_entries_d.quantity_change),
#		 )
#		 .where(ledger_entries_d.item == item)
#		 .where(ledger_entries_d.warehouse == warehouse)
#	 )
#	 print(query)
#	 stock, valuation, number_of_entries = query.run()[0]
#	 #result = query.run()
#	 #print(result)
#	 if number_of_entries == None or valuation == None:
#		 stock, valuation = 0, 0
#	 return stock, valuation


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
		.limit(1)
	)
	result = query.run()
	if len(result):
		stock, stock_balance, valuation_rate = result[0]
	else:
		stock, stock_balance, valuation_rate = 0, 0, 0
	print(stock, stock_balance, valuation_rate)
	return stock, stock_balance, valuation_rate
