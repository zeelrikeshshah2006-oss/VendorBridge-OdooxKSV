from flask import Flask, render_template, request, redirect, session, url_for, send_file
from datetime import datetime

from pymongo import MongoClient

app = Flask(__name__)

app.secret_key = "erp_secret_key"

client = MongoClient(
"mongodb+srv://zeelrikeshshah2006_db_user:Zeel123@cluster0.oeaqtyt.mongodb.net/?appName=Cluster0"
)

db = client["vendorbridge"]

# Define collections
users = db["users"]
vendors = db["vendors"]
rfqs = db["rfqs"]
quotations = db["quotations"]
approvals = db["approvals"]
purchase_orders = db["purchaseOrders"]
invoices = db["invoices"]
activity_logs = db["activityLogs"]
@app.route("/")
def home():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():

    email = request.form["email"]
    password = request.form["password"]
    role = request.form["role"]

    user = db.users.find_one({
        "email": email,
        "password": password,
        "role": role
    })

    if user:

        session["user"] = email
        session["role"] = role
        session["name"] = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip() or email

        if role == "Vendor":
            return redirect("/vendor-dashboard")
        else:
            return redirect("/dashboard")

    return render_template("login.html", error="Invalid Email, Password, or Role")

@app.route("/dashboard")
def dashboard():

    total_rfqs = rfqs.count_documents({})
    total_vendors = vendors.count_documents({})
    total_invoices = invoices.count_documents({})
    total_approvals = approvals.count_documents({})

    return render_template(
        "dashboard.html",
        rfqs=total_rfqs,
        vendors=total_vendors,
        invoices=total_invoices,
        approvals=total_approvals
    )

@app.route("/add_vendor", methods=["POST"])
def add_vendor():

    vendors.insert_one({

        "vendor_name":
        request.form["vendor_name"],

        "gst":
        request.form["gst"],

        "category":
        request.form["category"],

        "status":"Active"

    })

    activity_logs.insert_one({
        "action":"Vendor Added"
    })

    return redirect("/vendors")

@app.route("/create_rfq", methods=["POST"])
def create_rfq():

    rfqs.insert_one({
        "title":
        request.form["title"],

        "quantity":
        request.form["quantity"],

        "deadline":
        request.form["deadline"],

        "vendor_ids":
        request.form.getlist("vendor_ids"),

        "status":"Open"
    })

    activity_logs.insert_one({
        "action":"RFQ Created",
        "user":session["user"]
    })

    return redirect("/dashboard")


@app.route("/submit_quote", methods=["POST"])
def submit_quote():

    quotations.insert_one({

        "rfq_id":
        request.form["rfq_id"],

        "price":
        request.form["price"],

        "delivery_days":
        request.form["delivery_days"]

    })

    return redirect("/quotation")

@app.route("/comparison")
def view_comparison():
    # Fetch all vendors
    all_vendors = list(vendors.find())
    # Build comparison data
    comparison = []
    min_price = None
    for v in all_vendors:
        quote = quotations.find_one({"vendor_id": v["_id"]})
        price = float(quote.get('price', 0)) if quote else None
        if price is not None:
            if min_price is None or price < min_price:
                min_price = price
        comparison.append({
            "vendor_id": str(v["_id"]),
            "name": v.get('vendor_name') or v.get('companyName'),
            "price": price,
            "delivery": quote.get('delivery_days') if quote else None,
            "rating": v.get('rating'),
            "warranty": v.get('warranty'),
            "payment": v.get('payment_terms')
        })
    return render_template("Quotation comparison.html", comparison=comparison, min_price=min_price)

@app.route("/approve/<id>")
def approve(id):

    approvals.insert_one({

        "quotation_id":id,

        "status":"Approved"

    })

    return redirect("/approvals")

@app.route("/generate_po/<id>")
def generate_po(id):

    purchase_orders.insert_one({

        "quotation_id":id,

        "po_number":"PO001",

        "status":"Generated"

    })

    return redirect("/purchase-order")

@app.route("/generate_invoice/<id>")
def generate_invoice(id):

    subtotal = 50000

    gst = subtotal * 0.18

    total = subtotal + gst

    invoices.insert_one({

        "po_id":id,

        "subtotal":subtotal,

        "gst":gst,

        "total":total

    })

    return redirect("/invoice")

@app.route("/reports")
def reports():

    vendor_count = vendors.count_documents({})

    rfq_count = rfqs.count_documents({})

    invoice_count = invoices.count_documents({})

    return render_template(
        "reports-analytics.html",
        vendors=vendor_count,
        rfqs=rfq_count,
        invoices=invoice_count
    )

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        firstName = request.form["firstName"]
        lastName = request.form["lastName"]
        email = request.form["email"]
        phone = request.form["phone"]
        role = request.form["role"]
        country = request.form["country"]
        password = request.form["password"]
        additionalInfo = request.form.get("additionalInfo", "")

        # Check if user already exists
        existing_user = db.users.find_one({"email": email})
        if existing_user:
            return render_template("register.html", error="Email already registered")

        # Insert into MongoDB users collection
        db.users.insert_one({
            "firstName": firstName,
            "lastName": lastName,
            "email": email,
            "phone": phone,
            "role": role,
            "country": country,
            "password": password,
            "additionalInfo": additionalInfo
        })

        return redirect("/")
    
    return render_template("register.html")

@app.route("/vendor-dashboard")
def vendor_dashboard():
    return render_template("vendor-dashboard.html")

@app.route("/vendors")
def view_vendors():
    all_vendors = list(vendors.find())
    return render_template("vendors.html", vendors=all_vendors)

