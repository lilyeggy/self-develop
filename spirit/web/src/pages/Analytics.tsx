import { useQuery } from '@tanstack/react-query'
import { analyticsAPI, reviewAPI } from '../api'
import { FiTrendingUp, FiClock, FiAward } from 'react-icons/fi'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts'

function Analytics() {
  const { data: analytics, isLoading } = useQuery({
    queryKey: ['analytics'],
    queryFn: async () => {
      const response = await analyticsAPI.get()
      return response.data
    }
  })

  const { data: summaries } = useQuery({
    queryKey: ['summaries'],
    queryFn: async () => {
      const response = await reviewAPI.getSummaries('weekly', 5)
      return response.data
    }
  })

  const COLORS = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe']

  const categoryLabels: Record<string, string> = {
    idea: '想法',
    question: '问题',
    insight: '感悟',
    plan: '计划',
    reflection: '反思',
    note: '笔记',
    diary: '日记'
  }

  if (isLoading) {
    return <div className="loading"><div className="spinner"></div></div>
  }

  const categoryData = analytics?.thoughts_by_category
    ? Object.entries(analytics.thoughts_by_category).map(([key, value]) => ({
        name: categoryLabels[key] || key,
        value
      }))
    : []

  return (
    <div>
      <div className="page-header">
        <h2>数据分析</h2>
        <p>了解你的思考模式和成长趋势</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>总思考数</h3>
          <div className="value">{analytics?.total_thoughts || 0}</div>
        </div>
        <div className="stat-card">
          <h3>认知模式</h3>
          <div className="value">{analytics?.cognitive_patterns?.length || 0}</div>
        </div>
        <div className="stat-card">
          <h3>高频标签</h3>
          <div className="value">{analytics?.top_tags?.slice(0, 3).map((t: any) => `#${t.tag}`).join(' ') || '-'}</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '30px' }}>
        <div className="analytics-chart">
          <h3>思考分类分布</h3>
          {categoryData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p style={{ textAlign: 'center', color: '#999', padding: '40px' }}>暂无数据</p>
          )}
        </div>

        <div className="analytics-chart">
          <h3>每日思考趋势</h3>
          {analytics?.daily_thoughts_count?.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={analytics.daily_thoughts_count}>
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#667eea" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p style={{ textAlign: 'center', color: '#999', padding: '40px' }}>暂无数据</p>
          )}
        </div>
      </div>

      <div className="analytics-chart">
        <h3>认知模式分析</h3>
        {analytics?.cognitive_patterns?.length > 0 ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '15px' }}>
            {analytics.cognitive_patterns.map((pattern: any, index: number) => (
              <div key={index} style={{ padding: '20px', background: 'var(--background)', borderRadius: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                  <FiAward color="#667eea" />
                  <h4>{pattern.title}</h4>
                </div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{pattern.description}</p>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ textAlign: 'center', color: '#999', padding: '40px' }}>记录更多思考来发现你的认知模式</p>
        )}
      </div>

      <div className="analytics-chart" style={{ marginTop: '30px' }}>
        <h3>回顾总结</h3>
        {summaries && summaries.length > 0 ? (
          <div>
            {summaries.map((summary: any) => (
              <div key={summary.id} style={{ padding: '20px', borderBottom: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <h4>{summary.period.toUpperCase()} - {new Date(summary.period_end).toLocaleDateString('zh-CN')}</h4>
                </div>
                <p>{summary.summary}</p>
                {summary.suggestions && summary.suggestions.length > 0 && (
                  <div style={{ marginTop: '10px' }}>
                    <strong>建议：</strong>
                    <ul style={{ marginTop: '5px' }}>
                      {summary.suggestions.map((s: string, i: number) => (
                        <li key={i} style={{ color: 'var(--text-secondary)' }}>{s}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p style={{ textAlign: 'center', color: '#999', padding: '40px' }}>暂无回顾总结</p>
        )}
      </div>
    </div>
  )
}

export default Analytics
