import { useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import {
  Elements,
  PaymentElement,
  useStripe,
  useElements,
} from '@stripe/react-stripe-js';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import axios from 'axios';
import { useAuth } from '@/context/AuthContext';
import { CreditCard, Loader2, CheckCircle2, ShieldCheck } from 'lucide-react';

// Only load Stripe if the key is available
const stripeKey = process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY;
const stripePromise = stripeKey ? loadStripe(stripeKey) : null;

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function CheckoutForm({ projectId, amount, onSuccess, onCancel }) {
  const stripe = useStripe();
  const elements = useElements();
  const [processing, setProcessing] = useState(false);
  const { getAuthHeaders } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!stripe || !elements) {
      return;
    }

    setProcessing(true);

    try {
      const { error, paymentIntent } = await stripe.confirmPayment({
        elements,
        confirmParams: {
          return_url: window.location.href,
        },
        redirect: 'if_required',
      });

      if (error) {
        toast.error(error.message);
        setProcessing(false);
        return;
      }

      if (paymentIntent && paymentIntent.status === 'succeeded') {
        // Confirm payment on backend
        await axios.post(
          `${API}/projects/${projectId}/confirm-payment`,
          null,
          {
            params: { payment_intent_id: paymentIntent.id },
            headers: getAuthHeaders(),
          }
        );
        toast.success('Pagamento realizado com sucesso!');
        onSuccess?.();
      }
    } catch (err) {
      toast.error('Erro ao processar pagamento');
      console.error(err);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="bg-muted/50 rounded-lg p-4 mb-4">
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground">Total a pagar:</span>
          <span className="text-2xl font-bold text-primary">€{amount}</span>
        </div>
      </div>

      <PaymentElement 
        options={{
          layout: 'tabs',
        }}
      />

      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <ShieldCheck className="w-4 h-4 text-green-500" />
        Pagamento seguro processado pelo Stripe
      </div>

      <div className="flex gap-3">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={processing}
          className="flex-1"
        >
          Cancelar
        </Button>
        <Button
          type="submit"
          disabled={!stripe || processing}
          className="flex-1 bg-secondary hover:bg-secondary/90"
        >
          {processing ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              A processar...
            </>
          ) : (
            <>
              <CreditCard className="w-4 h-4 mr-2" />
              Pagar €{amount}
            </>
          )}
        </Button>
      </div>
    </form>
  );
}

export default function PaymentModal({ project, isOpen, onClose, onSuccess }) {
  const [clientSecret, setClientSecret] = useState(null);
  const [amount, setAmount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [paid, setPaid] = useState(false);
  const { getAuthHeaders } = useAuth();

  const initPayment = async () => {
    if (clientSecret) return;
    
    setLoading(true);
    try {
      const response = await axios.post(
        `${API}/projects/${project.id}/create-payment`,
        {},
        { headers: getAuthHeaders() }
      );
      setClientSecret(response.data.client_secret);
      setAmount(response.data.amount);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao iniciar pagamento');
      onClose();
    } finally {
      setLoading(false);
    }
  };

  const handleSuccess = () => {
    setPaid(true);
    setTimeout(() => {
      onSuccess?.();
      onClose();
    }, 2000);
  };

  if (!isOpen) return null;

  // Initialize payment when modal opens
  if (!clientSecret && !loading && !paid) {
    initPayment();
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-card rounded-xl shadow-xl max-w-md w-full p-6 relative">
        <h2 className="text-xl font-bold text-primary mb-4 flex items-center gap-2">
          <CreditCard className="w-5 h-5 text-secondary" />
          Pagamento do Projeto
        </h2>
        
        <p className="text-muted-foreground mb-6">
          Projeto: <strong>{project.name}</strong>
        </p>

        {paid ? (
          <div className="text-center py-8">
            <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-primary mb-2">Pagamento Confirmado!</h3>
            <p className="text-muted-foreground">O seu projeto foi iniciado.</p>
          </div>
        ) : loading ? (
          <div className="flex flex-col items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-secondary mb-4" />
            <p className="text-muted-foreground">A preparar pagamento...</p>
          </div>
        ) : clientSecret ? (
          <Elements
            stripe={stripePromise}
            options={{
              clientSecret,
              appearance: {
                theme: 'stripe',
                variables: {
                  colorPrimary: '#3b82f6',
                  colorBackground: '#ffffff',
                  colorText: '#1e293b',
                  colorDanger: '#ef4444',
                  borderRadius: '8px',
                },
              },
            }}
          >
            <CheckoutForm
              projectId={project.id}
              amount={amount}
              onSuccess={handleSuccess}
              onCancel={onClose}
            />
          </Elements>
        ) : null}
      </div>
    </div>
  );
}
