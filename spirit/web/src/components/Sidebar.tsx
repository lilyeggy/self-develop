import { NavLink, useNavigate } from 'react-router-dom'
import { FiHome, FiEdit3, FiBarChart2, FiSettings, FiLogOut, FiZap } from 'react-icons/fi'

interface SidebarProps {
  onLogout: () => void
}

function Sidebar({ onLogout }: SidebarProps) {
  const navigate = useNavigate()

  const handleLogout = () => {
    onLogout()
    navigate('/login')
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <FiZap size={28} />
        <h1>Spirit</h1>
      </div>

      <nav>
        <NavLink
          to="/dashboard"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <FiHome />
          <span>仪表盘</span>
        </NavLink>

        <NavLink
          to="/thoughts"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <FiEdit3 />
          <span>思考记录</span>
        </NavLink>

        <NavLink
          to="/analytics"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <FiBarChart2 />
          <span>数据分析</span>
        </NavLink>

        <NavLink
          to="/settings"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <FiSettings />
          <span>设置</span>
        </NavLink>
      </nav>

      <div style={{ marginTop: 'auto', paddingTop: '20px' }}>
        <button onClick={handleLogout} className="nav-item" style={{ width: '100%', border: 'none', background: 'none', cursor: 'pointer' }}>
          <FiLogOut />
          <span>退出登录</span>
        </button>
      </div>
    </aside>
  )
}

export default Sidebar
