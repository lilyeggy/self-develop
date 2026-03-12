import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { reviewAPI, authAPI, exportAPI } from '../api'
import { FiBell, FiUser, FiDownload, FiPlus, FiTrash2 } from 'react-icons/fi'

function Settings() {
  const queryClient = useQueryClient()
  const [showAddConfig, setShowAddConfig] = useState(false)
  const [newConfig, setNewConfig] = useState({
    period: 'weekly',
    hour: 20,
    minute: 0,
    day_of_week: 1
  })

  const { data: configs } = useQuery({
    queryKey: ['reviewConfigs'],
    queryFn: async () => {
      const response = await reviewAPI.getConfigs()
      return response.data
    }
  })

  const { data: user } = useQuery({
    queryKey: ['user'],
    queryFn: async () => {
      const response = await authAPI.getMe()
      return response.data
    }
  })

  const createConfigMutation = useMutation({
    mutationFn: (data: typeof newConfig) => reviewAPI.createConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reviewConfigs'] })
      setShowAddConfig(false)
    }
  })

  const deleteConfigMutation = useMutation({
    mutationFn: (id: number) => reviewAPI.deleteConfig(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reviewConfigs'] })
    }
  })

  const handleExport = async (format: 'markdown' | 'json' | 'pdf') => {
    try {
      const response = await exportAPI.thoughts({ format })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `thoughts_${new Date().toISOString().split('T')[0]}.${format}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h2>设置</h2>
        <p>管理你的账户和系统配置</p>
      </div>

      <div className="analytics-chart" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
          <FiUser />
          <h3>账户信息</h3>
        </div>
        {user && (
          <div>
            <p><strong>用户名：</strong>{user.username}</p>
            <p><strong>邮箱：</strong>{user.email}</p>
            <p><strong>注册时间：</strong>{new Date(user.created_at).toLocaleDateString('zh-CN')}</p>
          </div>
        )}
      </div>

      <div className="analytics-chart" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
          <FiBell />
          <h3>回顾提醒</h3>
        </div>

        {configs && configs.length > 0 ? (
          <div>
            {configs.map((config: any) => (
              <div key={config.id} style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                padding: '15px',
                background: 'var(--background)',
                borderRadius: '10px',
                marginBottom: '10px'
              }}>
                <div>
                  <p><strong>{config.period === 'daily' ? '每日' : config.period === 'weekly' ? '每周' : '每月'}回顾</strong></p>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                    {config.hour}:{config.minute.toString().padStart(2, '0')}
                  </p>
                </div>
                <button
                  className="btn-icon"
                  onClick={() => deleteConfigMutation.mutate(config.id)}
                >
                  <FiTrash2 />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: 'var(--text-secondary)' }}>暂无提醒设置</p>
        )}

        {showAddConfig ? (
          <div style={{ marginTop: '20px', padding: '20px', background: 'var(--background)', borderRadius: '10px' }}>
            <select
              value={newConfig.period}
              onChange={(e) => setNewConfig({ ...newConfig, period: e.target.value })}
              style={{ width: '100%', padding: '10px', marginBottom: '10px', borderRadius: '5px' }}
            >
              <option value="daily">每日</option>
              <option value="weekly">每周</option>
              <option value="monthly">每月</option>
            </select>
            
            <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
              <input
                type="number"
                placeholder="小时"
                value={newConfig.hour}
                onChange={(e) => setNewConfig({ ...newConfig, hour: parseInt(e.target.value) })}
                style={{ width: '80px', padding: '8px', borderRadius: '5px' }}
              />
              <input
                type="number"
                placeholder="分钟"
                value={newConfig.minute}
                onChange={(e) => setNewConfig({ ...newConfig, minute: parseInt(e.target.value) })}
                style={{ width: '80px', padding: '8px', borderRadius: '5px' }}
              />
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                className="btn btn-primary"
                onClick={() => createConfigMutation.mutate(newConfig)}
                disabled={createConfigMutation.isPending}
              >
                保存
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => setShowAddConfig(false)}
              >
                取消
              </button>
            </div>
          </div>
        ) : (
          <button
            className="btn btn-secondary"
            onClick={() => setShowAddConfig(true)}
            style={{ marginTop: '15px' }}
          >
            <FiPlus /> 添加提醒
          </button>
        )}
      </div>

      <div className="analytics-chart">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
          <FiDownload />
          <h3>数据导出</h3>
        </div>
        
        <p style={{ marginBottom: '15px', color: 'var(--text-secondary)' }}>
          将你的思考记录导出为不同格式
        </p>
        
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button className="btn btn-secondary" onClick={() => handleExport('markdown')}>
            Markdown
          </button>
          <button className="btn btn-secondary" onClick={() => handleExport('json')}>
            JSON
          </button>
          <button className="btn btn-secondary" onClick={() => handleExport('pdf')}>
            PDF
          </button>
        </div>
      </div>
    </div>
  )
}

export default Settings
