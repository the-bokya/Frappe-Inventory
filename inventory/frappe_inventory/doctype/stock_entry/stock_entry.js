// Copyright (c) 2024, Ayush Chaudhari and contributors
// For license information, please see license.txt

frappe.ui.form.on("Stock Entry", {
	onload(frm) {
		update_transactions_fields(frm);
	},
	transaction_type(frm) {
		update_transactions_fields(frm);
	},
});

const update_transactions_fields = (frm) => {
	get_transactions(frm).refresh();
	switch (frm.fields_dict["transaction_type"].value) {
		case "Receipt":
			read_only_warehouse_state(frm, "source_warehouse", 1);
			read_only_warehouse_state(frm, "destination_warehouse", 0);
			read_only_valuation_state(frm, 0);
			break;
		case "Consume":
			read_only_warehouse_state(frm, "source_warehouse", 0);
			read_only_warehouse_state(frm, "destination_warehouse", 1);
			auto_valuation(frm);
			break;
		case "Transfer":
			read_only_warehouse_state(frm, "source_warehouse", 0);
			read_only_warehouse_state(frm, "destination_warehouse", 0);
			auto_valuation(frm);
			break;
	}
};

const get_transactions = (frm) => frm.fields_dict.transactions.grid;

const get_warehouse = (frm, warehouse_name) => get_transactions(frm).fields_map[warehouse_name];
const read_only_warehouse_state = (frm, warehouse_name, state) => {
	get_warehouse(frm, warehouse_name).hidden = state;
};
const read_only_valuation_state = (frm, state) => {
	get_transactions(frm).fields_map.valuation_rate.hidden = state;
};

const auto_valuation = (frm) => {
	frappe.msgprint("Valuation will be calculated automatically upon submission.");
	read_only_valuation_state(frm, 1);
};
