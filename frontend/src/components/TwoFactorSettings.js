import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAuth } from '@/context/AuthContext';
import { toast } from 'sonner';
import axios from 'axios';
import { 
  Shield, 
  ShieldCheck, 
  ShieldOff, 
  Smartphone, 
  Key,
  Loader2,
  Copy,
  Check
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function TwoFactorSettings() {
  const [status, setStatus] = useState({ enabled: false, email: '' });
  const [loading, setLoading] = useState(true);
  const [setupData, setSetupData] = useState(null);
  const [verifyCode, setVerifyCode] = useState('');
  const [disableCode, setDisableCode] = useState('');
  const [processing, setProcessing] = useState(false);
  const [copied, setCopied] = useState(false);
  const { getAuthHeaders } = useAuth();

  const fetchStatus = async () => {
    try {
      const response = await axios.get(`${API}/auth/2fa/status`, {
        headers: getAuthHeaders()
      });
      setStatus(response.data);
    } catch (error) {
      console.error('Error fetching 2FA status:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const initiateSetup = async () => {
    setProcessing(true);
    try {
      const response = await axios.post(`${API}/auth/2fa/setup`, {}, {
        headers: getAuthHeaders()
      });
      setSetupData(response.data);
    } catch (error) {
      toast.error('Erro ao iniciar configuração 2FA');
    } finally {
      setProcessing(false);
    }
  };

  const verifySetup = async () => {
    if (!verifyCode || verifyCode.length !== 6) {
      toast.error('Insira um código de 6 dígitos');
      return;
    }

    setProcessing(true);
    try {
      const formData = new FormData();
      formData.append('code', verifyCode);
      
      await axios.post(`${API}/auth/2fa/verify-setup`, formData, {
        headers: getAuthHeaders()
      });
      
      toast.success('2FA ativado com sucesso!');
      setSetupData(null);
      setVerifyCode('');
      fetchStatus();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Código inválido');
    } finally {
      setProcessing(false);
    }
  };

  const disable2FA = async () => {
    if (!disableCode || disableCode.length !== 6) {
      toast.error('Insira um código de 6 dígitos');
      return;
    }

    setProcessing(true);
    try {
      const formData = new FormData();
      formData.append('code', disableCode);
      
      await axios.post(`${API}/auth/2fa/disable`, formData, {
        headers: getAuthHeaders()
      });
      
      toast.success('2FA desativado');
      setDisableCode('');
      fetchStatus();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Código inválido');
    } finally {
      setProcessing(false);
    }
  };

  const copySecret = () => {
    if (setupData?.secret) {
      navigator.clipboard.writeText(setupData.secret);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-6 h-6 animate-spin text-secondary" />
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-xl p-6" data-testid="2fa-settings">
      <div className="flex items-center gap-3 mb-6">
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${status.enabled ? 'bg-green-100' : 'bg-muted'}`}>
          {status.enabled ? (
            <ShieldCheck className="w-6 h-6 text-green-600" />
          ) : (
            <Shield className="w-6 h-6 text-muted-foreground" />
          )}
        </div>
        <div>
          <h3 className="text-lg font-semibold text-foreground">Autenticação de 2 Fatores (2FA)</h3>
          <p className="text-sm text-muted-foreground">
            {status.enabled ? 'Proteção adicional ativada' : 'Adicione uma camada extra de segurança'}
          </p>
        </div>
      </div>

      {status.enabled ? (
        /* 2FA Enabled - Show Disable Option */
        <div className="space-y-4">
          <div className="flex items-center gap-2 p-4 bg-green-50 rounded-lg border border-green-200">
            <ShieldCheck className="w-5 h-5 text-green-600" />
            <span className="text-green-700 font-medium">2FA está ativo na sua conta</span>
          </div>

          <div className="pt-4 border-t border-border">
            <p className="text-sm text-muted-foreground mb-3">
              Para desativar o 2FA, insira o código do seu app de autenticação:
            </p>
            <div className="flex gap-3">
              <Input
                type="text"
                placeholder="000000"
                maxLength={6}
                value={disableCode}
                onChange={(e) => setDisableCode(e.target.value.replace(/\D/g, ''))}
                className="w-32 text-center text-lg tracking-widest"
                data-testid="2fa-disable-code"
              />
              <Button
                variant="destructive"
                onClick={disable2FA}
                disabled={processing}
                data-testid="2fa-disable-btn"
              >
                {processing ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldOff className="w-4 h-4 mr-2" />}
                Desativar 2FA
              </Button>
            </div>
          </div>
        </div>
      ) : setupData ? (
        /* Setup Mode - Show QR Code */
        <div className="space-y-6">
          <div className="flex flex-col items-center text-center">
            <div className="mb-4">
              <img 
                src={setupData.qr_code} 
                alt="QR Code 2FA" 
                className="w-48 h-48 rounded-lg border border-border"
              />
            </div>
            <p className="text-sm text-muted-foreground mb-2">
              Escaneie o QR code com o seu app de autenticação
            </p>
            <p className="text-xs text-muted-foreground">
              (Google Authenticator, Authy, Microsoft Authenticator, etc.)
            </p>
          </div>

          <div className="p-4 bg-muted rounded-lg">
            <p className="text-xs text-muted-foreground mb-2">Ou insira este código manualmente:</p>
            <div className="flex items-center gap-2">
              <code className="flex-1 bg-card px-3 py-2 rounded border border-border text-sm font-mono">
                {setupData.secret}
              </code>
              <Button variant="outline" size="sm" onClick={copySecret}>
                {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
              </Button>
            </div>
          </div>

          <div className="pt-4 border-t border-border">
            <p className="text-sm text-muted-foreground mb-3">
              Após configurar o app, insira o código de 6 dígitos para verificar:
            </p>
            <div className="flex gap-3">
              <Input
                type="text"
                placeholder="000000"
                maxLength={6}
                value={verifyCode}
                onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, ''))}
                className="w-32 text-center text-lg tracking-widest"
                data-testid="2fa-verify-code"
              />
              <Button
                onClick={verifySetup}
                disabled={processing}
                className="bg-secondary hover:bg-secondary/90"
                data-testid="2fa-verify-btn"
              >
                {processing ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Verificar e Ativar'}
              </Button>
            </div>
          </div>

          <Button
            variant="ghost"
            onClick={() => setSetupData(null)}
            className="w-full"
          >
            Cancelar
          </Button>
        </div>
      ) : (
        /* Initial State - Show Enable Button */
        <div className="space-y-4">
          <div className="p-4 bg-muted rounded-lg space-y-2">
            <div className="flex items-center gap-2">
              <Smartphone className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm font-medium text-foreground">O que precisa:</span>
            </div>
            <ul className="text-sm text-muted-foreground space-y-1 ml-6">
              <li>• Um smartphone com app de autenticação instalado</li>
              <li>• Google Authenticator, Authy ou similar</li>
            </ul>
          </div>

          <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
            <div className="flex items-start gap-2">
              <Key className="w-4 h-4 text-yellow-600 mt-0.5" />
              <p className="text-sm text-yellow-700">
                Com 2FA ativo, será necessário um código do app de autenticação além da password para fazer login.
              </p>
            </div>
          </div>

          <Button
            onClick={initiateSetup}
            disabled={processing}
            className="w-full bg-secondary hover:bg-secondary/90"
            data-testid="2fa-setup-btn"
          >
            {processing ? (
              <Loader2 className="w-4 h-4 animate-spin mr-2" />
            ) : (
              <Shield className="w-4 h-4 mr-2" />
            )}
            Configurar 2FA
          </Button>
        </div>
      )}
    </div>
  );
}
