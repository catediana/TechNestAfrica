1.PROJECT OVERVIEW
A Django-powered web platform for managing a poultry farming business. It allows customers to:

View available poultry products

Place online orders

Receive confirmation messages (via future APIs like WhatsApp/SMS/Email)

(Later) Make payments via M-Pesa or other mobile integrations

1.1 And allows admins to:

Manage product listings and orders

Track inventory

Update prices and availability

View reports on orders and customer details

1.2 🌱 Vision & Mission
Vision:
To be Africa’s leading tech-enabled poultry farming company, revolutionizing agribusiness and empowering women in tech.

Mission:
To provide quality poultry products and digital services through smart farming, online ordering, and tech-driven operations that encourage innovation, inclusion, and sustainability.🌱 Vision & Mission
Vision:
To be Africa’s leading tech-enabled poultry farming company, revolutionizing agribusiness and empowering women in tech.

Mission:
To provide quality poultry products and digital services through smart farming, online ordering, and tech-driven operations that encourage innovation, inclusion, and sustainability.

1.3🧱 CORE DJANGO APPS
1. products
Handles:

Product listings (eggs, broilers, layers, manure, feeds)

Categories

Product availability and pricing

Images/descriptions

2. orders
Handles:

Order placement form

Order tracking

Customer information

Quantity and pricing per product

Order status (Pending, Fulfilled, Canceled)

3. dashboard (optional but recommended)
Handles:

Admin dashboard interface (could use Django admin or a custom one)

Product & order analytics

Inventory alerts

Reports

4. blog (optional for marketing/engagement)
Handles:

Poultry tips and articles

Success stories

Business updates

1.4 ROUTES & PAGES
Page	URL	Purpose
Home	/	Landing page showing company intro
Products	/products/	Show all products
Order	/orders/place/	Order form
Order Success	/orders/success/	Thank you page
Admin	/admin/	Django admin dashboard
Blog	/blog/	Posts and articles (optional)

1.5📡 EXTERNAL APIS (Planned Integrations)
API	Purpose	Notes
M-Pesa Daraja API	Accept mobile payments	To be integrated later
WhatsApp API (e.g. Twilio)	Send order confirmations	Optional
Email API (e.g. SendGrid)	Send confirmation emails	Optional
SMS API (e.g. Africa's Talking)	Notify users via text	Optional
Weather API	Optional feature to show poultry-friendly weather	Nice-to-have

1.6📷 PRODUCT CATEGORIES
These categories will be modeled in your Product model and shown on the products page:

Eggs (tray, half-tray)

Broiler Chicken

Layer Chicken

Manure (bags or bulk)

Feed (starter, grower, finisher)

1.7📦 FEATURES
✅ Customer Features
Browse products by category

View product details and images

Fill and submit order form

Get notified of order status (via page, SMS, or email later)

✅ Admin Features
Add/edit/delete products

Manage inventory (available/out of stock)

View and manage customer orders

Search and filter orders by date/product

View order history

1.8🔐 Authentication (Optional Early or Later)
Customer accounts (create account, login, view past orders)

Admin login (already handled by Django admin)

Optional: Staff roles (order managers, inventory keepers)



