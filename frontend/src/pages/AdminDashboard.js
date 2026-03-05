import { useState, useEffect } from 'react';
import { Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import usePageTitle from '@/hooks/usePageTitle';
import { SettingsBar } from '@/components/SettingsBar';
import AnalyticsDashboard from '@/components/AnalyticsDashboard';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import { useAuth } from '@/context/AuthContext';
import axios from 'axios';
import { 
  Code2, 
  LayoutDashboard, 
  FolderKanban, 
  MessageSquare, 
  Users,
  Mail,
  LogOut,
  Menu,
  X,
  Shield,
  Clock,
  CheckCircle2,
  AlertCircle,
  Trash2,
  Send,
  FileEdit,
  Euro,
  Check,
  Reply,
  ChevronDown,
  User,
  Plus,
  BarChart3
} from 'lucide-react';
import ContentEditor from './ContentEditor';
import ProjectDetailsEnhanced from './ProjectDetailsEnhanced';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Admin Navbar Component
const AdminNavbar = () => {
  const location = useLocation();
  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
    toast.success('Sessão terminada');
  };

  const navItems = [
    { path: '/admin', icon: LayoutDashboard, label: 'Dashboard', exact: true },
    { path: '/admin/contacts', icon: Mail, label: 'Contactos' },
    { path: '/admin/users', icon: Users, label: 'Utilizadores' },
    { path: '/admin/projects', icon: FolderKanban, label: 'Projetos' },
    { path: '/admin/messages', icon: MessageSquare, label: 'Mensagens' },
    { path: '/admin/content', icon: FileEdit, label: 'Editar Site' },
    { path: '/admin/analytics', icon: BarChart3, label: 'Analytics' },
  ];

  return (
    <nav className="bg-gradient-to-r from-secondary to-primary border-b border-white/10 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
              <Code2 className="w-5 h-5 text-secondary" />
            </div>
            <span className="font-sans font-bold text-lg text-white">Andre Dev</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = item.exact 
                ? location.pathname === item.path
                : location.pathname.startsWith(item.path);
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`
                    flex items-center gap-2 px-3 py-2 rounded-lg transition-colors
                    ${isActive 
                      ? 'bg-white/20 text-white' 
                      : 'text-white/70 hover:bg-white/10 hover:text-white'
                    }
                  `}
                >
                  <item.icon className="w-4 h-4" />
                  <span className="font-medium text-sm">{item.label}</span>
                </Link>
              );
            })}
          </div>

          {/* User Menu - Desktop */}
          <div className="hidden md:block relative">
            <button
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/10 transition-colors text-white"
            >
              <Shield className="w-4 h-4" />
              <div className="text-left">
                <p className="text-xs text-white/60">Admin</p>
                <p className="text-sm font-medium">{user?.name}</p>
              </div>
              <ChevronDown className="w-4 h-4" />
            </button>

            {userMenuOpen && (
              <>
                <div 
                  className="fixed inset-0 z-10" 
                  onClick={() => setUserMenuOpen(false)}
                />
                <div className="absolute right-0 mt-2 w-56 bg-white border border-border rounded-lg shadow-lg py-2 z-20">
                  <div className="px-4 py-2 border-b border-border">
                    <p className="text-sm font-medium text-primary">{user?.name}</p>
                    <p className="text-xs text-muted-foreground">{user?.email}</p>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-muted-foreground hover:bg-muted transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    Terminar sessão
                  </button>
                </div>
              </>
            )}
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-white/10 text-white"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-white/10 py-2">
            <div className="space-y-1">
              {navItems.map((item) => {
                const isActive = item.exact 
                  ? location.pathname === item.path
                  : location.pathname.startsWith(item.path);
                
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`
                      flex items-center gap-2 px-4 py-3 rounded-lg transition-colors
                      ${isActive 
                        ? 'bg-white/20 text-white' 
                        : 'text-white/70 hover:bg-white/10 hover:text-white'
                      }
                    `}
                  >
                    <item.icon className="w-5 h-5" />
                    <span className="font-medium">{item.label}</span>
                  </Link>
                );
              })}
              <div className="border-t border-white/10 mt-2 pt-2">
                <div className="px-4 py-2">
                  <p className="text-sm font-medium text-white">{user?.name}</p>
                  <p className="text-xs text-white/60">{user?.email}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-4 py-3 text-white/70 hover:bg-white/10 rounded-lg transition-colors"
                >
                  <LogOut className="w-5 h-5" />
                  Terminar sessão
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

