from datetime import datetime
from hashlib import new
from unicodedata import category

from pymongo import MongoClient

client = MongoClient(
    "mongodb+srv://zeelrikeshshah2006_db_user:Zeel123@cluster0.oeaqtyt.mongodb.net/?appName=Cluster0"
)

db = client["vendorbridge"]

print("Connected Successfully")

users = db["users"]

users.insert_one({
    "userId": "U001",
    "firstName": "Admin",
    "lastName": "User",
    "email": "admin@vendorbridge.com",
    "phone": "9876543210",
    "password": "admin123",
    "role": "Admin",
    "country": "India",
    "status": "Active",
    "createdAt": datetime.now()
})

print("Data Inserted")

vendors = db["vendors"]

vendors.insert_one({
    "vendorId": "V001",
    "companyName": "ABC Technologies",
    "contactPerson": "Raj Patel",
    "email": "abc@gmail.com",
    "phone": "9876543210",
    "category": "IT Equipment",
    "address": "Ahmedabad",
    "rating": 4.5,
    "status": "Approved"
})

rfqs = db["rfqs"]

rfqs.insert_one({
    "rfqId": "RFQ001",
    "title": "Office Furniture Procurement",
    "category": "Furniture",
    "quantity": 100,
    "description": "Office chairs and tables required",
    "priority": "High",
    "submissionDeadline": datetime(2026, 7, 1),
    "createdBy": {
        "userId": "U001",
        "name": "Admin User"
    },
    "assignedVendors": [
        "V001",
        "V002"
    ],
    "attachment": "quotation.pdf",
    "status": "Open",
    "createdAt": datetime.now()
})

quotations = db["quotations"]


quotations.insert_one({
    "quotationId": "Q001",
    "rfqId": "RFQ001",
    "vendorId": "V001",
    "vendorName": "ABC Technologies",
    "quotedAmount": 450000,
    "deliveryDays": 10,
    "remarks": "Includes installation",
    "status": "Submitted",
    "submittedAt": datetime.now()
})

approvals = db["approvals"]
approvals.insert_one({
    "approvalId": "AP001",
    "rfqId": "RFQ001",
    "approverId": "U003",
    "approverName": "Procurement Manager",
    "status": "Pending",
    "comments": "",
    "createdAt": datetime.now()
})

purchaseOrders = db["purchaseOrders"]
purchaseOrders.insert_one({
    "poId": "PO001",
    "rfqId": "RFQ001",
    "vendorId": "V001",
    "vendorName": "ABC Technologies",
    "amount": 450000,
    "status": "Pending Approval",
    "createdAt": datetime.now()
})


activityLogs = db["activityLogs"]
activityLogs.insert_one({
    "logId": "LOG001",
    "userId": "U001",
    "action": "Created RFQ",
    "referenceId": "RFQ001",
    "timestamp": datetime.now()
})

notifications = db["notifications"]

notifications.insert_one({
  "notificationId": "N001",
  "title": "New Vendor Added",
  "message": "ABC Electronics added successfully",
  "status": "Unread",
  "createdAt": datetime.now()
})