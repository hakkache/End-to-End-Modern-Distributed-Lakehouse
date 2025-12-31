import csv
import random
from datetime import datetime, timedelta
import itertools

# Configuration
NUM_CUSTOMER_EVENTS = 2_000_000
NUM_INVENTORY_SNAPSHOTS = 500_000
NUM_PAYMENT_TRANSACTIONS = 1_000_000
NUM_SUPPORT_TICKETS = 300_000

# Reference data
EVENT_TYPES = ['page_view', 'product_view', 'add_to_cart', 'remove_from_cart', 'checkout_start', 'purchase']
DEVICE_TYPES = ['desktop', 'mobile', 'tablet']
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    'Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X)'
]
REFERRER_SOURCES = ['google', 'facebook', 'instagram', 'direct', 'email', 'affiliate', 'bing', 'twitter']
PAYMENT_METHODS = ['credit_card', 'debit_card', 'paypal', 'apple_pay', 'google_pay', 'bank_transfer']
PAYMENT_STATUSES = ['completed', 'pending', 'failed', 'refunded', 'cancelled']
CURRENCIES = ['USD', 'EUR', 'GBP', 'CAD', 'AUD']
COUNTRIES = ['US', 'UK', 'CA', 'AU', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE']
TICKET_TYPES = ['order_issue', 'product_inquiry', 'shipping_delay', 'refund_request', 'technical_support', 'account_issue']
PRIORITIES = ['low', 'medium', 'high', 'urgent']
TICKET_STATUSES = ['open', 'in_progress', 'waiting_customer', 'resolved', 'closed']
CHANNELS = ['email', 'chat', 'phone', 'social_media']

def random_date(start, end):
    delta = end - start
    random_days = random.randint(0, delta.days)
    random_seconds = random.randint(0, 86400)
    return start + timedelta(days=random_days, seconds=random_seconds)

def generate_ip():
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"

def generate_customer_events(filename, num_rows):
    print(f"Generating {filename} with {num_rows:,} rows...")
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['event_id', 'customer_id', 'session_id', 'event_type', 'event_timestamp', 
                        'page_url', 'product_id', 'category_id', 'referrer_source', 'device_type', 
                        'user_agent', 'ip_address'])
        
        for i in range(1, num_rows + 1):
            event_id = f"EVT{i:09d}"
            customer_id = f"CUST{random.randint(1, 100000):06d}"
            session_id = f"SESS{random.randint(1, 500000):08d}"
            event_type = random.choice(EVENT_TYPES)
            event_timestamp = random_date(start_date, end_date).strftime('%Y-%m-%d %H:%M:%S')
            page_url = f"https://shop.example.com/{random.choice(['products', 'category', 'cart', 'checkout'])}/{random.randint(1, 1000)}"
            product_id = f"PROD{random.randint(1, 10000):05d}" if event_type in ['product_view', 'add_to_cart', 'remove_from_cart'] else ''
            category_id = f"CAT{random.randint(1, 100):03d}" if product_id else ''
            referrer_source = random.choice(REFERRER_SOURCES)
            device_type = random.choice(DEVICE_TYPES)
            user_agent = random.choice(USER_AGENTS)
            ip_address = generate_ip()
            
            writer.writerow([event_id, customer_id, session_id, event_type, event_timestamp,
                           page_url, product_id, category_id, referrer_source, device_type,
                           user_agent, ip_address])
            
            if i % 100000 == 0:
                print(f"  Progress: {i:,}/{num_rows:,} ({i/num_rows*100:.1f}%)")
    
    print(f"✓ {filename} completed\n")

def generate_inventory_snapshots(filename, num_rows):
    print(f"Generating {filename} with {num_rows:,} rows...")
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['snapshot_id', 'product_id', 'warehouse_id', 'snapshot_date', 'quantity_on_hand',
                        'quantity_reserved', 'quantity_available', 'reorder_point', 'reorder_quantity',
                        'supplier_id', 'last_received_date', 'unit_cost'])
        
        for i in range(1, num_rows + 1):
            snapshot_id = f"SNAP{i:09d}"
            product_id = f"PROD{random.randint(1, 10000):05d}"
            warehouse_id = f"WH{random.randint(1, 20):03d}"
            snapshot_date = random_date(start_date, end_date).strftime('%Y-%m-%d')
            quantity_on_hand = random.randint(0, 5000)
            quantity_reserved = random.randint(0, min(quantity_on_hand, 500))
            quantity_available = quantity_on_hand - quantity_reserved
            reorder_point = random.randint(50, 500)
            reorder_quantity = random.randint(100, 1000)
            supplier_id = f"SUP{random.randint(1, 200):04d}"
            last_received_date = random_date(start_date, end_date).strftime('%Y-%m-%d')
            unit_cost = round(random.uniform(5.0, 500.0), 2)
            
            writer.writerow([snapshot_id, product_id, warehouse_id, snapshot_date, quantity_on_hand,
                           quantity_reserved, quantity_available, reorder_point, reorder_quantity,
                           supplier_id, last_received_date, unit_cost])
            
            if i % 50000 == 0:
                print(f"  Progress: {i:,}/{num_rows:,} ({i/num_rows*100:.1f}%)")
    
    print(f"✓ {filename} completed\n")

