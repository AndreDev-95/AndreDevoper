import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import { useAuth } from '@/context/AuthContext';
import usePageTitle from '@/hooks/usePageTitle';
import axios from 'axios';
import { Code2, ArrowLeft, Mail, Lock, User, Shield } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminSetupPage() {
  usePageTitle('Configurar Admin');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(true);
  const [adminExists, setAdminExists] = useState(false);
  const { setupAdmin, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const checkAdmin = async () => {
      try {
        const response = await axios.get(`${API}/admin/check`);
        setAdminExists(response.data.admin_exists);
      } catch (error) {
        console.error('Error checking admin:', error);
      } finally {
        setChecking(false);
      }
    };
    checkAdmin();
  }, []);

  useEffect(() => {
    if (user?.role === 'admin') {
      navigate('/dashboard');
    }
  }, [user, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.password !== formData.confirmPassword) {
      toast.error('As passwords não coincidem');
      return;
    }

    if (formData.password.length < 6) {
      toast.error('A password deve ter pelo menos 6 caracteres');
      return;
    }

    setLoading(true);

    try {
      await setupAdmin(formData.name, formData.email, formData.password);
      toast.success('Conta de administrador criada com sucesso!');
      navigate('/dashboard');
    } catch (error) {
      const message = error.response?.data?.detail || 'Erro ao criar conta de administrador';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-secondary"></div>
      </div>
    );
  }

  if (adminExists) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-secondary/10 rounded-full flex items-center justify-center mx-auto mb-6">
            <Shield className="w-8 h-8 text-secondary" />
          </div>
          <h1 className="text-2xl font-bold text-primary mb-4">Administrador já existe</h1>
          <p className="text-muted-foreground mb-6">
            Já existe uma conta de administrador configurada. Por favor, faça login para aceder.
          </p>
          <Link to="/login">
            <Button className="bg-secondary hover:bg-secondary/90">
              Ir para Login
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex" data-testid="admin-setup-page">
      {/* Left Panel - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 lg:p-12">
        <div className="w-full max-w-md">
          <Link 
            to="/" 
            className="inline-flex items-center gap-2 text-muted-foreground hover:text-primary transition-colors mb-8"
            data-testid="back-to-home"
          >
            <ArrowLeft className="w-4 h-4" />
            Voltar ao início
          </Link>

          <div className="mb-8">
            <div className="flex items-center gap-2 mb-6">
              <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                <Code2 className="w-6 h-6 text-white" />
              </div>
              <span className="font-sans font-bold text-xl text-primary">Andre Dev</span>
            </div>
            <div className="flex items-center gap-2 mb-4">
              <Shield className="w-6 h-6 text-secondary" />
              <h1 className="text-3xl font-bold text-primary">Configurar Admin</h1>
            </div>
            <p className="text-muted-foreground">
              Crie a conta de administrador para gerir a plataforma
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-primary mb-2">Nome</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input 
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="Nome do administrador"
                  className="pl-10"
                  required
                  data-testid="admin-name-input"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-primary mb-2">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input 
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  placeholder="admin@andredev.pt"
                  className="pl-10"
                  required
                  data-testid="admin-email-input"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-primary mb-2">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input 
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  placeholder="••••••••"
                  className="pl-10"
                  required
                  data-testid="admin-password-input"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-primary mb-2">Confirmar Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input 
                  type="password"
                  value={formData.confirmPassword}
                  onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
                  placeholder="••••••••"
                  className="pl-10"
                  required
                  data-testid="admin-confirm-password-input"
                />
              </div>
            </div>

            <Button 
              type="submit" 
              disabled={loading}
              className="w-full bg-secondary hover:bg-secondary/90 text-white rounded-none py-6 font-semibold"
              data-testid="admin-setup-submit-btn"
            >
              {loading ? 'A criar conta...' : 'Criar Conta de Admin'}
            </Button>
          </form>

          <p className="text-center mt-6 text-muted-foreground text-sm">
            Já tem conta?{' '}
            <Link to="/login" className="text-secondary hover:underline font-medium">
              Entrar
            </Link>
          </p>
        </div>
      </div>

      {/* Right Panel */}
      <div className="hidden lg:block lg:w-1/2 bg-gradient-to-br from-secondary to-primary relative overflow-hidden">
        <div className="absolute inset-0 flex items-center justify-center p-12">
          <div className="text-center">
            <Shield className="w-20 h-20 text-white/80 mx-auto mb-6" />
            <h2 className="text-4xl font-bold text-white mb-4">Painel de Administração</h2>
            <p className="text-white/70 text-lg max-w-md">
              Gerencie clientes, projetos, mensagens e contactos num único lugar.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
