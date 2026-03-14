import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
import { dashboardApi, scanApi, reportApi } from '../services/api'
import { PageHeader, Card, StatCard, LoadingSpinner, SeverityBadge, StatusBadge } from '../components/ui'
import {
  DocumentMagnifyingGlassIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  UserGroupIcon,
  ArrowTrendingUpIcon,
  ClockIcon,
} from '@heroicons/react/24/outline'
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, PointElement, LineElement, Title } from 'chart.js'
import { Doughnut, Line } from 'react-chartjs-2'

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, PointElement, LineElement, Title)

export default function Dashboard() {
  const { user, isRadiologist, isDoctor } = useAuth()

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: () => dashboardApi.getStats(),
  })

  const { data: roleData, isLoading: roleLoading } = useQuery({
    queryKey: ['roleDashboard', user?.role],
    queryFn: () => isDoctor ? dashboardApi.getDoctor() : dashboardApi.getRadiologist(),
  })

  const { data: distribution } = useQuery({
    queryKey: ['severityDistribution'],
    queryFn: () => dashboardApi.getSeverityDistribution(30),
  })

  const { data: trend } = useQuery({
    queryKey: ['scanTrend'],
    queryFn: () => dashboardApi.getTrend(14),
  })

  if (statsLoading || roleLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  const statsData = stats?.data || {}
  const dashboardData = roleData?.data || {}

  // Chart data
  const severityChartData = {
    labels: ['None', 'Mild', 'Moderate', 'Severe'],
    datasets: [{
      data: distribution?.data ? [
        distribution.data.none,
        distribution.data.mild,
        distribution.data.moderate,
        distribution.data.severe,
      ] : [0, 0, 0, 0],
      backgroundColor: ['#9CA3AF', '#22C55E', '#F59E0B', '#EF4444'],
      borderColor: ['#6B7280', '#16A34A', '#D97706', '#DC2626'],
      borderWidth: 1,
    }],
  }

  const trendChartData = {
    labels: trend?.data?.map(d => d.date.slice(5)) || [],
    datasets: [
      {
        label: 'Total Scans',
        data: trend?.data?.map(d => d.total_scans) || [],
        borderColor: '#3B82F6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
      },
      {
        label: 'Positive Cases',
        data: trend?.data?.map(d => d.positive_cases) || [],
        borderColor: '#EF4444',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        fill: true,
      },
    ],
  }

  return (
    <div>
      <PageHeader
        title={`Welcome back, ${user?.full_name?.split(' ')[0] || 'User'}`}
        subtitle={`${user?.role === 'radiologist' ? 'Radiologist' : 'Doctor'} Dashboard`}
      />

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Scans"
          value={statsData.scans?.total_scans || 0}
          icon={DocumentMagnifyingGlassIcon}
        />
        <StatCard
          title="Hemorrhage Detected"
          value={statsData.scans?.hemorrhage_detected || 0}
          icon={ExclamationTriangleIcon}
          changeType={statsData.scans?.hemorrhage_detected > 0 ? 'negative' : 'neutral'}
        />
        <StatCard
          title="Reports Generated"
          value={statsData.reports?.total_reports || 0}
          icon={DocumentTextIcon}
        />
        <StatCard
          title="Severe Cases"
          value={statsData.scans?.severe_cases || 0}
          icon={ExclamationTriangleIcon}
          changeType="negative"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Charts */}
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Severity Distribution</h3>
          <div className="h-64 flex items-center justify-center">
            <Doughnut data={severityChartData} options={{ maintainAspectRatio: false }} />
          </div>
        </Card>

        <Card className="lg:col-span-2">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Scan Trend (14 Days)</h3>
          <div className="h-64">
            <Line data={trendChartData} options={{ maintainAspectRatio: false, scales: { y: { beginAtZero: true } } }} />
          </div>
        </Card>
      </div>

      {/* Role-specific content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Critical Cases / Unacknowledged Reports */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              {isDoctor ? 'Unacknowledged Reports' : 'Critical Cases'}
            </h3>
            <Link to={isDoctor ? '/reports' : '/scans'} className="text-sm text-primary-600 hover:text-primary-500">
              View all →
            </Link>
          </div>
          <div className="space-y-3">
            {isDoctor ? (
              dashboardData.unacknowledged_reports?.length > 0 ? (
                dashboardData.unacknowledged_reports.slice(0, 5).map((report) => (
                  <Link
                    key={report.id}
                    to={`/reports/${report.id}`}
                    className="block p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-900">{report.title}</span>
                      {report.is_critical && <SeverityBadge level="severe" />}
                    </div>
                    <p className="text-sm text-gray-500 mt-1">{report.report_id}</p>
                  </Link>
                ))
              ) : (
                <p className="text-gray-500 text-center py-4">No unacknowledged reports</p>
              )
            ) : (
              dashboardData.critical_cases?.length > 0 ? (
                dashboardData.critical_cases.slice(0, 5).map((scan) => (
                  <Link
                    key={scan.id}
                    to={`/scans/${scan.id}`}
                    className="block p-3 rounded-lg border border-red-200 bg-red-50 hover:bg-red-100 transition-colors critical-pulse"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-red-900">{scan.patient_name}</span>
                      <SeverityBadge level="severe" />
                    </div>
                    <p className="text-sm text-red-700 mt-1">
                      Spread: {scan.spread_ratio?.toFixed(1)}%
                    </p>
                  </Link>
                ))
              ) : (
                <p className="text-gray-500 text-center py-4">No critical cases</p>
              )
            )}
          </div>
        </Card>

        {/* Recent Activity */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              {isDoctor ? 'Recent Reports' : 'Pending Reviews'}
            </h3>
          </div>
          <div className="space-y-3">
            {isDoctor ? (
              dashboardData.recent_reports?.length > 0 ? (
                dashboardData.recent_reports.slice(0, 5).map((report) => (
                  <Link
                    key={report.id}
                    to={`/reports/${report.id}`}
                    className="block p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-900">{report.title}</span>
                      <StatusBadge status={report.status} />
                    </div>
                    <p className="text-sm text-gray-500 mt-1">{report.report_id}</p>
                  </Link>
                ))
              ) : (
                <p className="text-gray-500 text-center py-4">No recent reports</p>
              )
            ) : (
              dashboardData.pending_reports?.length > 0 ? (
                dashboardData.pending_reports.slice(0, 5).map((report) => (
                  <Link
                    key={report.id}
                    to={`/reports/${report.id}`}
                    className="block p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-900">{report.title}</span>
                      {report.is_critical && <SeverityBadge level="severe" />}
                    </div>
                    <p className="text-sm text-gray-500 mt-1">{report.report_id}</p>
                  </Link>
                ))
              ) : (
                <p className="text-gray-500 text-center py-4">No pending reviews</p>
              )
            )}
          </div>
        </Card>
      </div>

      {/* Quick Stats */}
      {isRadiologist && dashboardData.weekly_stats && (
        <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Card className="bg-gradient-to-br from-primary-500 to-primary-600 text-white">
            <div className="flex items-center gap-4">
              <ArrowTrendingUpIcon className="h-10 w-10 opacity-80" />
              <div>
                <p className="text-primary-100">This Week</p>
                <p className="text-2xl font-bold">{dashboardData.weekly_stats.scans_uploaded} Scans</p>
              </div>
            </div>
          </Card>
          <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
            <div className="flex items-center gap-4">
              <DocumentTextIcon className="h-10 w-10 opacity-80" />
              <div>
                <p className="text-green-100">This Week</p>
                <p className="text-2xl font-bold">{dashboardData.weekly_stats.reports_created} Reports</p>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
