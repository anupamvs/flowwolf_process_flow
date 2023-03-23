// Copyright (c) 2023, Flowwolf Inc. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Process Flow Group', {
	onload: function(frm) {
		frm.set_query("reference_doctype", function() {
			return {
				"filters": {
					"track_changes": 1,
				}
			};
		});
	
		frm.set_query("process_flow", "process_flow_configuration", function() {
			return {
				"filters": {
					"type": ["!=", "Field Processing"],
				}
			};
		});
	},

	refresh(frm) {
		frm.trigger("set_status_field_options");
		frm.trigger("set_doc_process_flow_state_options");
	},

	reference_doctype(frm) {
		frm.trigger("set_status_field_options");
	},

	field(frm) {
		frm.trigger("set_doc_process_flow_state_options");
	},
	
	set_status_field_options(frm) {
		if (frm.doc.reference_doctype) {
			frappe.model.with_doctype(frm.doc.reference_doctype, () => {
				let meta = frappe.get_meta(frm.doc.reference_doctype);
				let fields = meta.fields.filter(df => df.fieldtype == "Select");
				let options = fields.map(f => {
					return {"label": f.label, "value": f.fieldname}
				});

				frm.set_df_property("field", "options", options);
			});
		}
	},

	set_doc_process_flow_state_options(frm) {
		if (frm.doc.reference_doctype && frm.doc.field) {
			frappe.model.with_doctype(frm.doc.reference_doctype, () => {
				let meta = frappe.get_meta(frm.doc.reference_doctype);
				let field = meta.fields.find(df => df.fieldname === frm.doc.field);

				frappe.meta.get_docfield("Process Flow Configuration", "state", frm.doc.name).options = field.options.split("\n");
				frappe.meta.get_docfield("Process Flow Configuration", "to_state", frm.doc.name).options = field.options.split("\n");
			});
		}
	}
});
