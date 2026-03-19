import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  BedDouble, LayoutDashboard, Calendar, UserCheck, 
  LogOut, CreditCard, FileText, Users, BarChart3,
  ClipboardCheck, Menu, X
} from 'lucide-react';
import { Button } from '../components/ui/button';

const Sidebar = ({ isOpen, setIsOpen }) => {
  const { user, logout, hasRole } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { 
      to: '/dashboard', 
      icon: LayoutDashboard, 
      label: 'Dashboard',
      roles: ['administrador', 'recepcionista', 'huesped']
    },
    { 
      to: '/habitaciones', 
      icon: BedDouble, 
      label: 'Habitaciones',
      roles: ['administrador', 'recepcionista', 'huesped']
    },
    { 
      to: '/reservas', 
      icon: Calendar, 
      label: 'Reservas',
      roles: ['administrador', 'recepcionista', 'huesped']
    },
    { 
      to: '/checkin', 
      icon: UserCheck, 
      label: 'Check-in',
      roles: ['administrador', 'recepcionista']
    },
    { 
      to: '/checkout', 
      icon: ClipboardCheck, 
      label: 'Check-out',
      roles: ['administrador', 'recepcionista']
    },
    { 
      to: '/pagos', 
      icon: CreditCard, 
      label: 'Pagos',
      roles: ['administrador', 'recepcionista']
    },
    { 
      to: '/facturas', 
      icon: FileText, 
      label: 'Facturas',
      roles: ['administrador', 'recepcionista', 'huesped']
    },
    { 
      to: '/reportes', 
      icon: BarChart3, 
      label: 'Reportes',
      roles: ['administrador']
    },
    { 
      to: '/usuarios', 
      icon: Users, 
      label: 'Usuarios',
      roles: ['administrador']
    },
  ];

  const filteredNavItems = navItems.filter(item => 
    item.roles.some(role => hasRole(role))
  );

  const getRoleBadge = (rol) => {
    const badges = {
      administrador: 'bg-amber-100 text-amber-800',
      recepcionista: 'bg-blue-100 text-blue-800',
      huesped: 'bg-emerald-100 text-emerald-800'
    };
    const labels = {
      administrador: 'Admin',
      recepcionista: 'Recepción',
      huesped: 'Huésped'
    };
    return (
      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${badges[rol]}`}>
        {labels[rol]}
      </span>
    );
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside 
        className={`fixed top-0 left-0 z-50 h-full w-64 bg-white border-r border-stone-100 transform transition-transform duration-300 ease-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        data-testid="sidebar"
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-6 border-b border-stone-100">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-primary rounded-sm flex items-center justify-center">
                  <BedDouble className="w-5 h-5 text-primary-foreground" />
                </div>
                <div>
                  <h1 className="text-lg font-semibold" style={{ fontFamily: 'Playfair Display, serif' }}>
                    Imperium
                  </h1>
                  <p className="text-xs text-muted-foreground">Boutique Hotel</p>
                </div>
              </div>
              <button 
                className="lg:hidden p-2 hover:bg-stone-100 rounded-sm"
                onClick={() => setIsOpen(false)}
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 overflow-y-auto">
            <ul className="space-y-1">
              {filteredNavItems.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    onClick={() => setIsOpen(false)}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-4 py-3 rounded-sm text-sm font-medium transition-all duration-200 ${
                        isActive
                          ? 'bg-primary/5 text-primary border-l-2 border-primary -ml-[2px]'
                          : 'text-muted-foreground hover:bg-stone-50 hover:text-foreground'
                      }`
                    }
                    data-testid={`nav-${item.label.toLowerCase()}`}
                  >
                    <item.icon className="w-5 h-5" strokeWidth={1.5} />
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>

          {/* User info */}
          <div className="p-4 border-t border-stone-100">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-stone-100 rounded-full flex items-center justify-center">
                <span className="text-sm font-semibold text-stone-600">
                  {user?.nombre_completo?.charAt(0)?.toUpperCase()}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{user?.nombre_completo}</p>
                <div className="mt-1">{getRoleBadge(user?.rol)}</div>
              </div>
            </div>
            <Button
              variant="outline"
              className="w-full justify-start gap-2 h-10"
              onClick={handleLogout}
              data-testid="logout-btn"
            >
              <LogOut className="w-4 h-4" />
              Cerrar sesión
            </Button>
          </div>
        </div>
      </aside>
    </>
  );
};

const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  return (
    <div className="min-h-screen bg-[#fcfaf8]">
      <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />
      
      {/* Main content */}
      <div className="lg:ml-64">
        {/* Mobile header */}
        <header className="lg:hidden sticky top-0 z-30 bg-white border-b border-stone-100 px-4 py-3">
          <div className="flex items-center justify-between">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 hover:bg-stone-100 rounded-sm"
              data-testid="mobile-menu-btn"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2">
              <BedDouble className="w-5 h-5 text-primary" />
              <span className="font-semibold" style={{ fontFamily: 'Playfair Display, serif' }}>
                Imperium
              </span>
            </div>
            <div className="w-9" /> {/* Spacer */}
          </div>
        </header>

        {/* Page content */}
        <main className="p-6 md:p-8 lg:p-10">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;
