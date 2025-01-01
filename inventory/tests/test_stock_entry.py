import frappe
from datetime import datetime
from frappe.tests import IntegrationTestCase
from inventory.frappe_inventory.utils import get_last_stock_and_valuation

class TestStockEntryAndLedgerEntryFlow(IntegrationTestCase):
	def test_flow(self):
		# Testing item creation
		item = frappe.get_doc({"doctype": "Item"})
		item_name = "Chocomoco Chocolate"
		item.name1 = item_name
		item.type = "Consumable"
		item.submit()

		self.assertTrue(frappe.db.exists({"doctype": "Item", "name1": item_name}))

		# Testing warehouse creation
		wh1 = "WH1"
		wh2 = "WH2"
		for warehouse_name in [wh1, wh2]:
			warehouse = frappe.get_doc({"doctype": "Warehouse"})
			warehouse.warehouse_name = warehouse_name
			warehouse.parent_warehouse = "All Warehouses"
			warehouse.submit()

			self.assertTrue(
				frappe.db.exists(
					{"doctype": "Warehouse", "warehouse_name": warehouse_name}
				)
			)

		# Testing "Receipt" by adding twice
		vals = [(10, 2), (11, 3), (9, 7)]

		for valuation_rate, quantity in vals:
			entry = frappe.get_doc({"doctype": "Stock Entry"})
			entry.transaction_type = "Receipt"
			entry.stock_datetime = datetime.now()
			transaction = frappe.get_doc({"doctype": "Stock Entry Item"})
			transaction.destination_warehouse = wh1
			transaction.quantity = quantity
			transaction.item = item_name
			transaction.valuation_rate = valuation_rate
			transaction.parent = entry
			transaction.parenttype = "Stock Entry"
			transaction.parentfield = "transactions"
			transaction.submit()
			entry.transactions.append(transaction)
			entry.submit()

			self.assertTrue(
				frappe.db.exists({"doctype": "Stock Entry", "name": entry.name})
			)

		# Test if moving average, stock and balance-keeping work
		test_stock, test_stock_balance, test_valuation_rate = get_last_stock_and_valuation(item_name, wh1)
		actual_stock = sum([qty for val, qty in vals])
		actual_stock_balance = sum([val*qty for val, qty in vals])
		actual_valuation_rate = actual_stock_balance / actual_stock

		self.assertEqual(test_stock, actual_stock)
		self.assertAlmostEqual(test_stock_balance, actual_stock_balance)
		self.assertAlmostEqual(test_valuation_rate, actual_valuation_rate)

		# Test "Consume"
		consumed_quantity = 2
		
		# Self explanatory.
		actual_stock -= consumed_quantity
		actual_stock_balance = actual_stock * actual_valuation_rate
		# Valuation rate doesn't change upon consumption

		entry = frappe.get_doc({"doctype": "Stock Entry"})
		entry.transaction_type = "Consume"
		entry.stock_datetime = datetime.now()
		transaction = frappe.get_doc({"doctype": "Stock Entry Item"})
		transaction.source_warehouse = wh1
		transaction.quantity = consumed_quantity
		transaction.item = item_name
		transaction.valuation_rate = valuation_rate
		transaction.parent = entry
		transaction.parenttype = "Stock Entry"
		transaction.parentfield = "transactions"
		transaction.submit()
		entry.transactions.append(transaction)
		entry.submit()

		test_stock, test_stock_balance, test_valuation_rate = get_last_stock_and_valuation(item_name, wh1)
		self.assertEqual(test_stock, actual_stock)
		self.assertAlmostEqual(test_stock_balance, actual_stock_balance)
		self.assertAlmostEqual(test_valuation_rate, actual_valuation_rate)

		# Test "Transfer"
		transferred_quantity = 3
		
		wh1_actual_stock = actual_stock - transferred_quantity
		wh1_actual_stock_balance = wh1_actual_stock * actual_valuation_rate
		wh1_actual_valuation_rate = actual_valuation_rate

		"""
		Valuation rate doesn't change across transfers and wh2 is currently empty.
		So, it is reasonable to assume that wh2's valuation rate is the same as
		that of wh1's after the transfer
		"""

		wh2_actual_stock = transferred_quantity
		wh2_actual_stock_balance = wh2_actual_stock * actual_valuation_rate
		wh2_actual_valuation_rate = actual_valuation_rate
		

		entry = frappe.get_doc({"doctype": "Stock Entry"})
		entry.transaction_type = "Transfer"
		entry.stock_datetime = datetime.now()
		transaction = frappe.get_doc({"doctype": "Stock Entry Item"})
		transaction.source_warehouse = wh1
		transaction.destination_warehouse = wh2
		transaction.quantity = transferred_quantity
		transaction.item = item_name
		transaction.valuation_rate = valuation_rate
		transaction.parent = entry
		transaction.parenttype = "Stock Entry"
		transaction.parentfield = "transactions"
		transaction.submit()
		entry.transactions.append(transaction)
		entry.submit()

		wh1_test_stock, wh1_test_stock_balance, wh1_test_valuation_rate = get_last_stock_and_valuation(item_name, wh1)
		self.assertEqual(wh1_test_stock, wh1_actual_stock)
		self.assertAlmostEqual(wh1_test_stock_balance, wh1_actual_stock_balance)
		self.assertAlmostEqual(wh1_test_valuation_rate, wh1_actual_valuation_rate)

		wh2_test_stock, wh2_test_stock_balance, wh2_test_valuation_rate = get_last_stock_and_valuation(item_name, wh2)
		self.assertEqual(wh2_test_stock, wh2_actual_stock)
		self.assertAlmostEqual(wh2_test_stock_balance, wh2_actual_stock_balance)
		self.assertAlmostEqual(wh2_test_valuation_rate, wh2_actual_valuation_rate)
		frappe.db.commit()