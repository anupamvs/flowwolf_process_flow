import frappe
import flowwolf
import json
from frappe import _
from frappe.utils import get_link_to_form
from frappe.utils.file_manager import get_file_path
from frappe.utils.background_jobs import enqueue

EVENT_MAP = {
	"before_insert": "Before Insert",
	"after_insert": "After Insert",
	"before_validate": "Before Validate",
	"validate": "Before Save",
	"on_update": "After Save",
	"before_submit": "Before Submit",
	"on_submit": "After Submit",
	"before_cancel": "Before Cancel",
	"on_cancel": "After Cancel",
	"on_trash": "Before Delete",
	"after_delete": "After Delete",
	"before_update_after_submit": "Before Save (Submitted Document)",
	"on_update_after_submit": "After Save (Submitted Document)"
}

def update_doc_processes(doc, method):
	process_flow_groups_doctypes = frappe.get_all("Application Flow", pluck="reference_doctype")
	if doc.doctype in process_flow_groups_doctypes and not doc._doc_processes:
		process_list = get_process_flow_group_process_list(doc)
		for row in process_list:
			if not has_doc_process(doc, row.get("state")):
				doc.append("_doc_processes", row)

def get_process_flow_group_process_list(doc):
	process_flow_groups = frappe.get_all("Application Flow", {"reference_doctype": doc.doctype}, pluck="name")
	process_list = []
	for process_flow_group in process_flow_groups:
		process_flow_group = frappe.get_doc("Application Flow", process_flow_group)
		for process in process_flow_group.process_flow_configuration:
			process_list.append({"field": process_flow_group.field, "state": process.state, "to_state": process.to_state, "process_flow": process.process_flow})
	
	return process_list

def has_doc_process(doc, state):
	for process in doc._doc_processes:
		if process.state == state:
			return True
	return False

# def execute_process_flow(doc, method):
# 	if frappe.flags.in_test or frappe.flags.in_migrate:
# 		return

# 	process_workflows = frappe.get_all("Process Flow",
# 		filters={
# 			"document_type": doc.doctype,
# 			"doctype_event": EVENT_MAP.get(method)
# 		}, pluck="name"
# 	)

# 	for process_workflow in process_workflows:
# 		process_workflow = frappe.get_doc("Process Flow", process_workflow)
# 		process_workflow.run_processes(doc)

# def execute_process_flow_after_insert(doc, method):
# 	if frappe.flags.in_test or frappe.flags.in_migrate:
# 		return

# 	process_flow_settings = frappe.get_doc("Process Flow Settings")
# 	status_field_map = {
# 		"Doc": "processing_status",
# 		"Doc Load": "status",
# 		"Doc Scale Ticket": "status"
# 	}
# 	if (process_flow_settings.in_background and 
# 		doc.doctype in ["Doc", "Doc Load", "Doc Scale Ticket"] and
# 		doc.get(status_field_map.get(doc.doctype))):
# 			enqueue_process_flow(doc.doctype, doc.name)

def run_process_flow(doc, method):
	process_flow_groups_doctypes = frappe.get_all("Application Flow", pluck="reference_doctype")
	process_flow_groups_field = frappe.get_all("Application Flow", filters={"reference_doctype": doc.ref_doctype}, pluck="field")

	process_flow_settings = frappe.get_doc("Process Flow Settings")

	if(process_flow_settings.in_background and doc.ref_doctype in process_flow_groups_doctypes and process_flow_groups_field):
		data = json.loads(doc.data)
		if data.get("changed"):
			for field in process_flow_groups_field:
				for row in data.get("changed"):
					if (len(row) == 3 and 
						row[0] == field and 
						row[2] and row[1]!=row[2]):
						enqueue_process_flow(doc.ref_doctype, doc.docname, field)

def enqueue_process_flow(dt, dn, field):
	enqueue("flowwolf_process_flow.utils.run_process_flow_", enqueue_after_commit=True, doctype=dt, name=dn, field=field)

def run_process_flow_(doctype, name, field):
	import time
	time.sleep(1)

	doc = frappe.get_doc(doctype, name)
	for row in doc._doc_processes:
		if row.field == field and row.state == doc.get(field):
			process_flow = frappe.get_doc("Process Flow", row.process_flow)
			process_flow.run_processes(doc, None, None, f"Status - {doc.get(field)}")
			doc = frappe.get_doc(doctype, name)
			if row.to_state and doc.processing_status_ != "Failed":
				doc.set(field, row.to_state)
				doc.save()

			break
			
@frappe.whitelist()
def get_process_flow_log_html_table(dt, dn):
	logs = frappe.get_all("Process Flow Log",  filters={"reference_document": dt, "reference_name": dn}, fields=["name", "status", "process_flow", "error_message", "creation", "description"])

	if logs:
		color = {
			"Pending": "grey",
			"In Progress": "orange",
			"Success": "green",
			"Failed": "red"
		}
		html = """
				<table class="table table-bordered">
					<thead>
						<tr>
							<th scope="col">Process Flow</th>
							<th scope="col">Description</th>
							<th scope="col">Status</th>
							<th scope="col">Error Message</th>
							<th>
						</tr>
					</thead>
					<tbody>
				"""
		
		for log in logs:
			error_message = log.error_message if log.error_message else ""
			description = log.description if log.description else ""
			html += f"""
						<tr>
							<td>{get_link_to_form("Process Flow Log", log.name, log.process_flow)}</td>
							<td>{description}</td>
							<td><span class="indicator whitespace-nowrap {color[log.status]}"> {log.status}</td>
							<td>{error_message}</td>
							<td>{frappe.utils.pretty_date(log.creation)}</td>
						</tr>
					"""
		
		html += """
					</tbody>
				</table>
			"""
		
		return html