import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { thoughtsAPI } from '../api'
import { FiSearch, FiFilter, FiStar, FiArchive, FiTrash2, FiZap, FiMessageSquare } from 'react-icons/fi'

function Thoughts() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [expandedId, setExpandedId] = useState<number | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['thoughts', { search, category }],
    queryFn: async () => {
      const response = await thoughtsAPI.list({ search: search || undefined, category: category || undefined })
      return response.data
    }
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => thoughtsAPI.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['thoughts'] })
    }
  })

  const favoriteMutation = useMutation({
    mutationFn: (id: number) => thoughtsAPI.toggleFavorite(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['thoughts'] })
    }
  })

  const expandMutation = useMutation({
    mutationFn: ({ id, types }: { id: number; types: string[] }) => thoughtsAPI.expand(id, types),
  })

  const handleExpand = async (id: number) => {
    if (expandedId === id) {
      setExpandedId(null)
    } else {
      setExpandedId(id)
      expandMutation.mutate({ id, types: ['question_extension', 'related_idea'] })
    }
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
        <h2>思考记录</h2>
        <p>管理你的所有思考记录</p>
      </div>

      <div style={{ display: 'flex', gap: '15px', marginBottom: '25px' }}>
        <div style={{ flex: 1, position: 'relative' }}>
          <FiSearch style={{ position: 'absolute', left: '15px', top: '50%', transform: 'translateY(-50%)', color: '#999' }} />
          <input
            type="text"
            placeholder="搜索思考内容..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: '100%',
              padding: '12px 15px 12px 45px',
              border: '2px solid var(--border)',
              borderRadius: '10px',
              fontSize: '1rem'
            }}
          />
        </div>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          style={{
            padding: '12px 15px',
            border: '2px solid var(--border)',
            borderRadius: '10px',
            fontSize: '1rem',
            background: 'white'
          }}
        >
          <option value="">全部分类</option>
          <option value="idea">💡 想法</option>
          <option value="question">❓ 问题</option>
          <option value="insight">✨ 感悟</option>
          <option value="plan">📋 计划</option>
          <option value="reflection">🔄 反思</option>
          <option value="note">📝 笔记</option>
          <option value="diary">📅 日记</option>
        </select>
      </div>

      {isLoading ? (
        <div className="loading"><div className="spinner"></div></div>
      ) : data && data.length > 0 ? (
        <div className="thoughts-grid">
          {data.map((thought: any) => (
            <div key={thought.id} className="thought-card">
              <div className="thought-card-header">
                <span className={`thought-category category-${thought.category}`}>
                  {categoryLabels[thought.category] || thought.category}
                </span>
                <span className="thought-time">
                  {new Date(thought.created_at).toLocaleString('zh-CN')}
                </span>
              </div>
              
              <div className="thought-content">{thought.content}</div>
              
              {thought.tags && thought.tags.length > 0 && (
                <div className="thought-tags">
                  {thought.tags.map((tag: string) => (
                    <span key={tag} className="thought-tag">#{tag}</span>
                  ))}
                </div>
              )}

              {expandedId === thought.id && expandMutation.data && (
                <div className="expansion-list">
                  <FiMessageSquare style={{ marginBottom: '10px' }} />
                  {expandMutation.data.data.expansions.map((exp: any) => (
                    <div key={exp.id} className="expansion-item">
                      <div className="expansion-type">{exp.expansion_type}</div>
                      <div>{exp.content}</div>
                    </div>
                  ))}
                </div>
              )}
              
              <div className="thought-actions">
                <button
                  className="btn-icon"
                  onClick={() => favoriteMutation.mutate(thought.id)}
                  title="收藏"
                >
                  <FiStar color={thought.is_favorite ? '#f59e0b' : undefined} />
                </button>
                <button
                  className="btn-icon"
                  onClick={() => handleExpand(thought.id)}
                  title="展开思考"
                >
                  <FiZap />
                </button>
                <button
                  className="btn-icon"
                  onClick={() => deleteMutation.mutate(thought.id)}
                  title="删除"
                >
                  <FiTrash2 />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <FiZap />
          <h3>没有找到记录</h3>
          <p>尝试调整搜索条件或创建新的思考</p>
        </div>
      )}
    </div>
  )
}

export default Thoughts
