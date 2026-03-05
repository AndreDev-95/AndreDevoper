import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import axios from 'axios';
import { 
  TrendingUp, 
  TrendingDown, 
  Euro, 
  CreditCard, 
  FolderKanban, 
  Users,
  ArrowUpRight,
  ArrowDownRight,
  BarChart3,
  PieChart
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Simple Bar Chart Component
const SimpleBarChart = ({ data, dataKey, labelKey, color = '#3b82f6' }) => {
  const maxValue = Math.max(...data.map(d => d[dataKey]), 1);
  
  return (
    <div className="flex items-end gap-2 h-40">
      {data.map((item, index) => (
        <div key={index} className="flex flex-col items-center flex-1">
          <div 
            className="w-full rounded-t transition-all duration-300 hover:opacity-80"
            style={{ 
              height: `${(item[dataKey] / maxValue) * 100}%`,
              backgroundColor: color,
              minHeight: item[dataKey] > 0 ? '8px' : '2px'
            }}
          />
          <span className="text-xs text-muted-foreground mt-2 truncate w-full text-center">
            {item[labelKey]}
          </span>
        </div>
      ))}
    </div>
  );
};

// Simple Donut Chart Component  
const SimpleDonutChart = ({ data, colors }) => {
  const total = data.reduce((sum, item) => sum + item.count, 0);
  let cumulativePercent = 0;
  
  if (total === 0) {
    return (
      <div className="flex items-center justify-center h-40">
        <p className="text-muted-foreground text-sm">Sem dados</p>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-6">
      <div className="relative w-32 h-32">
        <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
          {data.map((item, index) => {
            const percent = (item.count / total) * 100;
            const strokeDasharray = `${percent} ${100 - percent}`;
            const strokeDashoffset = -cumulativePercent;
            cumulativePercent += percent;
            
            return (
              <circle
                key={index}
                cx="18"
                cy="18"
                r="15.915"
                fill="none"
                stroke={colors[index % colors.length]}
                strokeWidth="3"
                strokeDasharray={strokeDasharray}
                strokeDashoffset={strokeDashoffset}
                className="transition-all duration-300"
              />
            );
          })}
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-2xl font-bold text-foreground">{total}</span>
        </div>
      </div>
      <div className="flex flex-col gap-2">
        {data.map((item, index) => (
          <div key={index} className="flex items-center gap-2">
            <div 
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: colors[index % colors.length] }}
            />
            <span className="text-sm text-muted-foreground">{item.type || item.status}</span>
            <span className="text-sm font-medium text-foreground ml-auto">{item.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default function AnalyticsDashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [revenueData, setRevenueData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { getAuthHeaders } = useAuth();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [analyticsRes, revenueRes] = await Promise.all([
          axios.get(`${API}/admin/analytics`, { headers: getAuthHeaders() }),
          axios.get(`${API}/admin/analytics/revenue`, { headers: getAuthHeaders() })
        ]);
        setAnalytics(analyticsRes.data);
        setRevenueData(revenueRes.data);
      } catch (error) {
        console.error('Error fetching analytics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-secondary"></div>
      </div>
    );
  }

  const statCards = [
    {
      label: 'Receita Total',
      value: `€${(revenueData?.total_revenue || 0).toLocaleString('pt-PT', { minimumFractionDigits: 2 })}`,
      icon: Euro,
      color: 'bg-green-500',
      trend: '+12%',
      trendUp: true
    },
    {
      label: 'Receita Pendente',
      value: `€${(revenueData?.pending_revenue || 0).toLocaleString('pt-PT', { minimumFractionDigits: 2 })}`,
      icon: CreditCard,
      color: 'bg-yellow-500',
      trend: revenueData?.pending_revenue > 0 ? 'A receber' : '-',
      trendUp: null
    },
    {
      label: 'Projetos Pagos',
      value: revenueData?.paid_projects || 0,
      icon: FolderKanban,
      color: 'bg-blue-500',
      trend: `${revenueData?.conversion_rate || 0}% conversão`,
      trendUp: true
    },
    {
      label: 'Valor Médio',
      value: `€${(revenueData?.average_project_value || 0).toLocaleString('pt-PT', { minimumFractionDigits: 2 })}`,
      icon: TrendingUp,
      color: 'bg-purple-500',
      trend: 'por projeto',
      trendUp: null
    }
  ];

  const typeColors = ['#3b82f6', '#22c55e', '#f59e0b'];
  const budgetColors = ['#f59e0b', '#22c55e', '#8b5cf6'];

  return (
    <div className="space-y-6" data-testid="analytics-dashboard">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, index) => (
          <div 
            key={index}
            className="bg-card border border-border p-5 rounded-xl shadow-sm hover:shadow-md transition-shadow"
            data-testid={`stat-card-${index}`}
          >
            <div className="flex items-start justify-between mb-3">
              <div className={`w-10 h-10 ${stat.color} rounded-lg flex items-center justify-center`}>
                <stat.icon className="w-5 h-5 text-white" />
              </div>
              {stat.trend && stat.trendUp !== null && (
                <div className={`flex items-center gap-1 text-xs font-medium ${stat.trendUp ? 'text-green-600' : 'text-red-600'}`}>
                  {stat.trendUp ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                  {stat.trend}
                </div>
              )}
            </div>
            <p className="text-2xl font-bold text-foreground">{stat.value}</p>
            <p className="text-sm text-muted-foreground">{stat.label}</p>
            {stat.trend && stat.trendUp === null && (
              <p className="text-xs text-muted-foreground mt-1">{stat.trend}</p>
            )}
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Chart */}
        <div className="bg-card border border-border p-6 rounded-xl shadow-sm">
          <div className="flex items-center gap-2 mb-6">
            <BarChart3 className="w-5 h-5 text-secondary" />
            <h3 className="font-semibold text-foreground">Receita por Mês</h3>
          </div>
          {revenueData?.revenue_by_month && (
            <SimpleBarChart 
              data={revenueData.revenue_by_month.slice(-6)} 
              dataKey="revenue" 
              labelKey="month"
              color="#22c55e"
            />
          )}
        </div>

        {/* Projects by Month Chart */}
        <div className="bg-card border border-border p-6 rounded-xl shadow-sm">
          <div className="flex items-center gap-2 mb-6">
            <BarChart3 className="w-5 h-5 text-secondary" />
            <h3 className="font-semibold text-foreground">Projetos por Mês</h3>
          </div>
          {analytics?.projects_by_month && (
            <SimpleBarChart 
              data={analytics.projects_by_month} 
              dataKey="count" 
              labelKey="month"
              color="#3b82f6"
            />
          )}
        </div>

        {/* Projects by Type */}
        <div className="bg-card border border-border p-6 rounded-xl shadow-sm">
          <div className="flex items-center gap-2 mb-6">
            <PieChart className="w-5 h-5 text-secondary" />
            <h3 className="font-semibold text-foreground">Projetos por Tipo</h3>
          </div>
          {analytics?.projects_by_type && (
            <SimpleDonutChart 
              data={analytics.projects_by_type} 
              colors={typeColors}
            />
          )}
        </div>

        {/* Budget Distribution */}
        <div className="bg-card border border-border p-6 rounded-xl shadow-sm">
          <div className="flex items-center gap-2 mb-6">
            <PieChart className="w-5 h-5 text-secondary" />
            <h3 className="font-semibold text-foreground">Estado dos Orçamentos</h3>
          </div>
          {analytics?.budget_distribution && (
            <SimpleDonutChart 
              data={analytics.budget_distribution} 
              colors={budgetColors}
            />
          )}
        </div>
      </div>

      {/* Conversion Rate Card */}
      <div className="bg-gradient-to-r from-secondary to-secondary/80 p-6 rounded-xl text-white">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-white/80 text-sm mb-1">Taxa de Conversão</p>
            <p className="text-4xl font-bold">{revenueData?.conversion_rate || 0}%</p>
            <p className="text-white/60 text-sm mt-1">dos projetos resultam em pagamento</p>
          </div>
          <div className="w-20 h-20 bg-card/20 rounded-full flex items-center justify-center">
            <TrendingUp className="w-10 h-10" />
          </div>
        </div>
      </div>
    </div>
  );
}
