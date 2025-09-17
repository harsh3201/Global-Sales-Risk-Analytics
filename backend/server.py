from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import random
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class SalesRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    region: str
    country: str
    customer_id: str
    customer_name: str
    product_category: str
    product_name: str
    sales_rep: str
    order_date: datetime
    revenue: float
    quantity: int
    deal_size: float
    currency: str
    payment_status: str
    payment_due_date: datetime
    days_overdue: int = 0

class CustomerProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    customer_name: str
    region: str
    country: str
    industry: str
    company_size: str
    total_revenue: float = 0.0
    avg_deal_size: float = 0.0
    payment_history_score: float = 0.0
    risk_score: float = 0.0
    risk_category: str = "Low"
    last_order_date: Optional[datetime] = None
    days_since_last_order: int = 0

class RegionalSummary(BaseModel):
    region: str
    total_revenue: float
    total_orders: int
    avg_deal_size: float
    risk_exposure: float
    top_customers: List[Dict[str, Any]]
    countries: List[str]

class KPIMetrics(BaseModel):
    total_revenue: float
    total_orders: int
    avg_deal_size: float
    revenue_growth: float
    high_risk_customers: int
    overdue_payments: float
    top_regions: List[Dict[str, Any]]

class ForecastData(BaseModel):
    period: str
    actual_revenue: Optional[float] = None
    forecasted_revenue: Optional[float] = None
    confidence_interval: Optional[Dict[str, float]] = None

