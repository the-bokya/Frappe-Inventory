# Copyright (c) 2024, Ayush Chaudhari and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from inventory.frappe_inventory.utils import get_last_stock_and_valuation
from datetime import datetime


class StockEntry(Document):
	def on_submit(self):
		self.fetch_valuation()
		ledger_entries = self.generate_ledgers()

		# Common datetime entry for all ledgers
		current_time = datetime.now()

		for ledger_entry in ledger_entries:
			ledger_entry.transaction_datetime = current_time
			ledger_entry.submit()

	def submit_receipt(self):
		ledger_entries = []

	@frappe.whitelist
	def fetch_valuation(self):
		for transaction in self.transactions:
			_, valuation = get_last_stock_and_valuation(
				transaction.item, transaction.source_warehouse
			)
			transaction.valuation_rate = valuation

	def update_ledger_quantity(self, ledger):
		ledger.final_quantity = ledger.quantity_change

	def update_sent_ledger(self, ledger, transaction, stock, valuation_rate):
		ledger.warehouse = transaction.source_warehouse
		ledger.valuation_rate = valuation_rate
		ledger.quantity_change = -transaction.quantity

		self.update_ledger_quantity(ledger)

		ledger.incoming_rate = 0
		ledger.outgoing_rate = valuation_rate

	def update_received_ledger(self, ledger, transaction, stock, valuation_rate):
		ledger.warehouse = transaction.destination_warehouse

		# Valuation rate may change for the receiving ledger entry
		new_valuation_rate = (
			valuation_rate * stock + transaction.valuation_rate * transaction.quantity
		) / (stock + transaction.quantity)
		ledger.valuation_rate = new_valuation_rate
		ledger.quantity_change = transaction.quantity

		self.update_ledger_quantity(ledger)

		ledger.incoming_rate = valuation_rate
		ledger.outgoing_rate = 0

	def generate_ledgers(self):
		ledgers = []
		for transaction in self.transactions:
			stock, moving_average_valuation_rate = get_last_stock_and_valuation(
				transaction.item, transaction.source_warehouse
			)
			valuation_rate = transaction.valuation_rate

			# Hacky way to revert transactions if stock not satisfied
			if self.transaction_type != "Receipt":
				if stock < transaction.quantity:
					frappe.throw(f"Not enough stock for {self.transaction_type} transaction. (for {transaction.item}, {stock} < {transaction.quantity})")
					frappe.db.rollback()
				valuation_rate = moving_average_valuation_rate
				transaction.valuation_rate = valuation_rate
				sent_ledger = frappe.get_doc({"doctype": "Stock Ledger Entry"})
				sent_ledger.item = transaction.item
				self.update_sent_ledger(sent_ledger, transaction, stock, valuation_rate)
				ledgers.append(sent_ledger)

			if self.transaction_type != "Consume":
				received_ledger = frappe.get_doc({"doctype": "Stock Ledger Entry"})
				received_ledger.item = transaction.item
				self.update_received_ledger(
					received_ledger, transaction, stock, valuation_rate
				)
				ledgers.append(received_ledger)
		return ledgers
