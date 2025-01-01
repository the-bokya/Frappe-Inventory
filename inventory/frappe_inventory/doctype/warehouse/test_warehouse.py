# Copyright (c) 2024, Ayush Chaudhari and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase
from frappe.tests.utils import FrappeTestCase
from inventory.frappe_inventory.utils import generate_warehouse

# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class UnitTestWarehouse(UnitTestCase):
	"""
	Unit tests for Warehouse.
	Use this class for testing individual functions and methods.
	"""

	pass


class IntegrationTestWarehouse(IntegrationTestCase):
	"""
	Integration tests for Warehouse.
	Use this class for testing interactions between multiple components.
	"""

	pass


class TestDriver(FrappeTestCase):
	def test_warehouse_generation(self):
		warehouse_name = "Jethalal"
		warehouse = generate_warehouse(warehouse_name)
		warehouse.insert()
		self.assertTrue(
			frappe.db.exists(
				{"doctype": "Warehouse", "warehouse_name": warehouse_name}
			)
		)