# Generate comprehensive mock data
async def generate_mock_data():
    """Generate realistic sales and customer data for all regions"""
    
    # Clear existing data
    await db.sales_records.delete_many({})
    await db.customer_profiles.delete_many({})
    
    regions_data = {
        "APAC": {
            "countries": ["China", "Japan", "India", "Australia", "Singapore", "South Korea"],
            "currencies": ["CNY", "JPY", "INR", "AUD", "SGD", "KRW"]
        },
        "EMEA": {
            "countries": ["Germany", "UK", "France", "Italy", "Spain", "Netherlands"],
            "currencies": ["EUR", "GBP", "EUR", "EUR", "EUR", "EUR"]
        },
        "Americas": {
            "countries": ["USA", "Canada", "Brazil", "Mexico", "Argentina", "Chile"],
            "currencies": ["USD", "CAD", "BRL", "MXN", "ARS", "CLP"]
        }
    }
    
    products = [
        {"category": "Software", "products": ["CRM Suite", "Analytics Platform", "Security Solution", "ERP System"]},
        {"category": "Cloud Services", "products": ["Infrastructure", "Database", "AI/ML Platform", "CDN"]},
        {"category": "Consulting", "products": ["Digital Transformation", "Data Strategy", "Security Audit", "Training"]},
        {"category": "Hardware", "products": ["Servers", "Networking", "Storage", "IoT Devices"]}
    ]
    
    industries = ["Technology", "Finance", "Healthcare", "Manufacturing", "Retail", "Government", "Education"]
    company_sizes = ["Startup", "SMB", "Mid-Market", "Enterprise"]
    payment_statuses = ["Paid", "Pending", "Overdue", "Partially Paid"]
    
    sales_records = []
    customer_profiles = {}
    
    # Generate sales data for the last 24 months
    start_date = datetime.now(timezone.utc) - timedelta(days=730)
    
    for i in range(5000):  # Generate 5000 sales records
        region = random.choice(list(regions_data.keys()))
        country = random.choice(regions_data[region]["countries"])
        currency = regions_data[region]["currencies"][regions_data[region]["countries"].index(country)]
        
        customer_id = f"CUST_{region}_{random.randint(1000, 9999)}"
        customer_name = f"{random.choice(['Global', 'Digital', 'Smart', 'Tech', 'Future', 'Prime'])} {random.choice(['Solutions', 'Systems', 'Corp', 'Industries', 'Enterprises', 'Group'])}"
        
        product_cat = random.choice(products)
        product_name = random.choice(product_cat["products"])
        
        # Generate realistic date distribution (more recent = higher probability)
        days_ago = int(np.random.exponential(180))  # Exponential distribution for recency
        order_date = start_date + timedelta(days=min(days_ago, 729))
        
        # Generate revenue based on region and product
        base_revenue = {
            "Software": random.uniform(50000, 500000),
            "Cloud Services": random.uniform(10000, 200000),
            "Consulting": random.uniform(25000, 300000),
            "Hardware": random.uniform(30000, 400000)
        }[product_cat["category"]]
        
        # Regional multipliers
        regional_multiplier = {"APAC": 0.8, "EMEA": 1.2, "Americas": 1.0}[region]
        revenue = base_revenue * regional_multiplier * random.uniform(0.7, 1.3)
        
        quantity = random.randint(1, 50)
        deal_size = revenue / quantity
        
        # Payment status logic
        payment_status = random.choices(
            payment_statuses, 
            weights=[70, 15, 10, 5]  # Most are paid, some pending/overdue
        )[0]
        
        payment_due_date = order_date + timedelta(days=random.randint(30, 90))
        days_overdue = max(0, (datetime.now(timezone.utc) - payment_due_date).days) if payment_status == "Overdue" else 0
        
        sales_record = SalesRecord(
            region=region,
            country=country,
            customer_id=customer_id,
            customer_name=customer_name,
            product_category=product_cat["category"],
            product_name=product_name,
            sales_rep=f"{random.choice(['John', 'Sarah', 'Mike', 'Lisa', 'David', 'Emma'])} {random.choice(['Smith', 'Johnson', 'Brown', 'Davis', 'Wilson', 'Taylor'])}",
            order_date=order_date,
            revenue=round(revenue, 2),
            quantity=quantity,
            deal_size=round(deal_size, 2),
            currency=currency,
            payment_status=payment_status,
            payment_due_date=payment_due_date,
            days_overdue=days_overdue
        )
        
        sales_records.append(sales_record.dict())
        
        # Build customer profiles
        if customer_id not in customer_profiles:
            customer_profiles[customer_id] = {
                "customer_id": customer_id,
                "customer_name": customer_name,
                "region": region,
                "country": country,
                "industry": random.choice(industries),
                "company_size": random.choice(company_sizes),
                "orders": [],
                "total_revenue": 0,
                "overdue_count": 0
            }
        
        customer_profiles[customer_id]["orders"].append(sales_record.dict())
        customer_profiles[customer_id]["total_revenue"] += revenue
        if payment_status == "Overdue":
            customer_profiles[customer_id]["overdue_count"] += 1
    
    # Insert sales records
    if sales_records:
        await db.sales_records.insert_many(sales_records)
    
    # Process customer profiles and calculate risk scores
    customer_profile_docs = []
    for customer_id, profile in customer_profiles.items():
        orders = profile["orders"]
        total_revenue = profile["total_revenue"]
        order_count = len(orders)
        avg_deal_size = total_revenue / order_count if order_count > 0 else 0
        
        # Calculate payment history score (0-100)
        overdue_ratio = profile["overdue_count"] / order_count if order_count > 0 else 0
        payment_history_score = max(0, 100 - (overdue_ratio * 100))
        
        # Calculate days since last order
        order_dates = []
        for order in orders:
            if isinstance(order["order_date"], datetime):
                order_dates.append(order["order_date"])
            else:
                order_dates.append(datetime.fromisoformat(order["order_date"].replace('Z', '+00:00')))
        
        last_order_date = max(order_dates)
        days_since_last_order = (datetime.now(timezone.utc) - last_order_date).days
        
        # Calculate risk score (0-100, higher = more risky)
        recency_factor = min(days_since_last_order / 365, 1.0) * 30  # Up to 30 points for recency
        payment_factor = (100 - payment_history_score) * 0.4  # Up to 40 points for payment issues
        volatility_factor = random.uniform(0, 30)  # Up to 30 points for business volatility
        
        risk_score = recency_factor + payment_factor + volatility_factor
        
        # Categorize risk
        if risk_score < 30:
            risk_category = "Low"
        elif risk_score < 60:
            risk_category = "Medium"
        else:
            risk_category = "High"
        
        customer_profile = CustomerProfile(
            customer_id=customer_id,
            customer_name=profile["customer_name"],
            region=profile["region"],
            country=profile["country"],
            industry=profile["industry"],
            company_size=profile["company_size"],
            total_revenue=round(total_revenue, 2),
            avg_deal_size=round(avg_deal_size, 2),
            payment_history_score=round(payment_history_score, 1),
            risk_score=round(risk_score, 1),
            risk_category=risk_category,
            last_order_date=last_order_date,
            days_since_last_order=days_since_last_order
        )
        
        customer_profile_docs.append(customer_profile.dict())
    
    # Insert customer profiles
    if customer_profile_docs:
        await db.customer_profiles.insert_many(customer_profile_docs)
    
    return {"message": f"Generated {len(sales_records)} sales records and {len(customer_profile_docs)} customer profiles"}

