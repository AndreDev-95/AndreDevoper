import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import axios from 'axios';
import { ArrowLeft, Mail, CheckCircle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [resetToken, setResetToken] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!email.trim()) {
      toast.error('Por favor, insira o seu email');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${BACKEND_URL}/api/auth/forgot-password`, {
        email: email.trim()
      });
      
      setSubmitted(true);
      
      if (response.data.reset_token) {
        setResetToken(response.data.reset_token);
      }
      
      toast.success('Instruções enviadas!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao processar pedido');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-muted flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="bg-white border border-border p-8 rounded-2xl text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <h1 className="text-2xl font-bold text-foreground mb-2">Email Enviado!</h1>
            <p className="text-muted-foreground mb-6">
              Se o email existir na nossa base de dados, receberá instruções para recuperar a sua password.
            </p>
            
            {resetToken && (
              <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-left">
                <p className="text-sm text-yellow-800 font-medium mb-2">
                  Modo de Desenvolvimento:
                </p>
                <p className="text-xs text-yellow-700 mb-2">
                  Em produção, este link seria enviado por email.
                </p>
                <Link 
                  to={`/reset-password?token=${resetToken}`}
                  className="text-sm text-secondary hover:underline break-all"
                >
                  Clique aqui para redefinir a password
                </Link>
              </div>
            )}
            
            <Link to="/login">
              <Button variant="outline" className="w-full">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Voltar ao Login
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-muted flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white border border-border p-8 rounded-2xl">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-secondary/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <Mail className="w-8 h-8 text-secondary" />
            </div>
            <h1 className="text-2xl font-bold text-foreground mb-2">Recuperar Password</h1>
            <p className="text-muted-foreground">
              Insira o seu email e enviaremos instruções para recuperar a sua password.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Email
              </label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="seu@email.com"
                required
                data-testid="forgot-password-email"
              />
            </div>

            <Button 
              type="submit" 
              className="w-full bg-secondary hover:bg-secondary/90"
              disabled={loading}
              data-testid="forgot-password-submit"
            >
              {loading ? 'A enviar...' : 'Enviar Instruções'}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <Link 
              to="/login" 
              className="text-sm text-secondary hover:underline flex items-center justify-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Voltar ao Login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
