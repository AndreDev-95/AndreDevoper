import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
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
  ArrowLeft,
  Send,
  Euro,
  FileText,
  Image,
  Upload,
  Download,
  Check,
  Clock,
  MessageSquare,
  Paperclip,
  Eye
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ProjectDetails() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const { getAuthHeaders, user } = useAuth();
  
  const [project, setProject] = useState(null);
  const [messages, setMessages] = useState([]);
  const [files, setFiles] = useState([]);
  const [previews, setPreviews] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [newMessage, setNewMessage] = useState('');
  const [sendingMessage, setSendingMessage] = useState(false);
  
  const [uploadDialog, setUploadDialog] = useState(false);
  const [fileName, setFileName] = useState('');
  const [fileUrl, setFileUrl] = useState('');
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchProjectDetails();
  }, [projectId]);

  const fetchProjectDetails = async () => {
    try {
      const [projectRes, messagesRes, filesRes, previewsRes] = await Promise.all([
        axios.get(`${API}/projects/${projectId}`, { headers: getAuthHeaders() }),
        axios.get(`${API}/projects/${projectId}/messages`, { headers: getAuthHeaders() }),
        axios.get(`${API}/projects/${projectId}/files`, { headers: getAuthHeaders() }),
        axios.get(`${API}/projects/${projectId}/previews`, { headers: getAuthHeaders() })
      ]);
      
      setProject(projectRes.data);
      setMessages(messagesRes.data);
      setFiles(filesRes.data);
      setPreviews(previewsRes.data);
    } catch (error) {
      console.error('Error fetching project:', error);
      toast.error('Erro ao carregar projeto');
      navigate('/dashboard/projects');
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    setSendingMessage(true);
    try {
      await axios.post(
        `${API}/projects/${projectId}/messages`,
        { content: newMessage },
        { headers: getAuthHeaders() }
      );
      setNewMessage('');
      toast.success('Mensagem enviada');
      fetchProjectDetails();
    } catch (error) {
      toast.error('Erro ao enviar mensagem');
    } finally {
      setSendingMessage(false);
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!fileName.trim() || !fileUrl.trim()) {
      toast.error('Preencha todos os campos');
      return;
    }

    setUploading(true);
    try {
      await axios.post(
        `${API}/projects/${projectId}/files`,
        { filename: fileName, file_url: fileUrl },
        { headers: getAuthHeaders() }
      );
      setFileName('');
      setFileUrl('');
      setUploadDialog(false);
      toast.success('Ficheiro adicionado');
      fetchProjectDetails();
    } catch (error) {
      toast.error('Erro ao adicionar ficheiro');
    } finally {
      setUploading(false);
    }
  };

  const handleAcceptProposal = async () => {
    if (!window.confirm('Tem certeza que deseja aceitar esta proposta? O valor tornar-se-á oficial.')) return;

    try {
      await axios.post(
        `${API}/projects/${projectId}/accept-proposal`,
        {},
        { headers: getAuthHeaders() }
      );
      toast.success('Proposta aceite! Valor oficial definido.');
      fetchProjectDetails();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao aceitar proposta');
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
      pending: { label: 'Aguarda Resposta', class: 'bg-orange-100 text-orange-700', icon: Clock },
      accepted: { label: 'Aceite', class: 'bg-green-100 text-green-700', icon: Check },
      counter_proposal: { label: 'Contraproposta Recebida', class: 'bg-purple-100 text-purple-700', icon: Euro }
    };
    return badges[budgetStatus] || badges.pending;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-secondary"></div>
      </div>
    );
  }

  if (!project) return null;

  const statusBadge = getStatusBadge(project.status);
  const budgetBadge = getBudgetStatusBadge(project.budget_status);
  const BudgetIcon = budgetBadge.icon;

  return (
    <div className="min-h-screen bg-muted p-4 sm:p-6 lg:p-12">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <Link to="/dashboard/projects" className="inline-flex items-center gap-2 text-muted-foreground hover:text-primary mb-4">
            <ArrowLeft className="w-4 h-4" />
            Voltar aos Projetos
          </Link>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-primary mb-2">{project.name}</h1>
              <div className="flex flex-wrap gap-2">
                <span className={`text-xs px-3 py-1 rounded-full ${statusBadge.class}`}>
                  {statusBadge.label}
                </span>
                <span className="text-xs bg-muted px-3 py-1 rounded text-muted-foreground">
                  {project.project_type === 'web' ? 'Website' : project.project_type === 'android' ? 'Android' : 'iOS'}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Project Info & Budget */}
          <div className="lg:col-span-1 space-y-6">
            {/* Project Info */}
            <div className="bg-white border border-border p-6 rounded-xl">
              <h2 className="text-lg font-semibold text-primary mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Informações do Projeto
              </h2>
              <div className="space-y-3">
                <div>
                  <label className="text-sm text-muted-foreground">Descrição</label>
                  <p className="text-sm text-foreground mt-1">{project.description}</p>
                </div>
                <div>
                  <label className="text-sm text-muted-foreground">Criado em</label>
                  <p className="text-sm text-foreground mt-1">
                    {new Date(project.created_at).toLocaleDateString('pt-PT')}
                  </p>
                </div>
              </div>
            </div>

            {/* Budget Info */}
            <div className="bg-white border border-border p-6 rounded-xl">
              <h2 className="text-lg font-semibold text-primary mb-4 flex items-center gap-2">
                <Euro className="w-5 h-5" />
                Orçamento
              </h2>
              <div className="space-y-4">
                <div className={`p-4 rounded-lg ${budgetBadge.class.replace('text-', 'bg-').replace('-700', '-50')} border`}>
                  <div className="flex items-center gap-2 mb-2">
                    <BudgetIcon className="w-4 h-4" />
                    <span className="text-sm font-medium">{budgetBadge.label}</span>
                  </div>
                </div>

                <div>
                  <label className="text-sm text-muted-foreground">Proposta Inicial</label>
                  <p className="text-lg font-semibold text-primary mt-1">{project.budget}</p>
                </div>

                {project.counter_proposal && (
                  <div>
                    <label className="text-sm text-muted-foreground">Contraproposta</label>
                    <p className="text-lg font-semibold text-purple-700 mt-1">{project.counter_proposal}</p>
                  </div>
                )}

                {project.admin_notes && (
                  <div>
                    <label className="text-sm text-muted-foreground">Notas do Admin</label>
                    <p className="text-sm text-foreground mt-1 italic">{project.admin_notes}</p>
                  </div>
                )}

                {project.official_value && (
                  <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                    <label className="text-sm text-green-700 font-medium">Valor Oficial</label>
                    <p className="text-2xl font-bold text-green-700 mt-1">{project.official_value}</p>
                    <p className="text-xs text-green-600 mt-1">Proposta aceite</p>
                  </div>
                )}

                {!project.official_value && project.budget_status === 'counter_proposal' && (
                  <Button 
                    onClick={handleAcceptProposal}
                    className="w-full bg-green-600 hover:bg-green-700"
                  >
                    <Check className="w-4 h-4 mr-2" />
                    Aceitar Contraproposta
                  </Button>
                )}
              </div>
            </div>

            {/* Files */}
            <div className="bg-white border border-border p-6 rounded-xl">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-primary flex items-center gap-2">
                  <Paperclip className="w-5 h-5" />
                  Ficheiros
                </h2>
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => setUploadDialog(true)}
                >
                  <Upload className="w-4 h-4 mr-2" />
                  Adicionar
                </Button>
              </div>
              
              {files.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">Sem ficheiros</p>
              ) : (
                <div className="space-y-2">
                  {files.map((file) => (
                    <div 
                      key={file.id}
                      className="flex items-center justify-between p-3 bg-muted rounded-lg"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-primary truncate">{file.filename}</p>
                        <p className="text-xs text-muted-foreground">
                          Por {file.uploaded_by_name} • {new Date(file.created_at).toLocaleDateString('pt-PT')}
                        </p>
                      </div>
                      <a 
                        href={file.file_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="ml-2 p-2 hover:bg-background rounded"
                      >
                        <Download className="w-4 h-4 text-secondary" />
                      </a>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Column - Chat & Previews */}
          <div className="lg:col-span-2 space-y-6">
            {/* Chat */}
            <div className="bg-white border border-border rounded-xl overflow-hidden flex flex-col" style={{ height: '500px' }}>
              <div className="p-4 border-b border-border">
                <h2 className="text-lg font-semibold text-primary flex items-center gap-2">
                  <MessageSquare className="w-5 h-5" />
                  Chat do Projeto
                </h2>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-8">Sem mensagens ainda. Inicie a conversa!</p>
                ) : (
                  messages.map((msg) => {
                    const isOwnMessage = msg.user_id === user?.id;
                    return (
                      <div 
                        key={msg.id}
                        className={`flex ${isOwnMessage ? 'justify-end' : 'justify-start'}`}
                      >
                        <div className={`max-w-[70%] ${isOwnMessage ? 'bg-secondary text-white' : 'bg-muted'} rounded-lg p-3`}>
                          <p className="text-xs font-medium mb-1 opacity-80">{msg.user_name}</p>
                          <p className="text-sm">{msg.content}</p>
                          <p className="text-xs opacity-60 mt-1">
                            {new Date(msg.created_at).toLocaleTimeString('pt-PT', { hour: '2-digit', minute: '2-digit' })}
                          </p>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

              {/* Message Input */}
              <div className="p-4 border-t border-border">
                <form onSubmit={handleSendMessage} className="flex gap-2">
                  <Input
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="Escreva uma mensagem..."
                    className="flex-1"
                  />
                  <Button type="submit" disabled={sendingMessage || !newMessage.trim()}>
                    <Send className="w-4 h-4" />
                  </Button>
                </form>
              </div>
            </div>

            {/* Previews */}
            <div className="bg-white border border-border p-6 rounded-xl">
              <h2 className="text-lg font-semibold text-primary mb-4 flex items-center gap-2">
                <Eye className="w-5 h-5" />
                Previews do Projeto
              </h2>
              
              {previews.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-8">
                  Sem previews ainda. O administrador irá adicionar conforme o projeto avança.
                </p>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {previews.map((preview) => (
                    <div key={preview.id} className="border border-border rounded-lg overflow-hidden">
                      <img 
                        src={preview.image_url}
                        alt={preview.description || 'Preview'}
                        className="w-full h-48 object-cover"
                      />
                      {preview.description && (
                        <div className="p-3 bg-muted">
                          <p className="text-sm text-foreground">{preview.description}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Upload Dialog */}
      <Dialog open={uploadDialog} onOpenChange={setUploadDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Adicionar Ficheiro</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleFileUpload} className="space-y-4 mt-4">
            <div>
              <label className="block text-sm font-medium mb-2">Nome do Ficheiro</label>
              <Input
                value={fileName}
                onChange={(e) => setFileName(e.target.value)}
                placeholder="Ex: Documento.pdf"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">URL do Ficheiro</label>
              <Input
                value={fileUrl}
                onChange={(e) => setFileUrl(e.target.value)}
                placeholder="Ex: https://..."
                required
              />
              <p className="text-xs text-muted-foreground mt-1">
                Cole a URL do ficheiro hospedado (Google Drive, Dropbox, etc.)
              </p>
            </div>
            <Button type="submit" disabled={uploading} className="w-full">
              {uploading ? 'A adicionar...' : 'Adicionar Ficheiro'}
            </Button>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
