import frappe


def after_install():
	insert_warehouses()

	frappe.db.commit()


def insert_warehouses():
	# Parent group for all warehouses, emulating "All Warehouses" from ERPNext
	parent_warehouse = insert_warehouse("All Warehouses", is_root=True)
	warehouse_names = ["Nattu Kaka", "Baagha"]

	for warehouse_name in warehouse_names:
		insert_warehouse(warehouse_name, parent_warehouse=parent_warehouse)


def insert_warehouse(warehouse_name, parent_warehouse=None, is_root=False):
	warehouse = frappe.get_doc(
		{"doctype": "Warehouse", "warehouse_name": warehouse_name}
	)

	if is_root:
		warehouse.is_group = True
	else:
		warehouse.parent_warehouse = parent_warehouse

	warehouse.insert()
	return warehouse