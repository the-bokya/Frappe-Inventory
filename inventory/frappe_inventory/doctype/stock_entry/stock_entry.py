# Copyright (c) 2024, Ayush Chaudhari and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from inventory.frappe_inventory.utils import get_last_stock_and_valuation
from datetime import datetime


class StockEntry(Document):
	def on_submit(self):
		self.fetch_valuation()
		ledgers = self.generate_ledgers()

		# Common datetime entry for all ledgers
		current_time = self.stock_datetime

		for ledger in ledgers:
			ledger.transaction_datetime = current_time
			ledger.valuation_rate = ledger.stock_balance / ledger.final_quantity
			ledger.submit()

	def submit_receipt(self):
		ledgers = []


	def update_ledger_quantity(self, ledger, stock):
		ledger.final_quantity = stock + ledger.quantity_change

	def update_sent_ledger(
		self, ledger, transaction, stock, stock_balance, valuation_rate
	):
		ledger.warehouse = transaction.source_warehouse
		ledger.quantity_change = -transaction.quantity
		ledger.stock_balance = stock_balance + ledger.quantity_change * valuation_rate

		self.update_ledger_quantity(ledger, stock)

		ledger.incoming_rate = 0
		ledger.outgoing_rate = valuation_rate

	def update_received_ledger(
		self, ledger, transaction, stock, stock_balance, valuation_rate
	):
		ledger.warehouse = transaction.destination_warehouse

		ledger.quantity_change = transaction.quantity
		ledger.stock_balance = stock_balance + ledger.quantity_change * valuation_rate

		self.update_ledger_quantity(ledger, stock)

		ledger.incoming_rate = valuation_rate
		ledger.outgoing_rate = 0

	def generate_ledgers(self):
		ledgers = []
		for transaction in self.transactions:
			source_stock, source_stock_balance, source_moving_average_valuation_rate = (
				get_last_stock_and_valuation(
					transaction.item, transaction.source_warehouse
				)
			)
			(
				destination_stock,
				destination_stock_balance,
				destination_moving_average_valuation_rate,
			) = get_last_stock_and_valuation(
				transaction.item, transaction.destination_warehouse
			)
			if self.transaction_type == "Receipt":
				valuation_rate = transaction.valuation_rate
			else:
				valuation_rate = source_moving_average_valuation_rate

			# Hacky way to revert transactions if stock not satisfied
			if self.transaction_type != "Receipt":
				if source_stock < transaction.quantity:
					frappe.throw(
						f"Not enough stock for {self.transaction_type} transaction. (for {transaction.item}, {source_stock} < {transaction.quantity})"
					)
					frappe.db.rollback()

				source_valuation_rate = source_moving_average_valuation_rate
				transaction.valuation_rate = valuation_rate
				sent_ledger = frappe.get_doc({"doctype": "Stock Ledger Entry"})
				sent_ledger.item = transaction.item
				self.update_sent_ledger(
					sent_ledger,
					transaction,
					source_stock,
					source_stock_balance,
					valuation_rate,
				)
				ledgers.append(sent_ledger)

			if self.transaction_type != "Consume":
				received_ledger = frappe.get_doc({"doctype": "Stock Ledger Entry"})
				received_ledger.item = transaction.item
				self.update_received_ledger(
					received_ledger,
					transaction,
					destination_stock,
					destination_stock_balance,
					valuation_rate,
				)
				ledgers.append(received_ledger)
		return ledgers
