import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { thoughtsAPI, analyticsAPI } from '../api'
import { FiSend, FiZap } from 'react-icons/fi'

function Dashboard() {
  const queryClient = useQueryClient()
  const [content, setContent] = useState('')

  const { data: analytics } = useQuery({
    queryKey: ['analytics'],
    queryFn: async () => {
      const response = await analyticsAPI.get()
      return response.data
    }
  })

  const { data: thoughts, isLoading } = useQuery({
    queryKey: ['thoughts', { limit: 5 }],
    queryFn: async () => {
      const response = await thoughtsAPI.list({ limit: 5 })
      return response.data
    }
  })

  const createMutation = useMutation({
    mutationFn: (data: { content: string }) => thoughtsAPI.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['thoughts'] })
      queryClient.invalidateQueries({ queryKey: ['analytics'] })
      setContent('')
    }
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!content.trim()) return
    createMutation.mutate({ content: content.trim() })
  }

  const categoryLabels: Record<string, string> = {
    idea: '💡 想法',
    question: '❓ 问题',
    insight: '✨ 感悟',
    plan: '📋 计划',
    reflection: '🔄 反思',
    note: '📝 笔记',
    diary: '📅 日记'
  }

  return (
    <div>
      <div className="page-header">
        <h2>仪表盘</h2>
        <p>欢迎回来，开始记录你的思考吧</p>
      </div>

      <div className="quick-input">
        <form onSubmit={handleSubmit}>
          <textarea
            placeholder="记录你的想法、问题、感悟..."
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />
          <div className="quick-input-actions">
            <div></div>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!content.trim() || createMutation.isPending}
            >
              <FiSend />
              记录
            </button>
          </div>
        </form>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>总思考数</h3>
          <div className="value">{analytics?.total_thoughts || 0}</div>
        </div>
        <div className="stat-card">
          <h3>本月新增</h3>
          <div className="value">{analytics?.thoughts_by_category ? Object.values(analytics.thoughts_by_category).reduce((a: any, b: any) => a + b, 0) : 0}</div>
        </div>
        <div className="stat-card">
          <h3>今日记录</h3>
          <div className="value">{analytics?.daily_thoughts_count?.slice(-1)[0]?.count || 0}</div>
        </div>
        <div className="stat-card">
          <h3>认知模式</h3>
          <div className="value">{analytics?.cognitive_patterns?.length || 0}</div>
        </div>
      </div>

      <h3 style={{ marginBottom: '20px' }}>最近的思考</h3>
      
      {isLoading ? (
        <div className="loading"><div className="spinner"></div></div>
      ) : thoughts && thoughts.length > 0 ? (
        <div className="thoughts-grid">
          {thoughts.map((thought: any) => (
            <div key={thought.id} className="thought-card">
              <div className="thought-card-header">
                <span className={`thought-category category-${thought.category}`}>
                  {categoryLabels[thought.category] || thought.category}
                </span>
                <span className="thought-time">
                  {new Date(thought.created_at).toLocaleDateString('zh-CN')}
                </span>
              </div>
              <div className="thought-content">
                {thought.content.length > 150
                  ? thought.content.substring(0, 150) + '...'
                  : thought.content}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <FiZap />
          <h3>还没有记录</h3>
          <p>在上方输入框中记录你的第一个想法</p>
        </div>
      )}
    </div>
  )
}

export default Dashboard
