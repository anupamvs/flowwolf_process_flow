# Copyright (c) 2023, Flowwolf Inc. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class ProcessFlowGroup(Document):
	def validate(self):
		self.insert_custom_field()

	def validate_track_changes(self):
		if not frappe.get_meta(self.reference_doctype).track_changes:
			frappe.throw(_("Track Chnages Must be Enabled in Reference DocType."))

	def insert_custom_field(self):
		meta = frappe.get_meta(self.reference_doctype)
		print("````````````````````````````````````````````````````````````````")
		print(meta.__dict__)
		print("````````````````````````````````````````````````````````````````")
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
				"options": "\nPending\nIn Progress\nSucess\nFailed",
				"fieldname": "_processing_status",
				"insert_after": "_tab_process_flow",
			},
			{
				"doctype": "Custom Field",
				"dt": self.reference_doctype,
				"label": "Process Flow List",
				"fieldtype": "Table",
				"options": "Doc Process Flow Detail",
				"fieldname": "_doc_processes",
				"insert_after": "_processing_status",
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