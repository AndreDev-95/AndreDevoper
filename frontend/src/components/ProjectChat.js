import { useState, useEffect, useRef } from 'react';
import { Send, MessageSquare, User, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { useAuth } from '@/context/AuthContext';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ProjectChat({ projectId, projectName }) {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const messagesEndRef = useRef(null);
  const { getAuthHeaders, user } = useAuth();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchMessages = async () => {
    try {
      const response = await axios.get(`${API}/projects/${projectId}/chat`, {
        headers: getAuthHeaders()
      });
      setMessages(response.data.messages || []);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching messages:', error);
      setLoading(false);
    }
  };

  const fetchUnreadCount = async () => {
    try {
      const response = await axios.get(`${API}/projects/${projectId}/chat/unread`, {
        headers: getAuthHeaders()
      });
      setUnreadCount(response.data.unread_count || 0);
    } catch (error) {
      console.error('Error fetching unread count:', error);
    }
  };

  useEffect(() => {
    fetchUnreadCount();
    // Poll for unread count every 30 seconds
    const interval = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(interval);
  }, [projectId]);

  useEffect(() => {
    if (isOpen) {
      fetchMessages();
      // Poll for new messages every 10 seconds when chat is open
      const interval = setInterval(fetchMessages, 10000);
      return () => clearInterval(interval);
    }
  }, [isOpen, projectId]);

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    setSending(true);
    try {
      const formData = new FormData();
      formData.append('content', newMessage.trim());
      
      await axios.post(`${API}/projects/${projectId}/chat`, formData, {
        headers: getAuthHeaders()
      });
      
      setNewMessage('');
      fetchMessages();
    } catch (error) {
      toast.error('Erro ao enviar mensagem');
    } finally {
      setSending(false);
    }
  };

  const formatTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('pt-PT', { hour: '2-digit', minute: '2-digit' });
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Hoje';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Ontem';
    }
    return date.toLocaleDateString('pt-PT', { day: 'numeric', month: 'short' });
  };

  // Group messages by date
  const groupedMessages = messages.reduce((groups, message) => {
    const date = formatDate(message.created_at);
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(message);
    return groups;
  }, {});

  return (
    <>
      {/* Chat Toggle Button */}
      <Button
        onClick={() => setIsOpen(true)}
        variant="outline"
        className="relative"
        data-testid="chat-toggle-btn"
      >
        <MessageSquare className="w-4 h-4 mr-2" />
        Chat
        {unreadCount > 0 && (
          <span className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-medium">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </Button>

      {/* Chat Modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="w-full max-w-lg bg-card rounded-2xl shadow-2xl flex flex-col max-h-[80vh]">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-primary text-white rounded-t-2xl">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-card/20 rounded-full flex items-center justify-center">
                  <MessageSquare className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold">Chat do Projeto</h3>
                  <p className="text-xs text-white/70 truncate max-w-[200px]">{projectName}</p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsOpen(false)}
                className="text-white hover:bg-card/20"
              >
                <X className="w-5 h-5" />
              </Button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-muted/30">
              {loading ? (
                <div className="flex items-center justify-center h-32">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-secondary"></div>
                </div>
              ) : messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-32 text-center">
                  <MessageSquare className="w-10 h-10 text-muted-foreground mb-2 opacity-50" />
                  <p className="text-muted-foreground text-sm">Sem mensagens ainda</p>
                  <p className="text-muted-foreground text-xs">Inicie a conversa!</p>
                </div>
              ) : (
                Object.entries(groupedMessages).map(([date, msgs]) => (
                  <div key={date}>
                    <div className="flex items-center justify-center mb-3">
                      <span className="text-xs text-muted-foreground bg-card px-3 py-1 rounded-full shadow-sm">
                        {date}
                      </span>
                    </div>
                    {msgs.map((message) => {
                      const isOwn = message.sender_id === user?.id;
                      return (
                        <div
                          key={message.id}
                          className={`flex ${isOwn ? 'justify-end' : 'justify-start'} mb-3`}
                        >
                          <div className={`flex items-end gap-2 max-w-[80%] ${isOwn ? 'flex-row-reverse' : ''}`}>
                            {!isOwn && (
                              <div className="w-8 h-8 bg-secondary rounded-full flex items-center justify-center flex-shrink-0">
                                <User className="w-4 h-4 text-white" />
                              </div>
                            )}
                            <div
                              className={`
                                px-4 py-2 rounded-2xl
                                ${isOwn 
                                  ? 'bg-primary text-white rounded-br-md' 
                                  : 'bg-card text-foreground rounded-bl-md shadow-sm'}
                              `}
                            >
                              {!isOwn && (
                                <p className="text-xs font-medium text-secondary mb-1">
                                  {message.sender_name}
                                  {message.sender_role === 'admin' && (
                                    <span className="ml-1 text-xs bg-secondary/20 text-secondary px-1.5 py-0.5 rounded text-[10px]">
                                      Admin
                                    </span>
                                  )}
                                </p>
                              )}
                              <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>
                              <p className={`text-[10px] mt-1 ${isOwn ? 'text-white/60' : 'text-muted-foreground'}`}>
                                {formatTime(message.created_at)}
                              </p>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form onSubmit={handleSendMessage} className="p-4 border-t border-border bg-card rounded-b-2xl">
              <div className="flex gap-2">
                <Textarea
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  placeholder="Escreva a sua mensagem..."
                  className="min-h-[44px] max-h-32 resize-none"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage(e);
                    }
                  }}
                  data-testid="chat-input"
                />
                <Button
                  type="submit"
                  disabled={sending || !newMessage.trim()}
                  className="bg-secondary hover:bg-secondary/90 px-4"
                  data-testid="chat-send-btn"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Pressione Enter para enviar, Shift+Enter para nova linha
              </p>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
