# Copyright (c) 2024, Ayush Chaudhari and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase
from frappe.tests.utils import FrappeTestCase
from inventory.frappe_inventory.utils import generate_single_transaction, generate_item


# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class UnitTestStockEntry(UnitTestCase):
	"""
	Unit tests for StockEntry.
	Use this class for testing individual functions and methods.
	"""

	pass


class IntegrationTestStockEntry(IntegrationTestCase):
	"""
	Integration tests for StockEntry.
	Use this class for testing interactions between multiple components.
	"""

	pass

class TestDriver(FrappeTestCase):
	def setUp(self):
		generate_item("TV", "Consumable").insert()
	def test_stock_entry_generation(self):
		stock_entry = generate_single_transaction("Receipt", 1, "TV", valuation_rate=1, destination_warehouse_name="Nattu Kaka")
		stock_entry.submit()

		self.assertTrue(
			frappe.db.exists({"doctype": "Stock Entry", "name": stock_entry.name})
		)
