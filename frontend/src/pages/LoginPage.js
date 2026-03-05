import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import { useAuth } from '@/context/AuthContext';
import usePageTitle from '@/hooks/usePageTitle';
import { Code2, ArrowLeft, Mail, Lock } from 'lucide-react';

export default function LoginPage() {
  usePageTitle('Entrar');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await login(email, password);
      toast.success('Login efetuado com sucesso!');
      navigate('/dashboard');
    } catch (error) {
      const message = error.response?.data?.detail || 'Erro ao efetuar login';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex" data-testid="login-page">
      {/* Left Panel - Form */}
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
            <h1 className="text-3xl font-bold text-foreground mb-2">Bem-vindo de volta</h1>
            <p className="text-muted-foreground">Entre na sua conta para aceder à área de cliente</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input 
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="email@exemplo.com"
                  className="pl-10"
                  required
                  data-testid="login-email-input"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-foreground">Password</label>
                <Link 
                  to="/forgot-password" 
                  className="text-sm text-secondary hover:underline"
                  data-testid="forgot-password-link"
                >
                  Esqueceu a password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <Input 
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="pl-10"
                  required
                  data-testid="login-password-input"
                />
              </div>
            </div>

            <Button 
              type="submit" 
              disabled={loading}
              className="w-full bg-primary text-white hover:bg-primary/90 rounded-none py-6 font-semibold"
              data-testid="login-submit-btn"
            >
              {loading ? 'A entrar...' : 'Entrar'}
            </Button>
          </form>

          <p className="text-center mt-6 text-muted-foreground">
            Não tem conta?{' '}
            <Link to="/register" className="text-secondary hover:underline font-medium" data-testid="register-link">
              Criar conta
            </Link>
          </p>
        </div>
      </div>

      {/* Right Panel - Image */}
      <div className="hidden lg:block lg:w-1/2 bg-primary relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary to-slate-900"></div>
        <div className="absolute inset-0 flex items-center justify-center p-12">
          <div className="text-center">
            <h2 className="text-4xl font-bold text-white mb-4">Área de Cliente</h2>
            <p className="text-white/70 text-lg max-w-md">
              Acompanhe os seus projetos, comunique connosco e gerencie a sua conta num só lugar.
            </p>
          </div>
        </div>
        <img 
          src="https://images.unsplash.com/photo-1759661881353-5b9cc55e1cf4?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njd8MHwxfHNlYXJjaHwxfHxjb2RpbmclMjBzZXR1cCUyMG1vbml0b3IlMjBjb2RlJTIwc2NyZWVufGVufDB8fHx8MTc3MTUxNzQwM3ww&ixlib=rb-4.1.0&q=85"
          alt="Code"
          className="absolute inset-0 w-full h-full object-cover opacity-20"
        />
      </div>
    </div>
  );
}
