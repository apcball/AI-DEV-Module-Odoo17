{
    "name": "Sales Forecast Planning",
    "summary": "Forecast sales demand, allocate to orders, and track forecast accuracy",
    "version": "17.0.1.0.0",
    "category": "Sales",
    "author": "AI-DEV-Module-Odoo17",
    "website": "https://github.com/apcball/AI-DEV-Module-Odoo17",
    "depends": ["sale_management", "mail"],
    "data": [
        "security/sale_forecast_security.xml",
        "security/ir.model.access.csv",
        "data/sequence_data.xml",
        "views/forecast_plan_views.xml",
        "views/forecast_allocation_views.xml",
        "views/sale_order_views.xml",
        "views/menuitem.xml",
        "views/sale_forecast_dashboard.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "sale_forecast/static/src/dashboard/**/*",
            "sale_forecast/static/src/dashboard_action.js",
        ],
    },
    "application": True,
    "installable": True,
}
