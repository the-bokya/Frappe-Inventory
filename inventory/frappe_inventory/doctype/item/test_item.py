# Copyright (c) 2024, Ayush Chaudhari and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase
from frappe.tests.utils import FrappeTestCase
from inventory.frappe_inventory.utils import generate_item

# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class UnitTestItem(UnitTestCase):
	"""
	Unit tests for Item.
	Use this class for testing individual functions and methods.
	"""

	pass


class IntegrationTestItem(IntegrationTestCase):
	"""
	Integration tests for Item.
	Use this class for testing interactions between multiple components.
	"""

	pass

class TestDriver(FrappeTestCase):
	def test_item_generation(self):
		# Testing item creation
		item_name = "Chocomoco Chocolate - Premium"
		item = generate_item(item_name, "Consumable")
		item.submit()

		self.assertTrue(frappe.db.exists({"doctype": "Item", "name1": item_name}))