// Admin Sidebar Component (DEPRECATED - keeping for compatibility)
const AdminSidebar = ({ open, setOpen }) => {
  const location = useLocation();
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
    toast.success('Sessão terminada');
  };

  const navItems = [
    { path: '/admin', icon: LayoutDashboard, label: 'Dashboard', exact: true },
    { path: '/admin/content', icon: FileEdit, label: 'Editar Site' },
    { path: '/admin/contacts', icon: Mail, label: 'Contactos' },
    { path: '/admin/users', icon: Users, label: 'Utilizadores' },
    { path: '/admin/projects', icon: FolderKanban, label: 'Projetos' },
    { path: '/admin/messages', icon: MessageSquare, label: 'Mensagens' },
    { path: '/admin/analytics', icon: BarChart3, label: 'Analytics' },
  ];

  return (
    <>
      {open && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      <aside className={`
        fixed top-0 left-0 h-screen w-64 bg-gradient-to-b from-secondary to-primary z-50
        transform transition-transform duration-200 ease-in-out
        ${open ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0 lg:static
      `}>
        <div className="flex flex-col h-full">
          <div className="p-6 flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
                <Code2 className="w-6 h-6 text-secondary" />
              </div>
              <span className="font-sans font-bold text-xl text-white">Andre Dev</span>
            </Link>
            <button 
              className="lg:hidden text-white"
              onClick={() => setOpen(false)}
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          <div className="px-6 py-4 border-t border-white/10">
            <div className="flex items-center gap-2 mb-1">
              <Shield className="w-4 h-4 text-white/80" />
              <span className="text-white/80 text-sm font-medium">Administrador</span>
            </div>
            <p className="text-white font-medium truncate">{user?.name}</p>
            <p className="text-white/60 text-sm truncate">{user?.email}</p>
          </div>

          <nav className="flex-1 px-4 py-6">
            <div className="space-y-1">
              {navItems.map((item) => {
                const isActive = item.exact 
                  ? location.pathname === item.path
                  : location.pathname.startsWith(item.path);
                
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`
                      flex items-center gap-3 px-4 py-3 rounded-lg transition-colors
                      ${isActive 
                        ? 'bg-white/20 text-white' 
                        : 'text-white/70 hover:bg-white/10 hover:text-white'
                      }
                    `}
                    data-testid={`admin-nav-${item.label.toLowerCase()}`}
                    onClick={() => setOpen(false)}
                  >
                    <item.icon className="w-5 h-5 flex-shrink-0" />
                    <span className="font-medium">{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </nav>

          <div className="p-4 border-t border-white/10">
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 px-4 py-3 rounded-lg w-full text-white/70 hover:bg-white/10 hover:text-white transition-colors"
              data-testid="admin-logout-btn"
            >
              <LogOut className="w-5 h-5" />
              <span className="font-medium">Terminar sessão</span>
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};

// Admin Dashboard Overview
const AdminOverview = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const { getAuthHeaders } = useAuth();

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await axios.get(`${API}/admin/stats`, {
          headers: getAuthHeaders()
        });
        setStats(response.data);
      } catch (error) {
        console.error('Error fetching stats:', error);
        toast.error('Erro ao carregar estatísticas');
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, [getAuthHeaders]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-secondary"></div>
      </div>
    );
  }

  const statCards = [
    { label: 'Utilizadores', value: stats?.total_users || 0, icon: Users, color: 'bg-blue-500' },
    { label: 'Contactos', value: stats?.total_contacts || 0, icon: Mail, color: 'bg-green-500' },
    { label: 'Projetos', value: stats?.total_projects || 0, icon: FolderKanban, color: 'bg-purple-500' },
    { label: 'Mensagens', value: stats?.total_messages || 0, icon: MessageSquare, color: 'bg-orange-500' },
  ];

  const projectStats = [
    { label: 'Pendentes', value: stats?.pending_projects || 0, icon: Clock, color: 'text-yellow-600' },
    { label: 'Em Progresso', value: stats?.in_progress_projects || 0, icon: AlertCircle, color: 'text-blue-600' },
    { label: 'Concluídos', value: stats?.completed_projects || 0, icon: CheckCircle2, color: 'text-green-600' },
  ];

  return (
    <div data-testid="admin-dashboard">
      <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-primary mb-4 sm:mb-6 md:mb-8">Painel de Administração</h1>
      
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 md:gap-6 mb-4 sm:mb-6 md:mb-8">
        {statCards.map((stat, index) => (
          <div 
            key={index}
            className="bg-white border border-border p-3 sm:p-4 md:p-6 rounded-xl shadow-sm"
            data-testid={`admin-stat-${index}`}
          >
            <div className={`w-8 h-8 sm:w-10 sm:h-10 md:w-12 md:h-12 ${stat.color} rounded-lg flex items-center justify-center mb-2 sm:mb-4`}>
              <stat.icon className="w-4 h-4 sm:w-5 sm:h-5 md:w-6 md:h-6 text-white" />
            </div>
            <p className="text-xl sm:text-2xl md:text-3xl font-bold text-primary">{stat.value}</p>
            <p className="text-muted-foreground text-xs sm:text-sm truncate">{stat.label}</p>
          </div>
        ))}
      </div>

      <div className="bg-white border border-border p-4 sm:p-6 rounded-xl shadow-sm">
        <h2 className="text-base sm:text-lg font-semibold text-primary mb-3 sm:mb-4">Estado dos Projetos</h2>
        <div className="grid grid-cols-3 gap-2 sm:gap-4">
          {projectStats.map((stat, index) => (
            <div key={index} className="text-center p-2 sm:p-4 bg-muted rounded-lg">
              <stat.icon className={`w-5 h-5 sm:w-6 sm:h-6 md:w-8 md:h-8 mx-auto mb-1 sm:mb-2 ${stat.color}`} />
              <p className="text-lg sm:text-xl md:text-2xl font-bold text-primary">{stat.value}</p>
              <p className="text-xs sm:text-sm text-muted-foreground">{stat.label}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Contacts Management
const AdminContacts = () => {
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const { getAuthHeaders } = useAuth();

  const fetchContacts = async () => {
    try {
      const response = await axios.get(`${API}/admin/contacts`, {
        headers: getAuthHeaders()
      });
      setContacts(response.data);
    } catch (error) {
      console.error('Error fetching contacts:', error);
      toast.error('Erro ao carregar contactos');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContacts();
  }, []);

  const handleDelete = async (contactId) => {
    if (!window.confirm('Tem certeza que deseja eliminar este contacto?')) return;
    
    try {
      await axios.delete(`${API}/admin/contacts/${contactId}`, {
        headers: getAuthHeaders()
      });
      toast.success('Contacto eliminado');
      fetchContacts();
    } catch (error) {
      toast.error('Erro ao eliminar contacto');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-secondary"></div>
      </div>
    );
  }

  return (
    <div data-testid="admin-contacts-page">
      <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-primary mb-4 sm:mb-6 md:mb-8">Contactos</h1>
      
      {contacts.length === 0 ? (
        <div className="bg-white border border-border rounded-xl p-6 sm:p-8 md:p-12 text-center">
          <Mail className="w-10 h-10 sm:w-12 sm:h-12 text-muted-foreground mx-auto mb-3 sm:mb-4" />
          <h3 className="text-base sm:text-lg font-semibold text-primary mb-2">Sem contactos</h3>
          <p className="text-sm sm:text-base text-muted-foreground">Os contactos do formulário aparecerão aqui.</p>
        </div>
      ) : (
        <div className="space-y-3 sm:space-y-4">
          {contacts.map((contact) => (
            <div 
              key={contact.id}
              className="bg-white border border-border p-4 sm:p-6 rounded-xl shadow-sm"
              data-testid={`contact-${contact.id}`}
            >
              <div className="flex justify-between items-start gap-2 sm:gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 sm:gap-3 mb-1 sm:mb-2">
                    <h3 className="text-base sm:text-lg font-semibold text-primary truncate">{contact.name}</h3>
                    <span className="text-xs text-muted-foreground">
                      {new Date(contact.created_at).toLocaleDateString('pt-PT')}
                    </span>
                  </div>
                  <p className="text-xs sm:text-sm text-secondary mb-1 truncate">{contact.email}</p>
                  {contact.phone && (
                    <p className="text-xs sm:text-sm text-muted-foreground mb-2">{contact.phone}</p>
                  )}
                  <p className="text-sm sm:text-base text-foreground mt-2 sm:mt-3">{contact.message}</p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDelete(contact.id)}
                  className="text-destructive hover:text-destructive hover:bg-destructive/10 flex-shrink-0"
                  data-testid={`delete-contact-${contact.id}`}
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Users Management
const AdminUsers = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newUser, setNewUser] = useState({ name: '', email: '', password: '', company: '' });
  const { getAuthHeaders } = useAuth();

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/users`, {
        headers: getAuthHeaders()
      });
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('Erro ao carregar utilizadores');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleDelete = async (userId) => {
    if (!window.confirm('Tem certeza que deseja eliminar este utilizador? Todos os projetos e mensagens serão eliminados.')) return;
    
    try {
      await axios.delete(`${API}/admin/users/${userId}`, {
        headers: getAuthHeaders()
      });
      toast.success('Utilizador eliminado');
      fetchUsers();
    } catch (error) {
      toast.error('Erro ao eliminar utilizador');
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    if (!newUser.name || !newUser.email || !newUser.password) {
      toast.error('Preencha todos os campos obrigatórios');
      return;
    }
    if (newUser.password.length < 6) {
      toast.error('A password deve ter pelo menos 6 caracteres');
      return;
    }
    
    setCreating(true);
    try {
      await axios.post(`${API}/admin/users`, newUser, {
        headers: getAuthHeaders()
      });
      toast.success('Cliente criado com sucesso! Email de boas-vindas enviado.');
      setShowCreateModal(false);
      setNewUser({ name: '', email: '', password: '', company: '' });
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao criar cliente');
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-secondary"></div>
      </div>
    );
  }

  return (
    <div data-testid="admin-users-page">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4 sm:mb-6 md:mb-8">
        <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-primary">Utilizadores</h1>
        <Button 
          onClick={() => setShowCreateModal(true)}
          className="bg-secondary hover:bg-secondary/90"
          data-testid="create-user-btn"
        >
          <User className="w-4 h-4 mr-2" />
          Criar Cliente
        </Button>
      </div>

      {/* Create User Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Criar Nova Conta de Cliente</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateUser} className="space-y-4 mt-4">
            <div>
              <label className="block text-sm font-medium mb-2">Nome *</label>
              <Input
                value={newUser.name}
                onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
                placeholder="Nome do cliente"
                required
                data-testid="new-user-name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Email *</label>
              <Input
                type="email"
                value={newUser.email}
                onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                placeholder="email@exemplo.com"
                required
                data-testid="new-user-email"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Password *</label>
              <Input
                type="text"
                value={newUser.password}
                onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                placeholder="Mínimo 6 caracteres"
                required
                data-testid="new-user-password"
              />
              <p className="text-xs text-muted-foreground mt-1">A password será enviada por email ao cliente</p>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Empresa (opcional)</label>
              <Input
                value={newUser.company}
                onChange={(e) => setNewUser({ ...newUser, company: e.target.value })}
                placeholder="Nome da empresa"
                data-testid="new-user-company"
              />
            </div>
            <div className="flex gap-3 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowCreateModal(false)}
                className="flex-1"
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={creating}
                className="flex-1 bg-secondary hover:bg-secondary/90"
                data-testid="submit-create-user"
              >
                {creating ? 'A criar...' : 'Criar Cliente'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
      
      {users.length === 0 ? (
        <div className="bg-white border border-border rounded-xl p-6 sm:p-8 md:p-12 text-center">
          <Users className="w-10 h-10 sm:w-12 sm:h-12 text-muted-foreground mx-auto mb-3 sm:mb-4" />
          <h3 className="text-base sm:text-lg font-semibold text-primary mb-2">Sem utilizadores</h3>
          <p className="text-sm sm:text-base text-muted-foreground mb-4">Os utilizadores registados aparecerão aqui.</p>
          <Button onClick={() => setShowCreateModal(true)} className="bg-secondary hover:bg-secondary/90">
            <User className="w-4 h-4 mr-2" />
            Criar Primeiro Cliente
          </Button>
        </div>
      ) : (
        <>
          {/* Mobile Cards */}
          <div className="lg:hidden space-y-3">
            {users.map((user) => (
              <div key={user.id} className="bg-white border border-border p-4 rounded-xl" data-testid={`user-card-${user.id}`}>
                <div className="flex justify-between items-start mb-2">
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-primary truncate">{user.name}</p>
                    <p className="text-sm text-muted-foreground truncate">{user.email}</p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(user.id)}
                    className="text-destructive hover:text-destructive hover:bg-destructive/10 flex-shrink-0"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>{user.company || 'Sem empresa'}</span>
                  <span>{new Date(user.created_at).toLocaleDateString('pt-PT')}</span>
                </div>
              </div>
            ))}
          </div>
          
          {/* Desktop Table */}
          <div className="hidden lg:block bg-white border border-border rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-muted">
                  <tr>
                    <th className="text-left p-4 font-medium text-primary">Nome</th>
                    <th className="text-left p-4 font-medium text-primary">Email</th>
                    <th className="text-left p-4 font-medium text-primary">Empresa</th>
                    <th className="text-left p-4 font-medium text-primary">Data</th>
                    <th className="text-right p-4 font-medium text-primary">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.id} className="border-t border-border" data-testid={`user-row-${user.id}`}>
                      <td className="p-4">{user.name}</td>
                      <td className="p-4 text-muted-foreground">{user.email}</td>
                      <td className="p-4 text-muted-foreground">{user.company || '-'}</td>
                      <td className="p-4 text-muted-foreground text-sm">
                        {new Date(user.created_at).toLocaleDateString('pt-PT')}
                      </td>
                      <td className="p-4 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(user.id)}
                          className="text-destructive hover:text-destructive hover:bg-destructive/10"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

// Projects Management
const AdminProjects = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const { getAuthHeaders } = useAuth();

  const fetchProjects = async () => {
    try {
      const response = await axios.get(`${API}/admin/projects`, {
        headers: getAuthHeaders()
      });
      setProjects(response.data);
    } catch (error) {
      console.error('Error fetching projects:', error);
      toast.error('Erro ao carregar projetos');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const getStatusBadge = (status) => {
    const badges = {
      pending: { label: 'Pendente', class: 'bg-yellow-100 text-yellow-700' },
      in_progress: { label: 'Em Progresso', class: 'bg-blue-100 text-blue-700' },
      completed: { label: 'Concluído', class: 'bg-green-100 text-green-700' }
    };
    return badges[status] || badges.pending;
  };

  const getBudgetStatusBadge = (budgetStatus) => {
    const badges = {
      pending: { label: 'Orçamento Pendente', class: 'bg-orange-100 text-orange-700', icon: Clock },
      accepted: { label: 'Orçamento Aceite', class: 'bg-green-100 text-green-700', icon: CheckCircle2 },
      counter_proposal: { label: 'Contraproposta', class: 'bg-purple-100 text-purple-700', icon: Reply }
    };
    return badges[budgetStatus] || badges.pending;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-secondary"></div>
      </div>
    );
  }

  return (
    <div data-testid="admin-projects-page">
      <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-primary mb-4 sm:mb-6 md:mb-8">Projetos</h1>
      
      {projects.length === 0 ? (
        <div className="bg-white border border-border rounded-xl p-6 sm:p-8 md:p-12 text-center">
          <FolderKanban className="w-10 h-10 sm:w-12 sm:h-12 text-muted-foreground mx-auto mb-3 sm:mb-4" />
          <h3 className="text-base sm:text-lg font-semibold text-primary mb-2">Sem projetos</h3>
          <p className="text-sm sm:text-base text-muted-foreground">Os projetos dos clientes aparecerão aqui.</p>
        </div>
      ) : (
        <div className="space-y-4 sm:space-y-6">
          {projects.map((project) => {
            const statusBadge = getStatusBadge(project.status);
            const budgetBadge = getBudgetStatusBadge(project.budget_status);
            const BudgetIcon = budgetBadge.icon;
            return (
              <Link
                key={project.id}
                to={`/admin/projects/${project.id}`}
                className="block bg-white border border-border p-4 sm:p-6 rounded-xl shadow-sm hover:border-secondary/50 hover:shadow-md transition-all cursor-pointer"
                data-testid={`admin-project-${project.id}`}
              >
                <div className="flex flex-col gap-3 sm:gap-4">
                  <div className="flex-1">
                    <div className="flex flex-wrap items-center gap-2 sm:gap-3 mb-1 sm:mb-2">
                      <h3 className="text-base sm:text-lg font-semibold text-primary">{project.name}</h3>
                      <span className={`text-xs px-2 py-0.5 sm:py-1 rounded-full ${statusBadge.class}`}>
                        {statusBadge.label}
                      </span>
                    </div>
                    <p className="text-muted-foreground text-xs sm:text-sm mb-2 sm:mb-3">{project.description}</p>
                    {project.user && (
                      <p className="text-xs sm:text-sm">
                        <span className="text-muted-foreground">Cliente: </span>
                        <span className="text-secondary">{project.user.name}</span>
                        <span className="text-muted-foreground hidden sm:inline"> ({project.user.email})</span>
                      </p>
                    )}
                  </div>

                  {/* Budget Section */}
                  <div className="bg-muted/50 rounded-lg p-3 sm:p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Euro className="w-4 h-4 text-secondary" />
                      <span className="text-sm font-medium text-primary">Orçamento</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full flex items-center gap-1 ml-auto ${budgetBadge.class}`}>
                        <BudgetIcon className="w-3 h-3" />
                        {budgetBadge.label}
                      </span>
                    </div>
                    <div className="space-y-1">
                      <p className="text-sm">
                        <span className="text-muted-foreground">Proposto pelo cliente: </span>
                        <span className="font-semibold text-primary">{project.budget}</span>
                      </p>
                      {project.budget_status === 'counter_proposal' && project.counter_proposal && (
                        <p className="text-sm">
                          <span className="text-muted-foreground">Sua contraproposta: </span>
                          <span className="font-semibold text-purple-700">{project.counter_proposal}</span>
                        </p>
                      )}
                      {project.admin_notes && (
                        <p className="text-xs text-muted-foreground mt-2 italic">
                          Nota: {project.admin_notes}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Ver Detalhes Indicator */}
                  <div className="flex items-center justify-between pt-3 border-t border-border">
                    <div className="text-xs sm:text-sm text-muted-foreground">
                      Criado em {new Date(project.created_at).toLocaleDateString('pt-PT')}
                    </div>
                    <span className="text-xs text-secondary font-medium flex items-center gap-1">
                      Ver Detalhes →
                    </span>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
};

// Messages Management
const AdminMessages = () => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMessage, setSelectedMessage] = useState(null);
  const [replyText, setReplyText] = useState('');
  const [replying, setReplying] = useState(false);
  const { getAuthHeaders } = useAuth();

  const fetchMessages = async () => {
    try {
      const response = await axios.get(`${API}/admin/messages`, {
        headers: getAuthHeaders()
      });
      setMessages(response.data);
    } catch (error) {
      console.error('Error fetching messages:', error);
      toast.error('Erro ao carregar mensagens');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMessages();
  }, []);

  const handleReply = async () => {
    if (!replyText.trim()) {
      toast.error('Escreva uma resposta');
      return;
    }

    setReplying(true);
    try {
      await axios.put(`${API}/admin/messages/${selectedMessage.id}/reply?reply=${encodeURIComponent(replyText)}`, {}, {
        headers: getAuthHeaders()
      });
      toast.success('Resposta enviada');
      setSelectedMessage(null);
      setReplyText('');
      fetchMessages();
    } catch (error) {
      toast.error('Erro ao enviar resposta');
    } finally {
      setReplying(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-secondary"></div>
      </div>
    );
  }

  return (
    <div data-testid="admin-messages-page">
      <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-primary mb-4 sm:mb-6 md:mb-8">Mensagens</h1>
      
      {messages.length === 0 ? (
        <div className="bg-white border border-border rounded-xl p-6 sm:p-8 md:p-12 text-center">
          <MessageSquare className="w-10 h-10 sm:w-12 sm:h-12 text-muted-foreground mx-auto mb-3 sm:mb-4" />
          <h3 className="text-base sm:text-lg font-semibold text-primary mb-2">Sem mensagens</h3>
          <p className="text-sm sm:text-base text-muted-foreground">As mensagens dos clientes aparecerão aqui.</p>
        </div>
      ) : (
        <div className="space-y-3 sm:space-y-4">
          {messages.map((message) => (
            <div 
              key={message.id}
              className={`bg-white border p-4 sm:p-6 rounded-xl shadow-sm ${!message.is_read ? 'border-secondary' : 'border-border'}`}
              data-testid={`admin-message-${message.id}`}
            >
              <div className="flex flex-col sm:flex-row justify-between items-start gap-2 sm:gap-4 mb-2 sm:mb-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2 sm:gap-3">
                    <h3 className="font-semibold text-primary text-sm sm:text-base">{message.subject}</h3>
                    {!message.is_read && (
                      <span className="text-xs bg-secondary text-white px-2 py-0.5 rounded-full">Novo</span>
                    )}
                  </div>
                  {message.user && (
                    <p className="text-xs sm:text-sm text-muted-foreground mt-1 truncate">
                      De: {message.user.name} <span className="hidden sm:inline">({message.user.email})</span>
                    </p>
                  )}
                </div>
                <span className="text-xs text-muted-foreground whitespace-nowrap">
                  {new Date(message.created_at).toLocaleDateString('pt-PT')}
                </span>
              </div>
              <p className="text-sm sm:text-base text-foreground mb-3 sm:mb-4">{message.content}</p>
              
              {message.admin_reply ? (
                <div className="bg-muted p-3 sm:p-4 rounded-lg">
                  <p className="text-xs text-secondary font-medium mb-1">Sua resposta:</p>
                  <p className="text-xs sm:text-sm text-foreground">{message.admin_reply}</p>
                </div>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedMessage(message)}
                  data-testid={`reply-btn-${message.id}`}
                  className="w-full sm:w-auto"
                >
                  <Send className="w-4 h-4 mr-2" />
                  Responder
                </Button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Reply Dialog */}
      <Dialog open={!!selectedMessage} onOpenChange={() => setSelectedMessage(null)}>
        <DialogContent aria-describedby="reply-description" className="max-w-[95vw] sm:max-w-lg mx-auto">
          <DialogHeader>
            <DialogTitle className="text-base sm:text-lg">Responder a: {selectedMessage?.subject}</DialogTitle>
            <p id="reply-description" className="text-xs sm:text-sm text-muted-foreground truncate">
              {selectedMessage?.user?.name} ({selectedMessage?.user?.email})
            </p>
          </DialogHeader>
          <div className="space-y-3 sm:space-y-4 mt-3 sm:mt-4">
            <div className="bg-muted p-3 rounded-lg text-xs sm:text-sm">
              <p className="text-muted-foreground mb-1">Mensagem original:</p>
              <p>{selectedMessage?.content}</p>
            </div>
            <Textarea
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              placeholder="Escreva a sua resposta..."
              rows={4}
              className="min-h-[100px]"
              data-testid="reply-textarea"
            />
            <Button 
              onClick={handleReply} 
              disabled={replying}
              className="w-full bg-secondary hover:bg-secondary/90"
              data-testid="send-reply-btn"
            >
              {replying ? 'A enviar...' : 'Enviar Resposta'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Main Admin Dashboard Layout
export default function AdminDashboard() {
  usePageTitle('Painel Admin');
  const { user, isAdmin } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user && !isAdmin()) {
      navigate('/dashboard');
    }
  }, [user, isAdmin, navigate]);

  return (
    <div className="min-h-screen bg-muted" data-testid="admin-panel">
      <AdminNavbar />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        <Routes>
          <Route index element={<AdminOverview />} />
          <Route path="content" element={<ContentEditor />} />
          <Route path="contacts" element={<AdminContacts />} />
          <Route path="users" element={<AdminUsers />} />
          <Route path="projects" element={<AdminProjects />} />
          <Route path="projects/:projectId" element={<ProjectDetailsEnhanced />} />
          <Route path="messages" element={<AdminMessages />} />
          <Route path="analytics" element={<AnalyticsDashboard />} />
        </Routes>
      </main>
    </div>
  );
}
