import React, { useState, useEffect } from 'react';
import { Users, Car, Calendar, DollarSign, TrendingUp, TrendingDown } from 'lucide-react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar
} from 'recharts';
import { getDashboardStats } from '../../lib/api';

const REVENUE_DATA = [
  { name: 'Mon', revenue: 4000, rentals: 24 },
  { name: 'Tue', revenue: 3000, rentals: 18 },
  { name: 'Wed', revenue: 5500, rentals: 35 },
  { name: 'Thu', revenue: 4500, rentals: 28 },
  { name: 'Fri', revenue: 7000, rentals: 45 },
  { name: 'Sat', revenue: 9000, rentals: 60 },
  { name: 'Sun', revenue: 8500, rentals: 55 },
];

const Dashboard = () => {
  const [stats, setStats] = useState({
    total_customers: 0,
    total_vehicles: 0,
    active_rentals: 0,
    revenue: 0,
    utilization_pct: 0,
    available_vehicles: 0
  });
  
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getDashboardStats();
        setStats(data);
      } catch (error) {
        console.error("Failed to fetch dashboard stats:", error);
      }
    };
    fetchStats();
  }, []);

  const FLEET_STATUS = [
    { name: 'Available', value: stats.available_vehicles, color: '#10B981' },
    { name: 'Rented', value: stats.active_rentals, color: '#3B82F6' },
    { name: 'Maintenance', value: Math.max(0, stats.total_vehicles - stats.available_vehicles - stats.active_rentals), color: '#F59E0B' },
  ];
  return (
    <div className="pt-24 pb-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Admin Overview</h1>
        <p className="text-gray-400">Welcome back. Here's what's happening today.</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <KpiCard 
          title="Total Revenue" 
          value={`$${stats.revenue.toLocaleString()}`} 
          trend="+12.5%" 
          isPositive={true}
          icon={<DollarSign className="w-6 h-6 text-emerald-400" />}
          bgColor="bg-emerald-500/10"
        />
        <KpiCard 
          title="Active Rentals" 
          value={stats.active_rentals.toString()} 
          trend="+4.2%" 
          isPositive={true}
          icon={<Car className="w-6 h-6 text-blue-400" />}
          bgColor="bg-blue-500/10"
        />
        <KpiCard 
          title="Fleet Utilization" 
          value={`${stats.utilization_pct}%`} 
          trend="-2.1%" 
          isPositive={false}
          icon={<Calendar className="w-6 h-6 text-amber-400" />}
          bgColor="bg-amber-500/10"
        />
        <KpiCard 
          title="Total Customers" 
          value={stats.total_customers.toString()} 
          trend="+8.1%" 
          isPositive={true}
          icon={<Users className="w-6 h-6 text-purple-400" />}
          bgColor="bg-purple-500/10"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
        {/* Main Revenue Chart */}
        <div className="glass-card p-6 lg:col-span-2">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold text-white">Revenue (Last 7 Days)</h3>
            <select className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option>Last 7 Days</option>
              <option>Last 30 Days</option>
              <option>This Year</option>
            </select>
          </div>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={REVENUE_DATA} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3D7EFF" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3D7EFF" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="name" stroke="#9CA3AF" tick={{fill: '#9CA3AF', fontSize: 12}} tickLine={false} axisLine={false} />
                <YAxis stroke="#9CA3AF" tick={{fill: '#9CA3AF', fontSize: 12}} tickLine={false} axisLine={false} tickFormatter={(val) => `$${val/1000}k`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#111827', borderColor: '#1F2937', borderRadius: '8px', color: '#fff' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Area type="monotone" dataKey="revenue" stroke="#3D7EFF" strokeWidth={3} fillOpacity={1} fill="url(#colorRev)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Fleet Status */}
        <div className="glass-card p-6">
          <h3 className="text-lg font-bold text-white mb-6">Fleet Utilization</h3>
          <div className="h-48 w-full mb-6">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={FLEET_STATUS} layout="vertical" margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={true} vertical={false} />
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" stroke="#9CA3AF" tick={{fill: '#9CA3AF', fontSize: 12}} width={80} tickLine={false} axisLine={false} />
                <Tooltip cursor={{fill: 'rgba(255,255,255,0.05)'}} contentStyle={{ backgroundColor: '#111827', borderColor: '#1F2937', borderRadius: '8px' }} />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {FLEET_STATUS.map((entry, index) => (
                    <cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          
          <div className="space-y-3">
            {FLEET_STATUS.map((status) => (
              <div key={status.name} className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: status.color }}></div>
                  <span className="text-gray-300 text-sm">{status.name}</span>
                </div>
                <span className="font-bold text-white">{status.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      {/* Recent Activity Table */}
      <div className="glass-card overflow-hidden">
        <div className="p-6 border-b border-white/10 flex justify-between items-center">
          <h3 className="text-lg font-bold text-white">Recent Activity</h3>
          <button className="text-blue-400 text-sm hover:text-blue-300 font-medium transition-colors">View All</button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-white/5 border-b border-white/10">
                <th className="py-4 px-6 text-xs font-semibold text-gray-400 uppercase tracking-wider">Transaction ID</th>
                <th className="py-4 px-6 text-xs font-semibold text-gray-400 uppercase tracking-wider">Customer</th>
                <th className="py-4 px-6 text-xs font-semibold text-gray-400 uppercase tracking-wider">Vehicle</th>
                <th className="py-4 px-6 text-xs font-semibold text-gray-400 uppercase tracking-wider">Action</th>
                <th className="py-4 px-6 text-xs font-semibold text-gray-400 uppercase tracking-wider">Amount</th>
                <th className="py-4 px-6 text-xs font-semibold text-gray-400 uppercase tracking-wider">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10">
              <ActivityRow id="#TRX-8924" customer="Sarah Jenkins" vehicle="Porsche Taycan" action="Payment Completed" amount="$450.00" time="10 min ago" status="success" />
              <ActivityRow id="#RES-4421" customer="Michael Chen" vehicle="Tesla Model S" action="Reservation Created" amount="--" time="45 min ago" status="info" />
              <ActivityRow id="#RNT-3392" customer="Emma Watson" vehicle="Audi RS6" action="Rental Started (Pickup)" amount="--" time="2 hours ago" status="warning" />
              <ActivityRow id="#RNT-3351" customer="David Miller" vehicle="BMW M3" action="Rental Returned" amount="$285.00" time="5 hours ago" status="success" />
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Helper Components
const KpiCard = ({ title, value, trend, isPositive, icon, bgColor }) => (
  <div className="glass-card p-6 flex flex-col justify-between hover:-translate-y-1 transition-transform duration-300">
    <div className="flex justify-between items-start mb-4">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${bgColor}`}>
        {icon}
      </div>
      <div className={`flex items-center gap-1 px-2 py-1 rounded-md text-xs font-bold ${isPositive ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
        {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
        {trend}
      </div>
    </div>
    <div>
      <p className="text-3xl font-bold text-white mb-1">{value}</p>
      <p className="text-sm font-medium text-gray-400">{title}</p>
    </div>
  </div>
);

const ActivityRow = ({ id, customer, vehicle, action, amount, time, status }) => {
  const getStatusColor = () => {
    switch(status) {
      case 'success': return 'text-emerald-400';
      case 'warning': return 'text-amber-400';
      case 'error': return 'text-red-400';
      default: return 'text-blue-400';
    }
  };

  return (
    <tr className="hover:bg-white/5 transition-colors">
      <td className="py-4 px-6 text-sm font-mono text-gray-300">{id}</td>
      <td className="py-4 px-6 text-sm font-medium text-white">{customer}</td>
      <td className="py-4 px-6 text-sm text-gray-300">{vehicle}</td>
      <td className={`py-4 px-6 text-sm font-medium ${getStatusColor()}`}>{action}</td>
      <td className="py-4 px-6 text-sm font-bold text-white">{amount}</td>
      <td className="py-4 px-6 text-sm text-gray-400">{time}</td>
    </tr>
  );
};

export default Dashboard;
