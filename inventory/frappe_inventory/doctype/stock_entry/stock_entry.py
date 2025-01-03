# Copyright (c) 2024, Ayush Chaudhari and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from inventory.frappe_inventory.utils import get_last_stock_and_valuation
from datetime import datetime


class StockEntry(Document):
	def on_submit(self):

		# Common datetime entry for all ledgers
		current_time = self.stock_datetime

		# self.generate_ledgers yields a ledger at a time,
		# so all the ledgers are calculated and submitted sequentially.
		ledgers = self.generate_ledgers()
		for ledger in ledgers:
			ledger.transaction_datetime = current_time
			try:
				ledger.valuation_rate = ledger.stock_balance / ledger.final_quantity
			except ZeroDivisionError:
				ledger.valuation_rate = 0
			ledger.parent_stock_entry = self.name
			ledger.submit()

	def generate_ledgers(self):
		for transaction in self.transactions:
			(
				source_stock,
				source_stock_balance,
				source_moving_average_valuation_rate,
			) = get_last_stock_and_valuation(
				transaction.item, transaction.source_warehouse
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
				yield sent_ledger

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
				yield received_ledger


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
