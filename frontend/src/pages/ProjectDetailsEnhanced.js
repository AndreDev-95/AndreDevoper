import { useState, useEffect, useRef } from 'react';
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
import PaymentModal from '@/components/PaymentModal';
import { 
  ArrowLeft,
  Send,
  Euro,
  FileText,
  Image as ImageIcon,
  Upload,
  Download,
  Check,
  Clock,
  MessageSquare,
  Paperclip,
  Eye,
  Edit2,
  Trash2,
  X,
  File,
  Reply,
  Settings,
  CreditCard
} from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ProjectDetailsEnhanced() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const { getAuthHeaders, user, isAdmin } = useAuth();
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  
  const [project, setProject] = useState(null);
  const [messages, setMessages] = useState([]);
  const [files, setFiles] = useState([]);
  const [previews, setPreviews] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [newMessage, setNewMessage] = useState('');
  const [sendingMessage, setSendingMessage] = useState(false);
  const [messageAttachment, setMessageAttachment] = useState(null);
  
  const [editingMessage, setEditingMessage] = useState(null);
  const [editContent, setEditContent] = useState('');
  
  const [uploadDialog, setUploadDialog] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);
  
  // Payment modal
  const [paymentModalOpen, setPaymentModalOpen] = useState(false);

  // Admin-specific states
  const [budgetResponseDialog, setBudgetResponseDialog] = useState(false);
  const [budgetResponse, setBudgetResponse] = useState({
    budget_status: 'accepted',
    counter_proposal: '',
    admin_notes: ''
  });
  const [responding, setResponding] = useState(false);

  // Preview dialog for admin
  const [previewDialog, setPreviewDialog] = useState(false);
  const [newPreview, setNewPreview] = useState({ image_url: '', description: '', image_data: '' });
  const [addingPreview, setAddingPreview] = useState(false);
  const [previewFile, setPreviewFile] = useState(null);

  // Track previous message count for notifications
  const [prevMessageCount, setPrevMessageCount] = useState(0);
  const [prevBudgetStatus, setPrevBudgetStatus] = useState(null);

  // Polling for new messages with notifications
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const [messagesRes, projectRes] = await Promise.all([
          axios.get(`${API}/projects/${projectId}/messages`, { headers: getAuthHeaders() }),
          isAdmin() 
            ? axios.get(`${API}/admin/projects/${projectId}`, { headers: getAuthHeaders() })
            : axios.get(`${API}/projects/${projectId}`, { headers: getAuthHeaders() })
        ]);
        
        const newMessages = messagesRes.data;
        const newProject = projectRes.data;
        
        // Check for new messages from others
        if (prevMessageCount > 0 && newMessages.length > prevMessageCount) {
          const latestMsg = newMessages[newMessages.length - 1];
          if (latestMsg.user_id !== user?.id) {
            toast.info(`Nova mensagem de ${latestMsg.user_name}`, {
              description: latestMsg.content.substring(0, 50) + (latestMsg.content.length > 50 ? '...' : ''),
              duration: 5000
            });
          }
        }
        
        // Check for budget status changes (for client)
        if (!isAdmin() && prevBudgetStatus && newProject.budget_status !== prevBudgetStatus) {
          if (newProject.budget_status === 'accepted') {
            toast.success('O administrador aceitou o seu orçamento!', { duration: 6000 });
          } else if (newProject.budget_status === 'counter_proposal') {
            toast.info('O administrador enviou uma contraproposta!', { 
              description: `Novo valor: ${newProject.counter_proposal}`,
              duration: 6000 
            });
          }
        }
        
        setMessages(newMessages);
        setPrevMessageCount(newMessages.length);
        setProject(newProject);
        setPrevBudgetStatus(newProject.budget_status);
      } catch (error) {
        console.error('Error polling:', error);
      }
    }, 5000); // Check every 5 seconds
    
    return () => clearInterval(interval);
  }, [projectId, prevMessageCount, prevBudgetStatus, user?.id]);

  useEffect(() => {
    fetchProjectDetails();
  }, [projectId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchProjectDetails = async () => {
    try {
      const projectEndpoint = isAdmin() ? `${API}/admin/projects/${projectId}` : `${API}/projects/${projectId}`;
      const [projectRes, messagesRes, filesRes, previewsRes] = await Promise.all([
        axios.get(projectEndpoint, { headers: getAuthHeaders() }),
        axios.get(`${API}/projects/${projectId}/messages`, { headers: getAuthHeaders() }),
        axios.get(`${API}/projects/${projectId}/files`, { headers: getAuthHeaders() }),
        axios.get(`${API}/projects/${projectId}/previews`, { headers: getAuthHeaders() })
      ]);
      
      setProject(projectRes.data);
      setMessages(messagesRes.data);
      setPrevMessageCount(messagesRes.data.length);
      setPrevBudgetStatus(projectRes.data.budget_status);
      setFiles(filesRes.data);
      setPreviews(previewsRes.data);
    } catch (error) {
      console.error('Error fetching project:', error);
      toast.error('Erro ao carregar projeto');
      navigate(isAdmin() ? '/admin/projects' : '/dashboard/projects');
    } finally {
      setLoading(false);
    }
  };

  const fetchMessages = async () => {
    try {
      const res = await axios.get(`${API}/projects/${projectId}/messages`, { 
        headers: getAuthHeaders() 
      });
      setMessages(res.data);
      setPrevMessageCount(res.data.length);
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Check file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('Ficheiro muito grande. Máximo 10MB');
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      setMessageAttachment({
        filename: file.name,
        file_data: reader.result.split(',')[1], // Get base64 without prefix
        mime_type: file.type
      });
    };
    reader.readAsDataURL(file);
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() && !messageAttachment) return;

    setSendingMessage(true);
    try {
      const payload = {
        content: newMessage || '(Ficheiro anexado)',
        attachment: messageAttachment
      };

      await axios.post(
        `${API}/projects/${projectId}/messages`,
        payload,
        { headers: getAuthHeaders() }
      );
      
      setNewMessage('');
      setMessageAttachment(null);
      toast.success('Mensagem enviada');
      fetchMessages();
    } catch (error) {
      toast.error('Erro ao enviar mensagem');
    } finally {
      setSendingMessage(false);
    }
  };

  const handleEditMessage = async (messageId) => {
    if (!editContent.trim()) return;

    try {
      await axios.put(
        `${API}/projects/${projectId}/messages/${messageId}`,
        { content: editContent },
        { headers: getAuthHeaders() }
      );
      toast.success('Mensagem editada');
      setEditingMessage(null);
      fetchMessages();
    } catch (error) {
      toast.error('Erro ao editar mensagem');
    }
  };

  const handleDeleteMessage = async (messageId) => {
    if (!window.confirm('Eliminar esta mensagem?')) return;

    try {
      await axios.delete(
        `${API}/projects/${projectId}/messages/${messageId}`,
        { headers: getAuthHeaders() }
      );
      toast.success('Mensagem eliminada');
      fetchMessages();
    } catch (error) {
      toast.error('Erro ao eliminar mensagem');
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    const file = e.target.elements.fileInput.files[0];
    if (!file) {
      toast.error('Selecione um ficheiro');
      return;
    }

    // Check file size - 50MB limit for regular files
    if (file.size > 50 * 1024 * 1024) {
      toast.error('Ficheiro muito grande. Máximo 50MB.', { duration: 5000 });
      return;
    }

    setUploadingFile(true);
    const reader = new FileReader();
    
    reader.onload = async () => {
      try {
        await axios.post(
          `${API}/projects/${projectId}/files`,
          { 
            filename: file.name,
            file_data: reader.result.split(',')[1]
          },
          { headers: getAuthHeaders() }
        );
        
        setUploadDialog(false);
        toast.success('Ficheiro carregado');
        fetchProjectDetails();
      } catch (error) {
        toast.error(error.response?.data?.detail || 'Erro ao carregar ficheiro');
      } finally {
        setUploadingFile(false);
      }
    };

    reader.readAsDataURL(file);
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

  // Admin-specific functions
  const handleBudgetResponse = async () => {
    if (budgetResponse.budget_status === 'counter_proposal' && !budgetResponse.counter_proposal.trim()) {
      toast.error('Por favor, insira um valor para a contraproposta');
      return;
    }

    setResponding(true);
    try {
      await axios.put(
        `${API}/admin/projects/${projectId}/budget-response`,
        budgetResponse,
        { headers: getAuthHeaders() }
      );
      toast.success('Resposta ao orçamento enviada');
      setBudgetResponseDialog(false);
      setBudgetResponse({ budget_status: 'accepted', counter_proposal: '', admin_notes: '' });
      fetchProjectDetails();
    } catch (error) {
      toast.error('Erro ao responder ao orçamento');
    } finally {
      setResponding(false);
    }
  };

  const handlePreviewFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Check if it's image or video
    if (!file.type.startsWith('image/') && !file.type.startsWith('video/')) {
      toast.error('Apenas imagens e vídeos são permitidos');
      return;
    }

    // Check file size (500MB limit for videos, 50MB for images)
    const maxSize = file.type.startsWith('video/') ? 500 * 1024 * 1024 : 50 * 1024 * 1024;
    if (file.size > maxSize) {
      toast.error(`Ficheiro muito grande. Máximo ${file.type.startsWith('video/') ? '500MB' : '50MB'}`);
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      setPreviewFile({
        name: file.name,
        type: file.type,
        size: file.size,
        data: reader.result.split(',')[1] // Get base64 without prefix
      });
    };
    reader.readAsDataURL(file);
  };

  const handleAddPreview = async (e) => {
    e.preventDefault();
    
    // Must have either URL or uploaded file
    if (!newPreview.image_url.trim() && !previewFile) {
      toast.error('Por favor, insira uma URL ou faça upload de um ficheiro');
      return;
    }

    setAddingPreview(true);
    try {
      const payload = {
        description: newPreview.description,
        image_url: newPreview.image_url,
        image_data: previewFile?.data || null,
        mime_type: previewFile?.type || null
      };

      await axios.post(
        `${API}/projects/${projectId}/previews`,
        payload,
        { headers: getAuthHeaders() }
      );
      toast.success('Preview adicionado');
      setPreviewDialog(false);
      setNewPreview({ image_url: '', description: '', image_data: '' });
      setPreviewFile(null);
      fetchProjectDetails();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao adicionar preview');
    } finally {
      setAddingPreview(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      await axios.put(
        `${API}/admin/projects/${projectId}/status?status=${newStatus}`,
        {},
        { headers: getAuthHeaders() }
      );
      toast.success('Estado atualizado');
      fetchProjectDetails();
    } catch (error) {
      toast.error('Erro ao atualizar estado');
    }
  };


  const downloadFile = (file) => {
    let fileUrl = file.file_url;
    
    // Handle server-stored files - both /uploads/ and /api/uploads/ paths
    if (fileUrl?.startsWith('/uploads/') || fileUrl?.startsWith('/api/uploads/')) {
      fileUrl = `${BACKEND_URL}${fileUrl}`;
    }
    
    if (fileUrl) {
      window.open(fileUrl, '_blank');
    } else if (file.file_data) {
      // Legacy: base64 data stored directly
      const link = document.createElement('a');
      link.href = `data:application/octet-stream;base64,${file.file_data}`;
      link.download = file.filename;
      link.click();
    }
  };

  const downloadAttachment = (attachment) => {
    const link = document.createElement('a');
    link.href = `data:${attachment.mime_type};base64,${attachment.file_data}`;
    link.download = attachment.filename;
    link.click();
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
          <Link 
            to={isAdmin() ? "/admin/projects" : "/dashboard/projects"} 
            className="inline-flex items-center gap-2 text-muted-foreground hover:text-primary mb-4"
          >
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
            
            {/* Admin Controls */}
            {isAdmin() && (
              <div className="flex flex-wrap gap-2">
                <Select value={project.status} onValueChange={handleStatusChange}>
                  <SelectTrigger className="w-40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pending">Pendente</SelectItem>
                    <SelectItem value="in_progress">Em Progresso</SelectItem>
                    <SelectItem value="completed">Concluído</SelectItem>
                  </SelectContent>
                </Select>
                
                {project.budget_status === 'pending' && (
                  <Button onClick={() => setBudgetResponseDialog(true)} className="bg-secondary">
                    <Euro className="w-4 h-4 mr-2" />
                    Responder Orçamento
                  </Button>
                )}
                
                <Button onClick={() => setPreviewDialog(true)} variant="outline">
                  <Eye className="w-4 h-4 mr-2" />
                  Adicionar Preview
                </Button>
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column */}
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

                {/* PDF Download and Payment Buttons */}
                <div className="flex flex-col gap-2 pt-4 border-t border-border">
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={async () => {
                      try {
                        const response = await axios.get(
                          `${API}/projects/${project.id}/pdf?doc_type=budget`,
                          { 
                            headers: getAuthHeaders(),
                            responseType: 'blob'
                          }
                        );
                        const url = window.URL.createObjectURL(new Blob([response.data]));
                        const link = document.createElement('a');
                        link.href = url;
                        link.setAttribute('download', `orcamento_${project.name.replace(/\s+/g, '_')}.pdf`);
                        document.body.appendChild(link);
                        link.click();
                        link.remove();
                        window.URL.revokeObjectURL(url);
                      } catch (error) {
                        toast.error('Erro ao descarregar PDF');
                      }
                    }}
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Download Orçamento (PDF)
                  </Button>
                  
                  {project.budget_status === 'accepted' && !project.payment_status && !isAdmin() && (
                    <Button
                      onClick={() => setPaymentModalOpen(true)}
                      className="w-full bg-green-600 hover:bg-green-700"
                    >
                      <CreditCard className="w-4 h-4 mr-2" />
                      Pagar Agora
                    </Button>
                  )}
                  
                  {project.payment_status === 'paid' && (
                    <>
                      <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-center dark:bg-green-900/20 dark:border-green-800">
                        <Check className="w-5 h-5 text-green-600 dark:text-green-400 mx-auto mb-1" />
                        <p className="text-sm font-medium text-green-700 dark:text-green-400">Pago</p>
                        <p className="text-xs text-green-600 dark:text-green-500">
                          {project.payment_date && new Date(project.payment_date).toLocaleDateString('pt-PT')}
                        </p>
                      </div>
                      <Button
                        variant="outline"
                        className="w-full"
                        onClick={async () => {
                          try {
                            const response = await axios.get(
                              `${API}/projects/${project.id}/pdf?doc_type=invoice`,
                              { 
                                headers: getAuthHeaders(),
                                responseType: 'blob'
                              }
                            );
                            const url = window.URL.createObjectURL(new Blob([response.data]));
                            const link = document.createElement('a');
                            link.href = url;
                            link.setAttribute('download', `fatura_${project.name.replace(/\s+/g, '_')}.pdf`);
                            document.body.appendChild(link);
                            link.click();
                            link.remove();
                            window.URL.revokeObjectURL(url);
                          } catch (error) {
                            toast.error('Erro ao descarregar PDF');
                          }
                        }}
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Download Fatura (PDF)
                      </Button>
                    </>
                  )}
                </div>
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
                      <div className="flex-1 min-w-0 flex items-center gap-2">
                        <File className="w-4 h-4 text-secondary flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-primary truncate">{file.filename}</p>
                          <p className="text-xs text-muted-foreground">
                            Por {file.uploaded_by_name} • {new Date(file.created_at).toLocaleDateString('pt-PT')}
                          </p>
                        </div>
                      </div>
                      <button 
                        onClick={() => downloadFile(file)}
                        className="ml-2 p-2 hover:bg-background rounded"
                      >
                        <Download className="w-4 h-4 text-secondary" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Column */}
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
                          
                          {editingMessage === msg.id ? (
                            <div className="space-y-2">
                              <Textarea
                                value={editContent}
                                onChange={(e) => setEditContent(e.target.value)}
                                className="text-sm"
                              />
                              <div className="flex gap-2">
                                <Button size="sm" onClick={() => handleEditMessage(msg.id)}>Guardar</Button>
                                <Button size="sm" variant="outline" onClick={() => setEditingMessage(null)}>Cancelar</Button>
                              </div>
                            </div>
                          ) : (
                            <>
                              <p className="text-sm">{msg.content}</p>
                              
                              {msg.attachment && (
                                <div className="mt-2 p-2 bg-black/10 rounded flex items-center justify-between">
                                  <div className="flex items-center gap-2">
                                    <Paperclip className="w-4 h-4" />
                                    <span className="text-xs">{msg.attachment.filename}</span>
                                  </div>
                                  <button onClick={() => downloadAttachment(msg.attachment)}>
                                    <Download className="w-4 h-4" />
                                  </button>
                                </div>
                              )}
                              
                              <div className="flex items-center justify-between mt-2">
                                <p className="text-xs opacity-60">
                                  {new Date(msg.created_at).toLocaleTimeString('pt-PT', { hour: '2-digit', minute: '2-digit' })}
                                  {msg.edited && ' (editada)'}
                                </p>
                                
                                {isOwnMessage && (
                                  <div className="flex gap-1">
                                    <button 
                                      onClick={() => {
                                        setEditingMessage(msg.id);
                                        setEditContent(msg.content);
                                      }}
                                      className="p-1 hover:bg-white/20 rounded"
                                    >
                                      <Edit2 className="w-3 h-3" />
                                    </button>
                                    <button 
                                      onClick={() => handleDeleteMessage(msg.id)}
                                      className="p-1 hover:bg-white/20 rounded"
                                    >
                                      <Trash2 className="w-3 h-3" />
                                    </button>
                                  </div>
                                )}
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Message Input */}
              <div className="p-4 border-t border-border">
                {messageAttachment && (
                  <div className="mb-2 p-2 bg-muted rounded flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Paperclip className="w-4 h-4" />
                      <span className="text-sm">{messageAttachment.filename}</span>
                    </div>
                    <button onClick={() => setMessageAttachment(null)}>
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}
                
                <form onSubmit={handleSendMessage} className="flex gap-2">
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Paperclip className="w-4 h-4" />
                  </Button>
                  <Input
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="Escreva uma mensagem..."
                    className="flex-1"
                  />
                  <Button type="submit" disabled={sendingMessage || (!newMessage.trim() && !messageAttachment)}>
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
                  {previews.map((preview) => {
                    const isVideo = preview.mime_type?.startsWith('video/');
                    // Use image_url (now contains the file path) or image_data for backwards compatibility
                    let mediaUrl = preview.image_url;
                    if (preview.image_data && !preview.image_url) {
                      // Legacy: base64 data stored directly
                      mediaUrl = `data:${preview.mime_type};base64,${preview.image_data}`;
                    } else if (preview.image_url?.startsWith('/uploads/') || preview.image_url?.startsWith('/api/uploads/')) {
                      // New: file stored on server - prepend backend URL
                      mediaUrl = `${BACKEND_URL}${preview.image_url}`;
                    }
                    
                    return (
                      <div key={preview.id} className="border border-border rounded-lg overflow-hidden">
                        {isVideo ? (
                          <video 
                            src={mediaUrl}
                            controls
                            className="w-full h-48 object-cover bg-black"
                          >
                            Seu navegador não suporta vídeos.
                          </video>
                        ) : (
                          <img 
                            src={mediaUrl}
                            alt={preview.description || 'Preview'}
                            className="w-full h-48 object-cover"
                          />
                        )}
                        {preview.description && (
                          <div className="p-3 bg-muted">
                            <p className="text-sm text-foreground">{preview.description}</p>
                          </div>
                        )}
                      </div>
                    );
                  })}
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
              <label className="block text-sm font-medium mb-2">Selecione o ficheiro</label>
              <input
                type="file"
                name="fileInput"
                className="w-full border border-border rounded p-2"
                required
              />
              <p className="text-xs text-muted-foreground mt-1">
                Máximo 50MB. Suporta todos os tipos de ficheiros.
              </p>
            </div>
            <Button type="submit" disabled={uploadingFile} className="w-full">
              {uploadingFile ? 'A carregar...' : 'Carregar Ficheiro'}
            </Button>
          </form>
        </DialogContent>
      </Dialog>

      {/* Budget Response Dialog (Admin only) */}
      {isAdmin() && (
        <Dialog open={budgetResponseDialog} onOpenChange={setBudgetResponseDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Euro className="w-5 h-5 text-secondary" />
                Responder ao Orçamento
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div className="bg-muted p-3 rounded-lg">
                <p className="text-sm">
                  <span className="text-muted-foreground">Orçamento proposto: </span>
                  <span className="font-semibold text-primary">{project?.budget}</span>
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Sua Resposta</label>
                <Select 
                  value={budgetResponse.budget_status}
                  onValueChange={(value) => setBudgetResponse({...budgetResponse, budget_status: value})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="accepted">
                      <span className="flex items-center gap-2">
                        <Check className="w-4 h-4 text-green-600" />
                        Aceitar Orçamento
                      </span>
                    </SelectItem>
                    <SelectItem value="counter_proposal">
                      <span className="flex items-center gap-2">
                        <Reply className="w-4 h-4 text-purple-600" />
                        Fazer Contraproposta
                      </span>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {budgetResponse.budget_status === 'counter_proposal' && (
                <div>
                  <label className="block text-sm font-medium mb-2">Valor da Contraproposta *</label>
                  <Input
                    value={budgetResponse.counter_proposal}
                    onChange={(e) => setBudgetResponse({...budgetResponse, counter_proposal: e.target.value})}
                    placeholder="Ex: 6500€"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium mb-2">Notas (opcional)</label>
                <Textarea
                  value={budgetResponse.admin_notes}
                  onChange={(e) => setBudgetResponse({...budgetResponse, admin_notes: e.target.value})}
                  placeholder="Adicionar uma nota ou justificação..."
                  rows={3}
                />
              </div>

              <Button 
                onClick={handleBudgetResponse}
                disabled={responding}
                className="w-full bg-secondary hover:bg-secondary/90"
              >
                {responding ? 'A enviar...' : 'Enviar Resposta'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Add Preview Dialog (Admin only) */}
      {isAdmin() && (
        <Dialog open={previewDialog} onOpenChange={setPreviewDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Eye className="w-5 h-5 text-secondary" />
                Adicionar Preview do Projeto
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleAddPreview} className="space-y-4 mt-4">
              {/* File Upload Option */}
              <div>
                <label className="block text-sm font-medium mb-2">Upload de Ficheiro (Imagem ou Vídeo)</label>
                <input
                  type="file"
                  accept="image/*,video/*"
                  onChange={handlePreviewFileSelect}
                  className="w-full border border-border rounded p-2"
                />
                {previewFile && (
                  <div className="mt-2 p-2 bg-muted rounded flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {previewFile.type.startsWith('video/') ? (
                        <File className="w-4 h-4" />
                      ) : (
                        <ImageIcon className="w-4 h-4" />
                      )}
                      <span className="text-sm">{previewFile.name}</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setPreviewFile(null)}
                      className="text-muted-foreground hover:text-destructive"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}
                <p className="text-xs text-muted-foreground mt-1">
                  Imagens: máx 50MB | Vídeos: máx 500MB
                </p>
              </div>

              {/* URL Option */}
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t border-border" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-background px-2 text-muted-foreground">Ou</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">URL da Imagem/Vídeo</label>
                <Input
                  value={newPreview.image_url}
                  onChange={(e) => setNewPreview({...newPreview, image_url: e.target.value})}
                  placeholder="https://exemplo.com/imagem.jpg"
                  disabled={!!previewFile}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Cole uma URL de imagem ou vídeo hospedado
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Descrição (opcional)</label>
                <Textarea
                  value={newPreview.description}
                  onChange={(e) => setNewPreview({...newPreview, description: e.target.value})}
                  placeholder="Descrição do preview..."
                  rows={2}
                />
              </div>

              <Button type="submit" disabled={addingPreview} className="w-full">
                {addingPreview ? 'A adicionar...' : 'Adicionar Preview'}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      )}

      {/* Payment Modal */}
      <PaymentModal
        project={project}
        isOpen={paymentModalOpen}
        onClose={() => setPaymentModalOpen(false)}
        onSuccess={() => {
          fetchProject();
          setPaymentModalOpen(false);
        }}
      />
    </div>
  );
}
