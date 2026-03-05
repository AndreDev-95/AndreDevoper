import { useState, useEffect } from 'react';
import { Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import ProjectDetailsEnhanced from '@/pages/ProjectDetailsEnhanced';
import usePageTitle from '@/hooks/usePageTitle';
import { ThemeToggle } from '@/components/SettingsBar';
import NotificationsDropdown from '@/components/NotificationsDropdown';
import ProjectChat from '@/components/ProjectChat';
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
  DialogTrigger,
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import { useAuth } from '@/context/AuthContext';
import axios from 'axios';
import { 
  Code2, 
  LayoutDashboard, 
  FolderKanban, 
  MessageSquare, 
  Settings, 
  LogOut,
  Plus,
  Clock,
  CheckCircle2,
  AlertCircle,
  Menu,
  X,
  Send,
  Euro,
  User,
  Download,
  CreditCard,
  FileText,
  ChevronDown
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Navbar Component
const Navbar = () => {
  const location = useLocation();
  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
    toast.success('Sessão terminada com sucesso!');
  };

  const navItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', exact: true },
    { path: '/dashboard/projects', icon: FolderKanban, label: 'Projetos' },
    { path: '/dashboard/messages', icon: MessageSquare, label: 'Mensagens' },
    { path: '/dashboard/settings', icon: Settings, label: 'Definições' },
  ];

  return (
    <nav className="bg-card border-b border-border sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <Code2 className="w-5 h-5 text-white" />
            </div>
            <span className="font-sans font-bold text-lg text-foreground">Andre Dev</span>
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
                    flex items-center gap-2 px-4 py-2 rounded-lg transition-colors
                    ${isActive 
                      ? 'bg-primary text-white' 
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                    }
                  `}
                >
                  <item.icon className="w-4 h-4" />
                  <span className="font-medium text-sm">{item.label}</span>
                </Link>
              );
            })}
          </div>

          {/* Right Side - Theme Toggle, Notifications & User Menu */}
          <div className="hidden md:flex items-center gap-2">
            <ThemeToggle />
            <NotificationsDropdown />
            
            {/* User Menu - Desktop */}
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-muted transition-colors"
              >
                <div className="w-8 h-8 bg-secondary rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-white" />
                </div>
                <div className="text-left">
                  <p className="text-sm font-medium text-foreground">{user?.name}</p>
                </div>
                <ChevronDown className="w-4 h-4 text-muted-foreground" />
              </button>

            {/* Dropdown */}
            {userMenuOpen && (
              <>
                <div 
                  className="fixed inset-0 z-10" 
                  onClick={() => setUserMenuOpen(false)}
                />
                <div className="absolute right-0 mt-2 w-56 bg-card border border-border rounded-lg shadow-lg py-2 z-20">
                  <div className="px-4 py-2 border-b border-border">
                    <p className="text-sm font-medium text-foreground">{user?.name}</p>
                    <p className="text-xs text-muted-foreground">{user?.email}</p>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-muted-foreground hover:bg-muted transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    Sair
                  </button>
                </div>
              </>
            )}
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center gap-2">
            <ThemeToggle />
            <NotificationsDropdown />
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg hover:bg-muted"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-border py-2">
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
                        ? 'bg-primary text-white' 
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                      }
                    `}
                  >
                    <item.icon className="w-5 h-5" />
                    <span className="font-medium">{item.label}</span>
                  </Link>
                );
              })}
              <div className="border-t border-border mt-2 pt-2">
                <div className="px-4 py-2">
                  <p className="text-sm font-medium text-foreground">{user?.name}</p>
                  <p className="text-xs text-muted-foreground">{user?.email}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-4 py-3 text-muted-foreground hover:bg-muted rounded-lg transition-colors"
                >
                  <LogOut className="w-5 h-5" />
                  Sair
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