@app.route("/rfqs")
def view_rfqs():
    all_vendors = list(vendors.find())
    return render_template("RFQ's.html", vendors=all_vendors)

@app.route("/submit_comparison", methods=["POST"])
def submit_comparison():
    # Retrieve selected vendor ID from the form
    selected_vendor_id = request.form.get("selected_vendor")
    if not selected_vendor_id:
        # No vendor selected; redirect back with a message (could flash)
        return redirect(url_for('view_comparison'))

    # Insert a new purchase order linked to the selected vendor
    from bson.objectid import ObjectId
    vendor_obj = vendors.find_one({"_id": ObjectId(selected_vendor_id)})
    # Export comparison data as CSV
    import csv, io
    output = io.StringIO()
    writer = csv.writer(output)
    # Header
    header = ["Vendor"] + ["Price", "Delivery", "Rating", "Warranty", "Payment"]
    writer.writerow(header)
    for vendor in vendors.find():
        row = [vendor.get('vendor_name') or vendor.get('companyName'), "", "", vendor.get('rating', ''), "", ""]
        writer.writerow(row)
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='quotation_comparison.csv')

@app.route("/export_report")
def export_report():
    # Generate report CSV aggregating RFQs, POs, and approvals
    import csv, io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Metric", "Count"])
    writer.writerow(["Vendors", vendors.count_documents({})])
    writer.writerow(["RFQs", rfqs.count_documents({})])
    writer.writerow(["Purchase Orders", purchase_orders.count_documents({})])
    writer.writerow(["Approvals", approvals.count_documents({})])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='report.csv')

@app.route("/approvals")
def list_approvals():
    # Fetch recent approvals and timeline events
    recent_approvals = list(approvals.find().sort('created_at', -1).limit(5))
    # For each approval, gather its timeline events
    timeline = []
    for appr in recent_approvals:
        events = list(approval_events.find({"approval_id": appr["_id"]}).sort('timestamp', 1))
        timeline.append({"approval": appr, "events": events})
    return render_template("approval workflow.html", approvals=recent_approvals, timeline=timeline)

@app.route("/purchase-order")
def view_purchase_order():
    # Get selected vendor ID from query parameters
    vendor_id = request.args.get("vendor_id")
    # Fetch all vendors for dropdown
    all_vendors = list(vendors.find())
    selected_vendor = None
    if vendor_id:
        try:
            from bson.objectid import ObjectId
            selected_vendor = vendors.find_one({"_id": ObjectId(vendor_id)})
        except Exception:
            selected_vendor = None
    # Fetch purchase order and its items
    po = purchase_orders.find_one({"vendor_id": ObjectId(vendor_id)}) if vendor_id else None
    # Dummy items if none exist
    po_items = []
    if po:
        po_items = list(db["po_items"].find({"po_id": po["_id"]}))
        subtotal = sum(item.get('quantity', 0) * item.get('unit_price', 0) for item in po_items)
        gst = subtotal * 0.18
        total = subtotal + gst
    else:
        subtotal = gst = total = 0
    return render_template(
        "purchase-order-invoice.html",
        vendors=all_vendors,
        vendor=selected_vendor,
        purchase_order=po,
        po_items=po_items,
        subtotal=subtotal,
        gst=gst,
        total=total
    )

@app.route("/invoice")
def view_invoice():
    return render_template("purchase-order-invoice.html")

@app.route("/approve_vendor", methods=["POST"])


def approve_vendor():
    vendor_id = request.form.get('vendor_id')
    if not vendor_id:
        return redirect(url_for('view_comparison'))
    # Create PO and approval record
    from bson.objectid import ObjectId
    vendor_obj = vendors.find_one({"_id": ObjectId(vendor_id)})
    if not vendor_obj:
        return redirect(url_for('view_comparison'))
    # PO number
    po_count = purchase_orders.count_documents({}) + 1
    po_number = f"PO{po_count:03d}"
    purchase_orders.insert_one({
        "vendor_id": vendor_obj["_id"],
        "vendor_name": vendor_obj.get('vendor_name') or vendor_obj.get('companyName'),
        "po_number": po_number,
        "status": "Generated",
        "created_at": datetime.utcnow()
    })
    # Record approval
    approval_doc = {
        "vendor_id": vendor_obj["_id"],
        "status": "Approved",
        "created_at": datetime.utcnow()
    }
    # Optionally store RFQ reference if available in form
    if 'rfq_id' in request.form:
        approval_doc["rfq_id"] = request.form.get('rfq_id')
    approval_id = approvals.insert_one(approval_doc).inserted_id
    # Insert initial timeline event
    approval_events.insert_one({
        "approval_id": approval_id,
        "event": "Approved",
        "timestamp": datetime.utcnow(),
        "remarks": "Vendor approved"
    })
    # Redirect to detailed approval view
    return redirect(url_for('view_approval', approval_id=str(approval_id)))


@app.route("/approval/<approval_id>")
def view_approval(approval_id):
    from bson.objectid import ObjectId
    approval = approvals.find_one({"_id": ObjectId(approval_id)})
    if not approval:
        return redirect(url_for('dashboard'))
    vendor = vendors.find_one({"_id": approval.get("vendor_id")})
    approval_data = {
        "rfq_id": approval.get("rfq_id"),
        "vendor_name": vendor.get("vendor_name") if vendor else "",
        "quotation_value": approval.get("quotation_value", ""),
        "status": approval.get("status")
    }
    events = list(approval_events.find({"approval_id": ObjectId(approval_id)}).sort("timestamp", 1))
    return render_template("approval workflow.html", approval=approval_data, events=events)

@app.route("/activity-logs")
def view_activity_logs():
    activity_logs = db["activityLogs"]
    return render_template("activity-logs-notifications.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)