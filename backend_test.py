import requests
import sys
import json
from datetime import datetime

class SalesAnalyticsAPITester:
    def __init__(self, base_url="https://salesrisk-dash.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status=200, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            else:
                print(f"❌ Unsupported method: {method}")
                return False, {}

            print(f"   Status Code: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(response_data) > 0:
                        print(f"   Response keys: {list(response_data.keys())}")
                    elif isinstance(response_data, list) and len(response_data) > 0:
                        print(f"   Response: List with {len(response_data)} items")
                    return True, response_data
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                self.failed_tests.append(f"{name}: {response.status_code} - {response.text[:100]}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout after {timeout}s")
            self.failed_tests.append(f"{name}: Timeout")
            return False, {}
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Failed - Connection error: {str(e)}")
            self.failed_tests.append(f"{name}: Connection error")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append(f"{name}: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test("Root API", "GET", "")

    def test_generate_data(self):
        """Test data generation endpoint"""
        return self.run_test("Generate Data", "POST", "generate-data", expected_status=200)

    def test_kpis(self):
        """Test KPIs endpoint"""
        success, data = self.run_test("KPIs", "GET", "kpis")
        if success and data:
            required_fields = ['total_revenue', 'total_orders', 'avg_deal_size', 'revenue_growth', 'high_risk_customers', 'overdue_payments', 'top_regions']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                print(f"   ⚠️  Missing fields: {missing_fields}")
            else:
                print(f"   ✅ All required KPI fields present")
        return success, data

    def test_regional_summary(self):
        """Test regional summary endpoint"""
        success, data = self.run_test("Regional Summary", "GET", "regional-summary")
        if success and data:
            if isinstance(data, list) and len(data) > 0:
                regions = [item.get('region') for item in data]
                print(f"   Regions found: {regions}")
            else:
                print(f"   ⚠️  No regional data returned")
        return success, data

    def test_sales_trends(self):
        """Test sales trends endpoint with different parameters"""
        # Test default
        success1, data1 = self.run_test("Sales Trends (Default)", "GET", "sales-trends")
        
        # Test with period parameter
        success2, data2 = self.run_test("Sales Trends (Monthly)", "GET", "sales-trends?period=monthly")
        
        # Test with region parameter
        success3, data3 = self.run_test("Sales Trends (APAC)", "GET", "sales-trends?region=APAC")
        
        return success1 and success2 and success3, data1

    def test_customer_risk_analysis(self):
        """Test customer risk analysis endpoint"""
        # Test default
        success1, data1 = self.run_test("Customer Risk Analysis (All)", "GET", "customer-risk-analysis")
        
        # Test with risk category filter
        success2, data2 = self.run_test("Customer Risk Analysis (High Risk)", "GET", "customer-risk-analysis?risk_category=High")
        
        if success1 and data1:
            risk_categories = {}
            for customer in data1:
                category = customer.get('risk_category', 'Unknown')
                risk_categories[category] = risk_categories.get(category, 0) + 1
            print(f"   Risk distribution: {risk_categories}")
        
        return success1 and success2, data1

    def test_forecast(self):
        """Test sales forecast endpoint"""
        success, data = self.run_test("Sales Forecast", "GET", "forecast?months=6")
        if success and data:
            if isinstance(data, list):
                actual_count = len([item for item in data if item.get('actual_revenue')])
                forecast_count = len([item for item in data if item.get('forecasted_revenue')])
                print(f"   Historical periods: {actual_count}, Forecast periods: {forecast_count}")
        return success, data

    def test_country_performance(self):
        """Test country performance endpoint"""
        success, data = self.run_test("Country Performance", "GET", "country-performance")
        if success and data:
            if isinstance(data, list) and len(data) > 0:
                countries = [item.get('country') for item in data[:5]]
                print(f"   Top countries: {countries}")
        return success, data

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Global Sales & Risk Analytics API Tests")
        print("=" * 60)
        
        # Test basic connectivity first
        print("\n📡 Testing Basic Connectivity...")
        root_success, _ = self.test_root_endpoint()
        
        if not root_success:
            print("\n❌ Basic connectivity failed. Cannot proceed with other tests.")
            return self.print_summary()
        
        # Generate data first (if needed)
        print("\n📊 Testing Data Generation...")
        self.test_generate_data()
        
        # Test all endpoints
        print("\n📈 Testing Analytics Endpoints...")
        self.test_kpis()
        self.test_regional_summary()
        self.test_sales_trends()
        self.test_customer_risk_analysis()
        self.test_forecast()
        self.test_country_performance()
        
        return self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"   {i}. {failure}")
        else:
            print(f"\n✅ ALL TESTS PASSED!")
        
        print("=" * 60)
        return 0 if self.tests_passed == self.tests_run else 1

def main():
    tester = SalesAnalyticsAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())