# API Endpoints
@api_router.get("/")
async def root():
    return {"message": "Global Sales & Risk Analytics Dashboard API"}

@api_router.post("/generate-data")
async def generate_data():
    """Generate mock sales and customer data"""
    result = await generate_mock_data()
    return result

@api_router.get("/kpis", response_model=KPIMetrics)
async def get_kpis():
    """Get key performance indicators"""
    
    # Calculate current period (last 30 days) and previous period metrics
    current_date = datetime.now(timezone.utc)
    current_period_start = current_date - timedelta(days=30)
    previous_period_start = current_date - timedelta(days=60)
    previous_period_end = current_date - timedelta(days=30)
    
    # Current period metrics
    current_sales = await db.sales_records.find({
        "order_date": {"$gte": current_period_start}
    }, {"_id": 0}).to_list(length=None)
    
    # Previous period metrics
    previous_sales = await db.sales_records.find({
        "order_date": {"$gte": previous_period_start, "$lt": previous_period_end}
    }, {"_id": 0}).to_list(length=None)
    
    # Calculate metrics
    current_revenue = sum(record["revenue"] for record in current_sales)
    previous_revenue = sum(record["revenue"] for record in previous_sales)
    
    revenue_growth = ((current_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0
    
    total_orders = len(current_sales)
    avg_deal_size = current_revenue / total_orders if total_orders > 0 else 0
    
    # High risk customers
    high_risk_customers = await db.customer_profiles.count_documents({"risk_category": "High"})
    
    # Overdue payments
    overdue_records = await db.sales_records.find({"payment_status": "Overdue"}, {"_id": 0}).to_list(length=None)
    overdue_payments = sum(record["revenue"] for record in overdue_records)
    
    # Top regions by revenue (last 30 days)
    region_revenue = {}
    for record in current_sales:
        region = record["region"]
        if region not in region_revenue:
            region_revenue[region] = 0
        region_revenue[region] += record["revenue"]
    
    top_regions = [{"region": region, "revenue": revenue} for region, revenue in 
                   sorted(region_revenue.items(), key=lambda x: x[1], reverse=True)]
    
    return KPIMetrics(
        total_revenue=round(current_revenue, 2),
        total_orders=total_orders,
        avg_deal_size=round(avg_deal_size, 2),
        revenue_growth=round(revenue_growth, 1),
        high_risk_customers=high_risk_customers,
        overdue_payments=round(overdue_payments, 2),
        top_regions=top_regions
    )

@api_router.get("/regional-summary", response_model=List[RegionalSummary])
async def get_regional_summary():
    """Get regional performance summary"""
    
    regions = ["APAC", "EMEA", "Americas"]
    regional_summaries = []
    
    for region in regions:
        # Get sales data for the region
        sales_data = await db.sales_records.find({"region": region}, {"_id": 0}).to_list(length=None)
        customer_data = await db.customer_profiles.find({"region": region}, {"_id": 0}).to_list(length=None)
        
        if not sales_data:
            continue
            
        total_revenue = sum(record["revenue"] for record in sales_data)
        total_orders = len(sales_data)
        avg_deal_size = total_revenue / total_orders if total_orders > 0 else 0
        
        # Risk exposure (revenue from high-risk customers)
        high_risk_customer_ids = [c["customer_id"] for c in customer_data if c["risk_category"] == "High"]
        risk_exposure = sum(record["revenue"] for record in sales_data 
                           if record["customer_id"] in high_risk_customer_ids)
        
        # Top customers by revenue
        customer_revenue = {}
        for record in sales_data:
            customer_id = record["customer_id"]
            if customer_id not in customer_revenue:
                customer_revenue[customer_id] = {"name": record["customer_name"], "revenue": 0}
            customer_revenue[customer_id]["revenue"] += record["revenue"]
        
        top_customers = [{"name": data["name"], "revenue": data["revenue"]} for data in 
                        sorted(customer_revenue.values(), key=lambda x: x["revenue"], reverse=True)[:5]]
        
        # Countries in the region
        countries = list(set(record["country"] for record in sales_data))
        
        regional_summaries.append(RegionalSummary(
            region=region,
            total_revenue=round(total_revenue, 2),
            total_orders=total_orders,
            avg_deal_size=round(avg_deal_size, 2),
            risk_exposure=round(risk_exposure, 2),
            top_customers=top_customers,
            countries=countries
        ))
    
    return regional_summaries

@api_router.get("/sales-trends")
async def get_sales_trends(period: str = "monthly", region: Optional[str] = None):
    """Get sales trends over time"""
    
    # Build query
    query = {}
    if region:
        query["region"] = region
    
    # Get all sales data
    sales_data = await db.sales_records.find(query, {"_id": 0}).to_list(length=None)
    
    if not sales_data:
        return []
    
    # Process data by period
    trends = {}
    for record in sales_data:
        if isinstance(record["order_date"], datetime):
            order_date = record["order_date"]
        else:
            order_date = datetime.fromisoformat(record["order_date"].replace('Z', '+00:00'))
        
        if period == "monthly":
            period_key = order_date.strftime("%Y-%m")
        elif period == "quarterly":
            quarter = (order_date.month - 1) // 3 + 1
            period_key = f"{order_date.year}-Q{quarter}"
        else:  # yearly
            period_key = str(order_date.year)
        
        if period_key not in trends:
            trends[period_key] = {"revenue": 0, "orders": 0}
        
        trends[period_key]["revenue"] += record["revenue"]
        trends[period_key]["orders"] += 1
    
    # Convert to list and sort
    trend_list = [{"period": period, "revenue": data["revenue"], "orders": data["orders"]} 
                  for period, data in trends.items()]
    trend_list.sort(key=lambda x: x["period"])
    
    return trend_list

@api_router.get("/customer-risk-analysis")
async def get_customer_risk_analysis(risk_category: Optional[str] = None, region: Optional[str] = None):
    """Get detailed customer risk analysis"""
    
    query = {}
    if risk_category:
        query["risk_category"] = risk_category
    if region:
        query["region"] = region
    
    customers = await db.customer_profiles.find(query, {"_id": 0}).to_list(length=None)
    
    # Sort by risk score descending
    customers.sort(key=lambda x: x["risk_score"], reverse=True)
    
    return customers

@api_router.get("/forecast")
async def get_sales_forecast(months: int = 6):
    """Generate sales forecast using simple trend analysis"""
    
    # Get historical data (last 12 months)
    current_date = datetime.now(timezone.utc)
    start_date = current_date - timedelta(days=365)
    
    sales_data = await db.sales_records.find({
        "order_date": {"$gte": start_date}
    }, {"_id": 0}).to_list(length=None)
    
    if not sales_data:
        return []
    
    # Aggregate by month
    monthly_data = {}
    for record in sales_data:
        if isinstance(record["order_date"], datetime):
            order_date = record["order_date"]
        else:
            order_date = datetime.fromisoformat(record["order_date"].replace('Z', '+00:00'))
        month_key = order_date.strftime("%Y-%m")
        
        if month_key not in monthly_data:
            monthly_data[month_key] = 0
        monthly_data[month_key] += record["revenue"]
    
    # Sort months and get revenue values
    sorted_months = sorted(monthly_data.keys())
    revenues = [monthly_data[month] for month in sorted_months]
    
    if len(revenues) < 3:
        return []
    
    # Simple linear regression for forecasting
    x = np.arange(len(revenues))
    y = np.array(revenues)
    
    # Calculate trend
    coeffs = np.polyfit(x, y, 1)
    trend_slope = coeffs[0]
    trend_intercept = coeffs[1]
    
    # Generate forecast
    forecast_data = []
    
    # Add historical data
    for i, month in enumerate(sorted_months[-6:]):  # Last 6 months
        forecast_data.append(ForecastData(
            period=month,
            actual_revenue=revenues[sorted_months.index(month)],
            forecasted_revenue=None
        ))
    
    # Add forecasted data
    last_index = len(revenues) - 1
    for i in range(1, months + 1):
        forecast_month = (current_date + timedelta(days=30 * i)).strftime("%Y-%m")
        forecasted_value = trend_slope * (last_index + i) + trend_intercept
        
        # Add some realistic variance
        confidence_lower = forecasted_value * 0.8
        confidence_upper = forecasted_value * 1.2
        
        forecast_data.append(ForecastData(
            period=forecast_month,
            actual_revenue=None,
            forecasted_revenue=round(forecasted_value, 2),
            confidence_interval={
                "lower": round(confidence_lower, 2),
                "upper": round(confidence_upper, 2)
            }
        ))
    
    return forecast_data

@api_router.get("/country-performance")
async def get_country_performance(region: Optional[str] = None):
    """Get performance metrics by country"""
    
    query = {}
    if region:
        query["region"] = region
    
    sales_data = await db.sales_records.find(query, {"_id": 0}).to_list(length=None)
    customer_data = await db.customer_profiles.find(query, {"_id": 0}).to_list(length=None)
    
    # Aggregate by country
    country_metrics = {}
    for record in sales_data:
        country = record["country"]
        if country not in country_metrics:
            country_metrics[country] = {
                "country": country,
                "region": record["region"],
                "revenue": 0,
                "orders": 0,
                "customers": set()
            }
        
        country_metrics[country]["revenue"] += record["revenue"]
        country_metrics[country]["orders"] += 1
        country_metrics[country]["customers"].add(record["customer_id"])
    
    # Add risk metrics
    for customer in customer_data:
        country = customer["country"]
        if country in country_metrics:
            if "high_risk_customers" not in country_metrics[country]:
                country_metrics[country]["high_risk_customers"] = 0
            if customer["risk_category"] == "High":
                country_metrics[country]["high_risk_customers"] += 1
    
    # Convert to list format
    result = []
    for country_data in country_metrics.values():
        customer_count = len(country_data["customers"])
        result.append({
            "country": country_data["country"],
            "region": country_data["region"],
            "revenue": round(country_data["revenue"], 2),
            "orders": country_data["orders"],
            "customers": customer_count,
            "avg_deal_size": round(country_data["revenue"] / country_data["orders"], 2) if country_data["orders"] > 0 else 0,
            "high_risk_customers": country_data.get("high_risk_customers", 0)
        })
    
    # Sort by revenue descending
    result.sort(key=lambda x: x["revenue"], reverse=True)
    
    return result

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()