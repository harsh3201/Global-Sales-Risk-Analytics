import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import axios from 'axios';
import './App.css';

// Import shadcn components
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Badge } from './components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Alert, AlertDescription } from './components/ui/alert';

// Import Recharts for data visualization
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

// Import Lucide icons
import {
  TrendingUp, TrendingDown, Users, DollarSign, AlertTriangle, Globe,
  BarChart3, PieChart as PieChartIcon, Calendar, Filter, Download,
  MapPin, Building, Target, Activity, Eye, ArrowUpRight, ArrowDownRight
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Color palette for charts
const COLORS = {
  primary: '#3b82f6',
  secondary: '#10b981',
  accent: '#f59e0b',
  danger: '#ef4444',
  warning: '#f97316',
  info: '#06b6d4',
  success: '#22c55e'
};

const CHART_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

// KPI Card Component
const KPICard = ({ title, value, change, icon: Icon, trend, suffix = '', prefix = '' }) => {
  const isPositive = change >= 0;
  const TrendIcon = isPositive ? ArrowUpRight : ArrowDownRight;
  
  return (
    <Card className="overflow-hidden border-0 shadow-lg bg-gradient-to-br from-white to-gray-50 hover:shadow-xl transition-all duration-300">
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-600 uppercase tracking-wide">{title}</p>
            <div className="flex items-baseline space-x-1">
              <p className="text-3xl font-bold text-gray-900">
                {prefix}{typeof value === 'number' ? value.toLocaleString() : value}{suffix}
              </p>
              {change !== undefined && (
                <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${
                  isPositive 
                    ? 'bg-emerald-100 text-emerald-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  <TrendIcon className="w-3 h-3" />
                  <span>{Math.abs(change)}%</span>
                </div>
              )}
            </div>
          </div>
          <div className={`p-3 rounded-xl bg-gradient-to-br ${
            trend === 'up' ? 'from-emerald-500 to-emerald-600' :
            trend === 'down' ? 'from-red-500 to-red-600' :
            'from-blue-500 to-blue-600'
          }`}>
            <Icon className="w-6 h-6 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Dashboard Component
const Dashboard = () => {
  const [kpis, setKpis] = useState(null);
  const [regionalData, setRegionalData] = useState([]);
  const [salesTrends, setSalesTrends] = useState([]);
  const [riskAnalysis, setRiskAnalysis] = useState([]);
  const [forecast, setForecast] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedRegion, setSelectedRegion] = useState('all');
  const [selectedPeriod, setSelectedPeriod] = useState('monthly');

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [kpisRes, regionalRes, trendsRes, riskRes, forecastRes] = await Promise.all([
        axios.get(`${API}/kpis`),
        axios.get(`${API}/regional-summary`),
        axios.get(`${API}/sales-trends?period=${selectedPeriod}${selectedRegion !== 'all' ? `&region=${selectedRegion}` : ''}`),
        axios.get(`${API}/customer-risk-analysis`),
        axios.get(`${API}/forecast?months=6`)
      ]);

      setKpis(kpisRes.data);
      setRegionalData(regionalRes.data);
      setSalesTrends(trendsRes.data);
      setRiskAnalysis(riskRes.data);
      setForecast(forecastRes.data);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to load dashboard data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const generateData = async () => {
    try {
      setLoading(true);
      await axios.post(`${API}/generate-data`);
      await fetchData();
    } catch (err) {
      console.error('Error generating data:', err);
      setError('Failed to generate data. Please try again.');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedRegion, selectedPeriod]);

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-8">
        <div className="max-w-7xl mx-auto">
          <Alert className="border-red-200 bg-red-50">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">
              {error}
            </AlertDescription>
          </Alert>
          <div className="mt-6 text-center">
            <Button onClick={generateData} className="bg-blue-600 hover:bg-blue-700">
              Generate Sample Data
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-gray-600 font-medium">Loading analytics dashboard...</p>
        </div>
      </div>
    );
  }

  // Risk distribution data for pie chart
  const riskDistribution = riskAnalysis.reduce((acc, customer) => {
    acc[customer.risk_category] = (acc[customer.risk_category] || 0) + 1;
    return acc;
  }, {});

  const riskChartData = Object.entries(riskDistribution).map(([category, count]) => ({
    name: category,
    value: count,
    color: category === 'High' ? COLORS.danger : category === 'Medium' ? COLORS.warning : COLORS.success
  }));

  // Regional performance data for bar chart
  const regionalChartData = regionalData.map(region => ({
    region: region.region,
    revenue: region.total_revenue,
    orders: region.total_orders,
    risk_exposure: region.risk_exposure
  }));

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header Section */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <h1 className="text-3xl font-bold text-gray-900 tracking-tight">
                Global Sales & Risk Analytics
              </h1>
              <p className="text-gray-600 font-medium">
                Real-time insights across APAC, EMEA, and Americas regions
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <Select value={selectedRegion} onValueChange={setSelectedRegion}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Select region" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Regions</SelectItem>
                  <SelectItem value="APAC">APAC</SelectItem>
                  <SelectItem value="EMEA">EMEA</SelectItem>
                  <SelectItem value="Americas">Americas</SelectItem>
                </SelectContent>
              </Select>
              <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Period" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="monthly">Monthly</SelectItem>
                  <SelectItem value="quarterly">Quarterly</SelectItem>
                  <SelectItem value="yearly">Yearly</SelectItem>
                </SelectContent>
              </Select>
              <Button onClick={() => window.location.reload()} variant="outline" className="flex items-center space-x-2">
                <Activity className="w-4 h-4" />
                <span>Refresh</span>
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-8 space-y-8">
        {/* KPI Cards */}
        {kpis && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <KPICard
              title="Total Revenue"
              value={kpis.total_revenue}
              change={kpis.revenue_growth}
              icon={DollarSign}
              trend={kpis.revenue_growth >= 0 ? 'up' : 'down'}
              prefix="$"
            />
            <KPICard
              title="Total Orders"
              value={kpis.total_orders}
              icon={Target}
              trend="neutral"
            />
            <KPICard
              title="Avg Deal Size"
              value={kpis.avg_deal_size}
              icon={TrendingUp}
              trend="up"
              prefix="$"
            />
            <KPICard
              title="High Risk Customers"
              value={kpis.high_risk_customers}
              icon={AlertTriangle}
              trend="down"
            />
          </div>
        )}

        {/* Main Dashboard Tabs */}
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 lg:w-fit">
            <TabsTrigger value="overview" className="flex items-center space-x-2">
              <BarChart3 className="w-4 h-4" />
              <span>Overview</span>
            </TabsTrigger>
            <TabsTrigger value="regional" className="flex items-center space-x-2">
              <Globe className="w-4 h-4" />
              <span>Regional</span>
            </TabsTrigger>
            <TabsTrigger value="risk" className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4" />
              <span>Risk Analysis</span>
            </TabsTrigger>
            <TabsTrigger value="forecast" className="flex items-center space-x-2">
              <TrendingUp className="w-4 h-4" />
              <span>Forecast</span>
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Sales Trends Chart */}
              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <TrendingUp className="w-5 h-5 text-blue-600" />
                    <span>Sales Trends</span>
                  </CardTitle>
                  <CardDescription>Revenue and order trends over time</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={salesTrends}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="period" />
                      <YAxis />
                      <Tooltip formatter={(value, name) => [`$${value.toLocaleString()}`, name]} />
                      <Area
                        type="monotone"
                        dataKey="revenue"
                        stroke={COLORS.primary}
                        fill={COLORS.primary}
                        fillOpacity={0.3}
                        name="Revenue"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Regional Performance */}
              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Globe className="w-5 h-5 text-green-600" />
                    <span>Regional Performance</span>
                  </CardTitle>
                  <CardDescription>Revenue comparison across regions</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={regionalChartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="region" />
                      <YAxis />
                      <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
                      <Bar dataKey="revenue" fill={COLORS.secondary} radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>

            {/* Top Regions Table */}
            {kpis && kpis.top_regions.length > 0 && (
              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <MapPin className="w-5 h-5 text-orange-600" />
                    <span>Top Performing Regions</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {kpis.top_regions.map((region, index) => (
                      <div key={region.region} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div className="flex items-center space-x-4">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm ${
                            index === 0 ? 'bg-yellow-500' : index === 1 ? 'bg-gray-400' : 'bg-orange-600'
                          }`}>
                            {index + 1}
                          </div>
                          <div>
                            <h4 className="font-semibold text-gray-900">{region.region}</h4>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-lg text-gray-900">${region.revenue.toLocaleString()}</p>
                          <p className="text-sm text-gray-600">Revenue</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Regional Tab */}
          <TabsContent value="regional" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {regionalData.map((region) => (
                <Card key={region.region} className="border-0 shadow-lg overflow-hidden">
                  <CardHeader className={`bg-gradient-to-r ${
                    region.region === 'APAC' ? 'from-blue-500 to-blue-600' :
                    region.region === 'EMEA' ? 'from-green-500 to-green-600' :
                    'from-orange-500 to-orange-600'
                  } text-white`}>
                    <CardTitle className="flex items-center justify-between">
                      <span>{region.region}</span>
                      <Globe className="w-6 h-6" />
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-6 space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-600">Revenue</p>
                        <p className="text-xl font-bold text-gray-900">${region.total_revenue.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Orders</p>
                        <p className="text-xl font-bold text-gray-900">{region.total_orders.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Avg Deal</p>
                        <p className="text-xl font-bold text-gray-900">${region.avg_deal_size.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Risk Exposure</p>
                        <p className="text-xl font-bold text-red-600">${region.risk_exposure.toLocaleString()}</p>
                      </div>
                    </div>
                    
                    <div className="pt-4 border-t">
                      <h4 className="font-semibold text-gray-900 mb-2">Countries</h4>
                      <div className="flex flex-wrap gap-1">
                        {region.countries.map((country) => (
                          <Badge key={country} variant="secondary" className="text-xs">
                            {country}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <div className="pt-4 border-t">
                      <h4 className="font-semibold text-gray-900 mb-2">Top Customers</h4>
                      <div className="space-y-2">
                        {region.top_customers.slice(0, 3).map((customer, index) => (
                          <div key={index} className="flex justify-between text-sm">
                            <span className="text-gray-600 truncate">{customer.name}</span>
                            <span className="font-medium text-gray-900">${customer.revenue.toLocaleString()}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Risk Analysis Tab */}
          <TabsContent value="risk" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Risk Distribution Pie Chart */}
              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <PieChartIcon className="w-5 h-5 text-red-600" />
                    <span>Risk Distribution</span>
                  </CardTitle>
                  <CardDescription>Customer distribution by risk category</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={riskChartData}
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        dataKey="value"
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      >
                        {riskChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Risk Metrics */}
              <Card className="border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <AlertTriangle className="w-5 h-5 text-yellow-600" />
                    <span>Risk Metrics</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {Object.entries(riskDistribution).map(([category, count]) => (
                    <div key={category} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className={`w-4 h-4 rounded-full ${
                          category === 'High' ? 'bg-red-500' :
                          category === 'Medium' ? 'bg-yellow-500' :
                          'bg-green-500'
                        }`}></div>
                        <span className="font-medium text-gray-900">{category} Risk</span>
                      </div>
                      <span className="font-bold text-gray-900">{count} customers</span>
                    </div>
                  ))}
                  
                  {kpis && (
                    <div className="pt-4 border-t">
                      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                        <div className="flex items-center space-x-2">
                          <AlertTriangle className="w-5 h-5 text-red-600" />
                          <span className="font-semibold text-red-800">Overdue Payments</span>
                        </div>
                        <p className="text-2xl font-bold text-red-900 mt-2">
                          ${kpis.overdue_payments.toLocaleString()}
                        </p>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* High Risk Customers Table */}
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Users className="w-5 h-5 text-red-600" />
                  <span>High Risk Customers</span>
                </CardTitle>
                <CardDescription>Customers requiring immediate attention</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-3 px-4 font-semibold text-gray-900">Customer</th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-900">Region</th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-900">Risk Score</th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-900">Total Revenue</th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-900">Days Since Last Order</th>
                      </tr>
                    </thead>
                    <tbody>
                      {riskAnalysis
                        .filter(customer => customer.risk_category === 'High')
                        .slice(0, 10)
                        .map((customer, index) => (
                        <tr key={index} className="border-b hover:bg-gray-50">
                          <td className="py-3 px-4">
                            <div>
                              <p className="font-medium text-gray-900">{customer.customer_name}</p>
                              <p className="text-sm text-gray-600">{customer.country}</p>
                            </div>
                          </td>
                          <td className="py-3 px-4">
                            <Badge variant="outline">{customer.region}</Badge>
                          </td>
                          <td className="py-3 px-4">
                            <div className="flex items-center space-x-2">
                              <span className="font-bold text-red-600">{customer.risk_score.toFixed(1)}</span>
                              <div className="w-16 h-2 bg-gray-200 rounded-full">
                                <div 
                                  className="h-2 bg-red-500 rounded-full" 
                                  style={{ width: `${Math.min(customer.risk_score, 100)}%` }}
                                ></div>
                              </div>
                            </div>
                          </td>
                          <td className="py-3 px-4 font-medium text-gray-900">
                            ${customer.total_revenue.toLocaleString()}
                          </td>
                          <td className="py-3 px-4">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                              customer.days_since_last_order > 180 ? 'bg-red-100 text-red-800' :
                              customer.days_since_last_order > 90 ? 'bg-yellow-100 text-yellow-800' :
                              'bg-green-100 text-green-800'
                            }`}>
                              {customer.days_since_last_order} days
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Forecast Tab */}
          <TabsContent value="forecast" className="space-y-6">
            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <TrendingUp className="w-5 h-5 text-purple-600" />
                  <span>Sales Forecast</span>
                </CardTitle>
                <CardDescription>6-month revenue projection with confidence intervals</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={forecast}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="period" />
                    <YAxis />
                    <Tooltip 
                      formatter={(value, name) => [
                        value ? `$${value.toLocaleString()}` : 'N/A', 
                        name
                      ]} 
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="actual_revenue"
                      stroke={COLORS.primary}
                      strokeWidth={3}
                      dot={{ r: 5 }}
                      name="Actual Revenue"
                      connectNulls={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="forecasted_revenue"
                      stroke={COLORS.accent}
                      strokeWidth={3}
                      strokeDasharray="5 5"
                      dot={{ r: 5, fill: COLORS.accent }}
                      name="Forecasted Revenue"
                      connectNulls={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Forecast Summary */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <Card className="border-0 shadow-lg bg-gradient-to-br from-blue-50 to-blue-100">
                <CardContent className="p-6 text-center">
                  <TrendingUp className="w-12 h-12 text-blue-600 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-blue-900 mb-2">Next Month Forecast</h3>
                  <p className="text-3xl font-bold text-blue-800">
                    ${forecast.find(f => f.forecasted_revenue)?.forecasted_revenue?.toLocaleString() || 'N/A'}
                  </p>
                </CardContent>
              </Card>

              <Card className="border-0 shadow-lg bg-gradient-to-br from-green-50 to-green-100">
                <CardContent className="p-6 text-center">
                  <Target className="w-12 h-12 text-green-600 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-green-900 mb-2">6-Month Total</h3>
                  <p className="text-3xl font-bold text-green-800">
                    ${forecast
                      .filter(f => f.forecasted_revenue)
                      .reduce((sum, f) => sum + f.forecasted_revenue, 0)
                      .toLocaleString()}
                  </p>
                </CardContent>
              </Card>

              <Card className="border-0 shadow-lg bg-gradient-to-br from-purple-50 to-purple-100">
                <CardContent className="p-6 text-center">
                  <Activity className="w-12 h-12 text-purple-600 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-purple-900 mb-2">Confidence</h3>
                  <p className="text-3xl font-bold text-purple-800">85%</p>
                  <p className="text-sm text-purple-700 mt-2">Based on 24-month trend</p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

// Analytics Navigation Component
const AnalyticsNav = () => {
  const location = useLocation();
  
  const navItems = [
    { path: '/', label: 'Dashboard', icon: BarChart3 },
    { path: '/regional', label: 'Regional Analysis', icon: Globe },
    { path: '/customers', label: 'Customer Analytics', icon: Users },
    { path: '/reports', label: 'Reports', icon: Download }
  ];

  return (
    <nav className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-8">
        <div className="flex space-x-8">
          {navItems.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              className={`flex items-center space-x-2 py-4 px-2 border-b-2 font-medium text-sm transition-colors duration-200 ${
                location.pathname === path
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{label}</span>
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
};

// Main App Component
function App() {
  return (
    <BrowserRouter>
      <div className="App">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/regional" element={<Dashboard />} />
          <Route path="/customers" element={<Dashboard />} />
          <Route path="/reports" element={<Dashboard />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;