def generate_payment_transactions(filename, num_rows):
    print(f"Generating {filename} with {num_rows:,} rows...")
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['transaction_id', 'order_id', 'customer_id', 'payment_method', 'payment_status',
                        'amount', 'currency', 'transaction_timestamp', 'processor_response_code',
                        'gateway_fee', 'merchant_id', 'billing_country', 'risk_score'])
        
        for i in range(1, num_rows + 1):
            transaction_id = f"TXN{i:09d}"
            order_id = f"ORD{i:09d}"
            customer_id = f"CUST{random.randint(1, 100000):06d}"
            payment_method = random.choice(PAYMENT_METHODS)
            payment_status = random.choice(PAYMENT_STATUSES)
            amount = round(random.uniform(10.0, 2000.0), 2)
            currency = random.choice(CURRENCIES)
            transaction_timestamp = random_date(start_date, end_date).strftime('%Y-%m-%d %H:%M:%S')
            processor_response_code = random.choice(['00', '01', '05', '51', '54', '61', '65']) if payment_status != 'completed' else '00'
            gateway_fee = round(amount * random.uniform(0.02, 0.04), 2)
            merchant_id = f"MERCH{random.randint(1, 50):04d}"
            billing_country = random.choice(COUNTRIES)
            risk_score = round(random.uniform(0, 100), 2)
            
            writer.writerow([transaction_id, order_id, customer_id, payment_method, payment_status,
                           amount, currency, transaction_timestamp, processor_response_code,
                           gateway_fee, merchant_id, billing_country, risk_score])
            
            if i % 100000 == 0:
                print(f"  Progress: {i:,}/{num_rows:,} ({i/num_rows*100:.1f}%)")
    
    print(f"✓ {filename} completed\n")

def generate_support_tickets(filename, num_rows):
    print(f"Generating {filename} with {num_rows:,} rows...")
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    
    subjects = [
        "Order not received", "Product defect", "Refund request", "Shipping delay",
        "Wrong item received", "Account login issue", "Payment failed", "Tracking not updating",
        "Cancel order request", "Product inquiry", "Billing question", "Damaged package"
    ]
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ticket_id', 'customer_id', 'order_id', 'ticket_type', 'priority', 'status',
                        'created_timestamp', 'first_response_timestamp', 'resolution_timestamp',
                        'agent_id', 'satisfaction_score', 'subject', 'channel'])
        
        for i in range(1, num_rows + 1):
            ticket_id = f"TKT{i:08d}"
            customer_id = f"CUST{random.randint(1, 100000):06d}"
            order_id = f"ORD{random.randint(1, 1000000):09d}" if random.random() > 0.2 else ''
            ticket_type = random.choice(TICKET_TYPES)
            priority = random.choice(PRIORITIES)
            status = random.choice(TICKET_STATUSES)
            created_timestamp = random_date(start_date, end_date)
            
            # Response times based on status
            first_response_timestamp = ''
            resolution_timestamp = ''
            if status != 'open':
                first_response_timestamp = (created_timestamp + timedelta(hours=random.randint(1, 48))).strftime('%Y-%m-%d %H:%M:%S')
            if status in ['resolved', 'closed']:
                resolution_timestamp = (created_timestamp + timedelta(days=random.randint(1, 14))).strftime('%Y-%m-%d %H:%M:%S')
            
            created_timestamp = created_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            agent_id = f"AGT{random.randint(1, 100):04d}" if status != 'open' else ''
            satisfaction_score = random.randint(1, 5) if status in ['resolved', 'closed'] else ''
            subject = random.choice(subjects)
            channel = random.choice(CHANNELS)
            
            writer.writerow([ticket_id, customer_id, order_id, ticket_type, priority, status,
                           created_timestamp, first_response_timestamp, resolution_timestamp,
                           agent_id, satisfaction_score, subject, channel])
            
            if i % 50000 == 0:
                print(f"  Progress: {i:,}/{num_rows:,} ({i/num_rows*100:.1f}%)")
    
    print(f"✓ {filename} completed\n")

# Generate all files
print("=" * 60)
print("E-COMMERCE DATA GENERATOR")
print("=" * 60)
print(f"Total records to generate: {NUM_CUSTOMER_EVENTS + NUM_INVENTORY_SNAPSHOTS + NUM_PAYMENT_TRANSACTIONS + NUM_SUPPORT_TICKETS:,}")
print("=" * 60 + "\n")

generate_customer_events('customer_events.csv', NUM_CUSTOMER_EVENTS)
generate_inventory_snapshots('inventory_snapshots.csv', NUM_INVENTORY_SNAPSHOTS)
generate_payment_transactions('payment_transactions.csv', NUM_PAYMENT_TRANSACTIONS)
generate_support_tickets('support_tickets.csv', NUM_SUPPORT_TICKETS)

print("=" * 60)
print("ALL FILES GENERATED SUCCESSFULLY!")
print("=" * 60)
print(f"✓ customer_events.csv - {NUM_CUSTOMER_EVENTS:,} rows")
print(f"✓ inventory_snapshots.csv - {NUM_INVENTORY_SNAPSHOTS:,} rows")
print(f"✓ payment_transactions.csv - {NUM_PAYMENT_TRANSACTIONS:,} rows")
print(f"✓ support_tickets.csv - {NUM_SUPPORT_TICKETS:,} rows")
print("=" * 60)