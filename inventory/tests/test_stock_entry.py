import frappe
from datetime import datetime
from frappe.tests import IntegrationTestCase
from inventory.frappe_inventory.utils import get_last_stock_and_valuation, generate_item, generate_warehouse, generate_single_transaction


class TestStockEntryAndLedgerEntryFlow(IntegrationTestCase):
	def setUp(self):
		# Item creation
		self.item_name = "Chocomoco Chocolate"
		item = generate_item(self.item_name, "Consumable")
		item.submit()

		# Warehouse creation
		self.wh1 = "WH1"
		self.wh2 = "WH2"
		for warehouse_name in [self.wh1, self.wh2]:
			warehouse = generate_warehouse(warehouse_name)
			warehouse.save()

	def test_flow(self):
		# Adding to WH1 len(vals) times different quantities and stock to check moving average
		vals = [(10, 2), (11, 3), (9, 7)]

		for valuation_rate, quantity in vals:
			stock_entry = generate_single_transaction(
				"Receipt", quantity, self.item_name, valuation_rate=valuation_rate, destination_warehouse_name=self.wh1)
			stock_entry.submit()

		# To test if moving average, stock and balance-keeping work
		test_stock, test_stock_balance, test_valuation_rate = get_last_stock_and_valuation(
			self.item_name, self.wh1)
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

		consume_entry = generate_single_transaction(
			"Consume", consumed_quantity, self.item_name, valuation_rate=valuation_rate, source_warehouse_name=self.wh1)
		consume_entry.submit()

		test_stock, test_stock_balance, test_valuation_rate = get_last_stock_and_valuation(
			self.item_name, self.wh1)
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

		transfer_entry = generate_single_transaction("Transfer", transferred_quantity, self.item_name,
													 valuation_rate=valuation_rate, destination_warehouse_name=self.wh2, source_warehouse_name=self.wh1)
		transfer_entry.submit()

		wh1_test_stock, wh1_test_stock_balance, wh1_test_valuation_rate = get_last_stock_and_valuation(
			self.item_name, self.wh1)

		self.assertEqual(wh1_test_stock, wh1_actual_stock)
		self.assertAlmostEqual(wh1_test_stock_balance,
							   wh1_actual_stock_balance)
		self.assertAlmostEqual(wh1_test_valuation_rate,
							   wh1_actual_valuation_rate)

		wh2_test_stock, wh2_test_stock_balance, wh2_test_valuation_rate = get_last_stock_and_valuation(
			self.item_name, self.wh2)
		self.assertEqual(wh2_test_stock, wh2_actual_stock)
		self.assertAlmostEqual(wh2_test_stock_balance,
							   wh2_actual_stock_balance)
		self.assertAlmostEqual(wh2_test_valuation_rate,
							   wh2_actual_valuation_rate)
