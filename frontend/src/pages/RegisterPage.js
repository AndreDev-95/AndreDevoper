import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import { useAuth } from '@/context/AuthContext';
import usePageTitle from '@/hooks/usePageTitle';
import { Code2, ArrowLeft, Mail, Lock, User, Building } from 'lucide-react';

export default function RegisterPage() {
  usePageTitle('Criar Conta');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    company: ''
  });
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

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
      await register(formData.name, formData.email, formData.password, formData.company || null);
      toast.success('Conta criada com sucesso!');
      navigate('/dashboard');
    } catch (error) {
      const message = error.response?.data?.detail || 'Erro ao criar conta';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex" data-testid="register-page">
      {/* Left Panel - Image */}
      <div className="hidden lg:block lg:w-1/2 bg-primary relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary to-slate-900"></div>
        <div className="absolute inset-0 flex items-center justify-center p-12">
          <div className="text-center">
            <h2 className="text-4xl font-bold text-white mb-4">Junte-se a nós</h2>
            <p className="text-white/70 text-lg max-w-md">
              Crie a sua conta e comece a acompanhar os seus projetos de desenvolvimento.
            </p>
          </div>
        </div>
        <img 
          src="https://images.unsplash.com/photo-1755372740351-8d7d0fcd582c?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1NTZ8MHwxfHNlYXJjaHwzfHxoYW5kJTIwaG9sZGluZyUyMHNtYXJ0cGhvbmUlMjBtb2Rlcm4lMjBhcHAlMjBpbnRlcmZhY2V8ZW58MHx8fHwxNzcxNTE3NDA0fDA&ixlib=rb-4.1.0&q=85"
          alt="Mobile app"
          className="absolute inset-0 w-full h-full object-cover opacity-20"
        />
      </div>

      {/* Right Panel - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 lg:p-12">
        <div className="w-full max-w-md">
          <Link 
            to="/" 
            className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors mb-8"
            data-testid="back-to-home"
          >
            <ArrowLeft className="w-4 h-4" />
            Voltar
          </Link>

          <div className="mb-8">
            <div className="flex items-center gap-2 mb-6">
              <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                <Code2 className="w-6 h-6 text-white" />
              </div>
              <span className="font-sans font-bold text-xl text-foreground">Andre Dev</span>
            </div>
            <h1 className="text-3xl font-bold text-foreground mb-2">Criar conta</h1>
            <p className="text-muted-foreground">Registe-se para aceder à área de cliente</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Nome</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input 
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="O seu nome"
                  className="pl-10"
                  required
                  data-testid="register-name-input"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input 
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  placeholder="email@exemplo.com"
                  className="pl-10"
                  required
                  data-testid="register-email-input"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Empresa (opcional)</label>
              <div className="relative">
                <Building className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input 
                  value={formData.company}
                  onChange={(e) => setFormData({...formData, company: e.target.value})}
                  placeholder="Nome da empresa"
                  className="pl-10"
                  data-testid="register-company-input"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input 
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  placeholder="••••••••"
                  className="pl-10"
                  required
                  data-testid="register-password-input"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Confirmar Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input 
                  type="password"
                  value={formData.confirmPassword}
                  onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
                  placeholder="••••••••"
                  className="pl-10"
                  required
                  data-testid="register-confirm-password-input"
                />
              </div>
            </div>

            <Button 
              type="submit" 
              disabled={loading}
              className="w-full bg-primary text-white hover:bg-primary/90 rounded-none py-6 font-semibold"
              data-testid="register-submit-btn"
            >
              {loading ? 'A criar conta...' : 'Criar conta'}
            </Button>
          </form>

          <p className="text-center mt-6 text-muted-foreground">
            Já tem conta?{' '}
            <Link to="/login" className="text-secondary hover:underline font-medium" data-testid="login-link">
              Entrar
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