// Dashboard Overview
const DashboardOverview = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const { getAuthHeaders } = useAuth();

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await axios.get(`${API}/stats`, {
          headers: getAuthHeaders()
        });
        setStats(response.data);
      } catch (error) {
        console.error('Error fetching stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [getAuthHeaders]);

  const statCards = [
    { label: 'Total de Projetos', value: stats?.total_projects || 0, icon: FolderKanban, color: 'bg-secondary' },
    { label: 'Pendentes', value: stats?.pending || 0, icon: Clock, color: 'bg-yellow-500' },
    { label: 'Em Progresso', value: stats?.in_progress || 0, icon: AlertCircle, color: 'bg-blue-500' },
    { label: 'Concluídos', value: stats?.completed || 0, icon: CheckCircle2, color: 'bg-green-500' },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-secondary"></div>
      </div>
    );
  }

  return (
    <div data-testid="dashboard-overview">
      <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-foreground mb-4 sm:mb-6 md:mb-8">Dashboard</h1>
      
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 md:gap-6 mb-4 sm:mb-6 md:mb-8">
        {statCards.map((stat, index) => (
          <div 
            key={index}
            className="bg-card border border-border p-3 sm:p-4 md:p-6 rounded-xl shadow-sm"
            data-testid={`stat-card-${index}`}
          >
            <div className="flex items-center justify-between mb-2 sm:mb-4">
              <div className={`w-8 h-8 sm:w-10 sm:h-10 md:w-12 md:h-12 ${stat.color} rounded-lg flex items-center justify-center`}>
                <stat.icon className="w-4 h-4 sm:w-5 sm:h-5 md:w-6 md:h-6 text-white" />
              </div>
            </div>
            <p className="text-xl sm:text-2xl md:text-3xl font-bold text-foreground">{stat.value}</p>
            <p className="text-muted-foreground text-xs sm:text-sm truncate">{stat.label}</p>
          </div>
        ))}
      </div>

      <div className="bg-card border border-border p-4 sm:p-6 rounded-xl shadow-sm">
        <h2 className="text-base sm:text-lg font-semibold text-foreground mb-3 sm:mb-4">Ações Rápidas</h2>
        <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
          <Link to="/dashboard/projects" className="w-full sm:w-auto">
            <Button className="bg-secondary hover:bg-secondary/90 w-full sm:w-auto">
              <Plus className="w-4 h-4 mr-2" />
              Novo Projeto
            </Button>
          </Link>
          <Link to="/dashboard/messages" className="w-full sm:w-auto">
            <Button variant="outline" className="w-full sm:w-auto">
              <MessageSquare className="w-4 h-4 mr-2" />
              Enviar Mensagem
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
};

// Projects Page
const ProjectsPage = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [newProject, setNewProject] = useState({
    name: '',
    description: '',
    project_type: 'web',
    budget: ''
  });
  const { getAuthHeaders } = useAuth();

  const fetchProjects = async () => {
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('search', searchQuery);
      if (statusFilter) params.append('status', statusFilter);
      if (typeFilter) params.append('project_type', typeFilter);
      
      const response = await axios.get(`${API}/projects?${params.toString()}`, {
        headers: getAuthHeaders()
      });
      setProjects(response.data);
    } catch (error) {
      console.error('Error fetching projects:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [searchQuery, statusFilter, typeFilter]);

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleCreateProject = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/projects`, newProject, {
        headers: getAuthHeaders()
      });
      toast.success('Projeto criado com sucesso!');
      setDialogOpen(false);
      setNewProject({ name: '', description: '', project_type: 'web', budget: '' });
      fetchProjects();
    } catch (error) {
      toast.error('Erro ao criar projeto');
    }
  };

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
      pending: { label: 'Orçamento Pendente', class: 'bg-orange-100 text-orange-700' },
      accepted: { label: 'Orçamento Aceite', class: 'bg-green-100 text-green-700' },
      counter_proposal: { label: 'Contraproposta', class: 'bg-purple-100 text-purple-700' }
    };
    return badges[budgetStatus] || badges.pending;
  };

  const getTypeBadge = (type) => {
    const types = {
      web: 'Website',
      android: 'Android',
      ios: 'iOS',
      hybrid: 'Híbrido'
    };
    return types[type] || type;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-secondary"></div>
      </div>
    );
  }

  return (
    <div data-testid="projects-page">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 sm:gap-4 mb-4 sm:mb-6 md:mb-8">
        <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-foreground">Projetos</h1>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-secondary hover:bg-secondary/90 w-full sm:w-auto" data-testid="new-project-btn">
              <Plus className="w-4 h-4 mr-2" />
              Novo Projeto
            </Button>
          </DialogTrigger>
          <DialogContent aria-describedby="new-project-description" className="max-w-[95vw] sm:max-w-lg mx-auto">
            <DialogHeader>
              <DialogTitle>Criar Novo Projeto</DialogTitle>
              <p id="new-project-description" className="text-sm text-muted-foreground">
                Preencha os dados do seu novo projeto
              </p>
            </DialogHeader>
            <form onSubmit={handleCreateProject} className="space-y-4 mt-4">
              <div>
                <label className="block text-sm font-medium mb-2">Nome do Projeto</label>
                <Input 
                  value={newProject.name}
                  onChange={(e) => setNewProject({...newProject, name: e.target.value})}
                  placeholder="Ex: Website E-commerce"
                  required
                  data-testid="project-name-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Tipo</label>
                <Select 
                  value={newProject.project_type}
                  onValueChange={(value) => setNewProject({...newProject, project_type: value})}
                >
                  <SelectTrigger data-testid="project-type-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="web">Website</SelectItem>
                    <SelectItem value="android">Aplicação Android</SelectItem>
                    <SelectItem value="ios">Aplicação iOS</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Descrição</label>
                <Textarea 
                  value={newProject.description}
                  onChange={(e) => setNewProject({...newProject, description: e.target.value})}
                  placeholder="Descreva o seu projeto..."
                  rows={3}
                  required
                  data-testid="project-description-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Orçamento Proposto *</label>
                <Input 
                  value={newProject.budget}
                  onChange={(e) => setNewProject({...newProject, budget: e.target.value})}
                  placeholder="Ex: 5000€"
                  required
                  data-testid="project-budget-input"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  O orçamento será analisado pelo administrador
                </p>
              </div>
              <Button type="submit" className="w-full bg-primary" data-testid="create-project-btn">
                Criar Projeto
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Search and Filters */}
      <div className="bg-card border border-border rounded-xl p-4 mb-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-1">
            <Input
              placeholder="Pesquisar projetos..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full"
            />
          </div>
          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full p-2 border border-border rounded-md"
            >
              <option value="">Todos os status</option>
              <option value="pending">Pendente</option>
              <option value="in_progress">Em Progresso</option>
              <option value="completed">Concluído</option>
            </select>
          </div>
          <div>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="w-full p-2 border border-border rounded-md"
            >
              <option value="">Todos os tipos</option>
              <option value="web">Website</option>
              <option value="android">Android</option>
              <option value="ios">iOS</option>
            </select>
          </div>
        </div>
        {(searchQuery || statusFilter || typeFilter) && (
          <div className="mt-3 flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Filtros ativos:</span>
            {searchQuery && (
              <span className="text-xs bg-secondary/10 text-secondary px-2 py-1 rounded">
                "{searchQuery}"
              </span>
            )}
            {statusFilter && (
              <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                {statusFilter === 'pending' ? 'Pendente' : statusFilter === 'in_progress' ? 'Em Progresso' : 'Concluído'}
              </span>
            )}
            {typeFilter && (
              <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
                {typeFilter === 'web' ? 'Website' : typeFilter === 'android' ? 'Android' : 'iOS'}
              </span>
            )}
            <button
              onClick={() => {
                setSearchQuery('');
                setStatusFilter('');
                setTypeFilter('');
              }}
              className="text-xs text-muted-foreground hover:text-foreground underline ml-auto"
            >
              Limpar filtros
            </button>
          </div>
        )}
      </div>


      {projects.length === 0 ? (
        <div className="bg-card border border-border rounded-xl p-6 sm:p-8 md:p-12 text-center">
          <FolderKanban className="w-10 h-10 sm:w-12 sm:h-12 text-muted-foreground mx-auto mb-3 sm:mb-4" />
          <h3 className="text-base sm:text-lg font-semibold text-foreground mb-2">Sem projetos</h3>
          <p className="text-sm sm:text-base text-muted-foreground mb-4">Crie o seu primeiro projeto para começar.</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:gap-6">
          {projects.map((project) => {
            const statusBadge = getStatusBadge(project.status);
            const budgetBadge = getBudgetStatusBadge(project.budget_status);
            return (
              <Link
                key={project.id}
                to={`/dashboard/projects/${project.id}`}
                className="bg-card border border-border p-4 sm:p-6 rounded-xl shadow-sm hover:border-secondary/50 hover:shadow-md transition-all cursor-pointer"
                data-testid={`project-card-${project.id}`}
              >
                <div className="flex flex-col gap-3 sm:gap-4">
                  <div>
                    <div className="flex flex-wrap items-center gap-2 sm:gap-3 mb-2">
                      <h3 className="text-base sm:text-lg font-semibold text-foreground">{project.name}</h3>
                      <span className={`text-xs px-2 py-0.5 sm:py-1 rounded-full ${statusBadge.class}`}>
                        {statusBadge.label}
                      </span>
                    </div>
                    <p className="text-muted-foreground text-xs sm:text-sm mb-2 sm:mb-3">{project.description}</p>
                    <div className="flex flex-wrap gap-1.5 sm:gap-2 mb-3">
                      <span className="text-xs bg-muted px-2 py-1 rounded text-muted-foreground">
                        {getTypeBadge(project.project_type)}
                      </span>
                    </div>
                    
                    {/* Budget Section */}
                    <div className="bg-muted/50 rounded-lg p-3 sm:p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Euro className="w-4 h-4 text-secondary" />
                        <span className="text-sm font-medium text-foreground">Orçamento</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full ml-auto ${budgetBadge.class}`}>
                          {budgetBadge.label}
                        </span>
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm">
                          <span className="text-muted-foreground">Proposto: </span>
                          <span className="font-medium text-foreground">{project.budget}</span>
                        </p>
                        {project.budget_status === 'counter_proposal' && project.counter_proposal && (
                          <p className="text-sm">
                            <span className="text-muted-foreground">Contraproposta: </span>
                            <span className="font-medium text-purple-700">{project.counter_proposal}</span>
                          </p>
                        )}
                        {project.admin_notes && (
                          <p className="text-xs text-muted-foreground mt-2 italic">
                            Nota: {project.admin_notes}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
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

// Messages Page
const MessagesPage = () => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newMessage, setNewMessage] = useState({ subject: '', content: '' });
  const [sending, setSending] = useState(false);
  const { getAuthHeaders } = useAuth();

  const fetchMessages = async () => {
    try {
      const response = await axios.get(`${API}/messages`, {
        headers: getAuthHeaders()
      });
      setMessages(response.data);
    } catch (error) {
      console.error('Error fetching messages:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMessages();
  }, []);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    setSending(true);
    try {
      await axios.post(`${API}/messages`, newMessage, {
        headers: getAuthHeaders()
      });
      toast.success('Mensagem enviada com sucesso!');
      setNewMessage({ subject: '', content: '' });
      fetchMessages();
    } catch (error) {
      toast.error('Erro ao enviar mensagem');
    } finally {
      setSending(false);
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
    <div data-testid="messages-page">
      <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-foreground mb-4 sm:mb-6 md:mb-8">Mensagens</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 md:gap-8">
        {/* New Message Form */}
        <div className="bg-card border border-border p-4 sm:p-6 rounded-xl shadow-sm">
          <h2 className="text-base sm:text-lg font-semibold text-foreground mb-3 sm:mb-4">Nova Mensagem</h2>
          <form onSubmit={handleSendMessage} className="space-y-3 sm:space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Assunto</label>
              <Input 
                value={newMessage.subject}
                onChange={(e) => setNewMessage({...newMessage, subject: e.target.value})}
                placeholder="Assunto da mensagem"
                required
                data-testid="message-subject-input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Mensagem</label>
              <Textarea 
                value={newMessage.content}
                onChange={(e) => setNewMessage({...newMessage, content: e.target.value})}
                placeholder="Escreva a sua mensagem..."
                rows={4}
                required
                className="min-h-[100px] sm:min-h-[120px]"
                data-testid="message-content-input"
              />
            </div>
            <Button 
              type="submit" 
              disabled={sending}
              className="w-full bg-secondary hover:bg-secondary/90"
              data-testid="send-message-btn"
            >
              <Send className="w-4 h-4 mr-2" />
              {sending ? 'A enviar...' : 'Enviar Mensagem'}
            </Button>
          </form>
        </div>

        {/* Messages List */}
        <div className="space-y-3 sm:space-y-4">
          <h2 className="text-base sm:text-lg font-semibold text-foreground">Histórico</h2>
          {messages.length === 0 ? (
            <div className="bg-card border border-border rounded-xl p-6 sm:p-8 text-center">
              <MessageSquare className="w-8 h-8 sm:w-10 sm:h-10 text-muted-foreground mx-auto mb-2 sm:mb-3" />
              <p className="text-sm sm:text-base text-muted-foreground">Sem mensagens</p>
            </div>
          ) : (
            messages.map((message) => (
              <div 
                key={message.id}
                className="bg-card border border-border p-3 sm:p-4 rounded-xl shadow-sm"
                data-testid={`message-${message.id}`}
              >
                <div className="flex items-start justify-between gap-2 sm:gap-4 mb-2">
                  <h3 className="font-medium text-foreground text-sm sm:text-base">{message.subject}</h3>
                  <span className="text-xs text-muted-foreground whitespace-nowrap">
                    {new Date(message.created_at).toLocaleDateString('pt-PT')}
                  </span>
                </div>
                <p className="text-xs sm:text-sm text-muted-foreground">{message.content}</p>
                {message.admin_reply && (
                  <div className="mt-2 sm:mt-3 pt-2 sm:pt-3 border-t border-border">
                    <p className="text-xs text-secondary font-medium mb-1">Resposta:</p>
                    <p className="text-xs sm:text-sm text-foreground">{message.admin_reply}</p>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

// Settings Page
const SettingsPage = () => {
  const { user } = useAuth();
  const TwoFactorSettings = require('@/components/TwoFactorSettings').default;

  return (
    <div data-testid="settings-page">
      <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-foreground mb-4 sm:mb-6 md:mb-8">Definições</h1>

      <div className="grid gap-6 max-w-2xl">
        {/* Account Info */}
        <div className="bg-card border border-border p-4 sm:p-6 rounded-xl shadow-sm">
          <h2 className="text-base sm:text-lg font-semibold text-foreground mb-4 sm:mb-6">Informações da Conta</h2>
          
          <div className="space-y-3 sm:space-y-4">
            <div>
              <label className="block text-xs sm:text-sm font-medium text-muted-foreground mb-1">Nome</label>
              <p className="text-sm sm:text-base text-foreground">{user?.name}</p>
            </div>
            <div>
              <label className="block text-xs sm:text-sm font-medium text-muted-foreground mb-1">Email</label>
              <p className="text-sm sm:text-base text-foreground break-all">{user?.email}</p>
            </div>
            {user?.company && (
              <div>
                <label className="block text-xs sm:text-sm font-medium text-muted-foreground mb-1">Empresa</label>
                <p className="text-sm sm:text-base text-foreground">{user?.company}</p>
              </div>
            )}
            <div>
              <label className="block text-xs sm:text-sm font-medium text-muted-foreground mb-1">Membro desde</label>
              <p className="text-sm sm:text-base text-foreground">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString('pt-PT') : '-'}
              </p>
            </div>
          </div>
        </div>

        {/* 2FA Settings */}
        <TwoFactorSettings />
      </div>
    </div>
  );
};

// Main Dashboard Layout
export default function Dashboard() {
  usePageTitle('Dashboard');
  return (
    <div className="min-h-screen bg-muted" data-testid="dashboard">
      <Navbar />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        <Routes>
          <Route index element={<DashboardOverview />} />
          <Route path="projects" element={<ProjectsPage />} />
          <Route path="projects/:projectId" element={<ProjectDetailsEnhanced />} />
          <Route path="messages" element={<MessagesPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}
