# Copyright (c) 2023, Flowwolf Inc. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class ApplicationFlow(Document):
	def validate(self):
		self.insert_custom_field()
		self.create_client_script()

	def validate_track_changes(self):
		if not frappe.get_meta(self.reference_doctype).track_changes:
			frappe.throw(_("Track Chnages Must be Enabled in Reference DocType."))

	def insert_custom_field(self):
		meta = frappe.get_meta(self.reference_doctype)

		field_list = [
			{
				"doctype": "Custom Field",
				"dt": self.reference_doctype,
				"label": "Process Flow",
				"fieldtype": "Tab Break",
				"fieldname": "_tab_process_flow",
				"insert_after": meta.fields[-1].fieldname,
			},
			{
				"doctype": "Custom Field",
				"dt": self.reference_doctype,
				"label": "Processing Status",
				"fieldtype": "Select",
				"options": "\nPending\nIn Progress\nSuccess\nFailed",
				"fieldname": "processing_status_",
				"insert_after": "_tab_process_flow",
			},
			{
				"doctype": "Custom Field",
				"dt": self.reference_doctype,
				"label": "Failed Reason",
				"fieldtype": "Small Text",
				"read_only": 1,
				"fieldname": "_failed_reason",
				"depends_on": "eval: doc.processing_status_=='Failed'",
				"insert_after": "processing_status_",
			},
			{
				"doctype": "Custom Field",
				"dt": self.reference_doctype,
				"label": "Process Flow Configuration",
				"fieldtype": "Table",
				"options": "Process Flow Configuration Detail",
				"fieldname": "_doc_processes",
				"insert_after": "_failed_reason",
			},
			{
				"doctype": "Custom Field",
				"dt": self.reference_doctype,
				"fieldtype": "HTML",
				"fieldname": "_process_log",
				"insert_after": "_doc_processes",
			},
		]

		for row in field_list:
			if not meta.has_field(row.get("fieldname")):
				frappe.get_doc(row).insert()

	def create_client_script(self):
		client_script = frappe.db.exists("Client Script", f"Process Flow Log {self.reference_doctype}")
		if not client_script:
			client_script = frappe.get_doc({
				"doctype": "Client Script",
				"dt": self.reference_doctype,
				"view": "Form",
				"enabled": 1,
				"name": f"Process Flow Log {self.reference_doctype}",
				"script": """frappe.ui.form.on('"""+ self.reference_doctype +"""', {\n\trefresh(frm) {\n\t\tif(!frm.is_new()) {\n\t\t\tfrm.trigger("setup_process_flow_log");\n\t\t}\n\t},\n\tsetup_process_flow_log(frm) {\n\t\tfrappe.call({\n\t\t\tmethod: "flowwolf_process_flow.utils.get_process_flow_log_html_table",\n\t\t\targs: {\n\t\t\t\tdt: frm.doc.doctype,\n\t\t\t\tdn: frm.doc.name,\n\t\t\t},\n\t\t\tcallback: function(r) {\n\t\t\t\tif(r.message) {\n\t\t\t\t\t$(frm.fields_dict['_process_log'].wrapper).html(r.message);\n\t\t\t\t}\n\t\t\t}\n\t\t});\n\t},\n})"""
			}).insert()