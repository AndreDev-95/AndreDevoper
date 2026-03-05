import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { toast } from 'sonner';
import { useAuth } from '@/context/AuthContext';
import axios from 'axios';
import { 
  Save, 
  Plus, 
  Trash2, 
  FileText,
  Briefcase,
  Image,
  MessageSquare,
  Phone,
  Loader2,
  Mail,
  RotateCcw
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ContentEditor() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [content, setContent] = useState(null);
  const [emailTemplates, setEmailTemplates] = useState([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const { getAuthHeaders } = useAuth();

  useEffect(() => {
    fetchContent();
    fetchEmailTemplates();
  }, []);

  const fetchEmailTemplates = async () => {
    setLoadingTemplates(true);
    try {
      const response = await axios.get(`${API}/admin/email-templates`, {
        headers: getAuthHeaders()
      });
      setEmailTemplates(response.data.templates || []);
    } catch (error) {
      console.error('Error fetching email templates:', error);
    } finally {
      setLoadingTemplates(false);
    }
  };

  const fetchContent = async () => {
    try {
      const response = await axios.get(`${API}/admin/content`, {
        headers: getAuthHeaders()
      });
      setContent(response.data);
    } catch (error) {
      console.error('Error fetching content:', error);
      toast.error('Erro ao carregar conteúdo');
    } finally {
      setLoading(false);
    }
  };

  const saveHero = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/admin/content/hero`, content.hero, {
        headers: getAuthHeaders()
      });
      toast.success('Hero atualizado com sucesso!');
    } catch (error) {
      toast.error('Erro ao guardar hero');
    } finally {
      setSaving(false);
    }
  };

  const autoTranslateAndSave = async (contentType, contentData) => {
    setTranslating(true);
    try {
      // Auto-traduzir o conteúdo
      const translateResponse = await axios.post(
        `${API}/cms/auto-translate`,
        {
          content_type: contentType,
          content: contentData,
          target_languages: ['en', 'es', 'fr']
        },
        { headers: getAuthHeaders() }
      );

      if (translateResponse.data.success) {
        // Salvar conteúdo multi-idioma
        const translations = {
          pt: contentData,
          ...translateResponse.data.translations
        };

        await axios.post(
          `${API}/cms/save-multilang`,
          {
            content_type: contentType,
            ...translations
          },
          { headers: getAuthHeaders() }
        );

        toast.success('Conteúdo guardado com sucesso!');
      }
    } catch (error) {
      console.error('Translation error:', error);
      toast.error('Erro ao traduzir');
      // Fallback: salvar apenas em português
      try {
        await axios.put(`${API}/admin/content/${contentType}`, contentData, {
          headers: getAuthHeaders()
        });
        toast.success('Guardado em português');
      } catch (saveError) {
        toast.error('Erro ao guardar');
      }
    } finally {
      // removed;
    }
  };

  const saveServices = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/admin/content/services`, content.services, {
        headers: getAuthHeaders()
      });
      toast.success('Serviços atualizados com sucesso!');
    } catch (error) {
      toast.error('Erro ao guardar serviços');
    } finally {
      setSaving(false);
    }
  };

  const savePortfolio = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/admin/content/portfolio`, content.portfolio, {
        headers: getAuthHeaders()
      });
      toast.success('Portfolio atualizado com sucesso!');
    } catch (error) {
      toast.error('Erro ao guardar portfolio');
    } finally {
      setSaving(false);
    }
  };

  const saveTestimonials = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/admin/content/testimonials`, content.testimonials, {
        headers: getAuthHeaders()
      });
      toast.success('Testemunhos atualizados com sucesso!');
    } catch (error) {
      toast.error('Erro ao guardar testemunhos');
    } finally {
      setSaving(false);
    }
  };

  const saveContactInfo = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/admin/content/contact-info`, content.contact_info, {
        headers: getAuthHeaders()
      });
      toast.success('Informação de contacto atualizada!');
    } catch (error) {
      toast.error('Erro ao guardar contacto');
    } finally {
      setSaving(false);
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
    <div data-testid="content-editor-page">
      <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-primary mb-4 sm:mb-6 md:mb-8">
        Editar Conteúdo do Site
      </h1>

      <Tabs defaultValue="hero" className="w-full">
        <TabsList className="grid grid-cols-3 sm:grid-cols-6 gap-2 mb-6 h-auto p-1 bg-muted">
          <TabsTrigger value="hero" className="flex items-center gap-2 text-xs sm:text-sm py-2">
            <FileText className="w-4 h-4" />
            <span className="hidden sm:inline">Hero</span>
          </TabsTrigger>
          <TabsTrigger value="services" className="flex items-center gap-2 text-xs sm:text-sm py-2">
            <Briefcase className="w-4 h-4" />
            <span className="hidden sm:inline">Serviços</span>
          </TabsTrigger>
          <TabsTrigger value="portfolio" className="flex items-center gap-2 text-xs sm:text-sm py-2">
            <Image className="w-4 h-4" />
            <span className="hidden sm:inline">Portfolio</span>
          </TabsTrigger>
          <TabsTrigger value="testimonials" className="flex items-center gap-2 text-xs sm:text-sm py-2">
            <MessageSquare className="w-4 h-4" />
            <span className="hidden sm:inline">Testemunhos</span>
          </TabsTrigger>
          <TabsTrigger value="contact" className="flex items-center gap-2 text-xs sm:text-sm py-2">
            <Phone className="w-4 h-4" />
            <span className="hidden sm:inline">Contacto</span>
          </TabsTrigger>
          <TabsTrigger value="emails" className="flex items-center gap-2 text-xs sm:text-sm py-2">
            <Mail className="w-4 h-4" />
            <span className="hidden sm:inline">Emails</span>
          </TabsTrigger>
        </TabsList>

        {/* Hero Section Editor */}
        <TabsContent value="hero">
          <div className="bg-white border border-border p-4 sm:p-6 rounded-xl shadow-sm space-y-4">
            <h2 className="text-lg font-semibold text-primary mb-4">Secção Hero</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Tagline</label>
                <Input 
                  value={content.hero.tagline}
                  onChange={(e) => setContent({
                    ...content,
                    hero: { ...content.hero, tagline: e.target.value }
                  })}
                  placeholder="Ex: Agência de Desenvolvimento"
                  data-testid="hero-tagline-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Título</label>
                <Input 
                  value={content.hero.title}
                  onChange={(e) => setContent({
                    ...content,
                    hero: { ...content.hero, title: e.target.value }
                  })}
                  placeholder="Ex: Criamos o seu"
                  data-testid="hero-title-input"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Texto Destacado (colorido)</label>
              <Input 
                value={content.hero.highlight}
                onChange={(e) => setContent({
                  ...content,
                  hero: { ...content.hero, highlight: e.target.value }
                })}
                placeholder="Ex: futuro digital"
                data-testid="hero-highlight-input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Descrição</label>
              <Textarea 
                value={content.hero.description}
                onChange={(e) => setContent({
                  ...content,
                  hero: { ...content.hero, description: e.target.value }
                })}
                placeholder="Descrição do hero..."
                rows={3}
                data-testid="hero-description-input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Texto do Botão CTA</label>
              <Input 
                value={content.hero.cta_text}
                onChange={(e) => setContent({
                  ...content,
                  hero: { ...content.hero, cta_text: e.target.value }
                })}
                placeholder="Ex: Começar Projeto"
                data-testid="hero-cta-input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Estatísticas</label>
              <div className="space-y-2">
                {content.hero.stats?.map((stat, index) => (
                  <div key={index} className="flex gap-2 items-center">
                    <Input 
                      value={stat.value}
                      onChange={(e) => {
                        const newStats = [...content.hero.stats];
                        newStats[index].value = e.target.value;
                        setContent({
                          ...content,
                          hero: { ...content.hero, stats: newStats }
                        });
                      }}
                      placeholder="Valor (ex: 50+)"
                      className="w-24"
                    />
                    <Input 
                      value={stat.label}
                      onChange={(e) => {
                        const newStats = [...content.hero.stats];
                        newStats[index].label = e.target.value;
                        setContent({
                          ...content,
                          hero: { ...content.hero, stats: newStats }
                        });
                      }}
                      placeholder="Label"
                      className="flex-1"
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        const newStats = content.hero.stats.filter((_, i) => i !== index);
                        setContent({
                          ...content,
                          hero: { ...content.hero, stats: newStats }
                        });
                      }}
                      className="text-destructive"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const newStats = [...(content.hero.stats || []), { value: "", label: "" }];
                    setContent({
                      ...content,
                      hero: { ...content.hero, stats: newStats }
                    });
                  }}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Adicionar Estatística
                </Button>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <Button 
                onClick={saveHero} 
                disabled={saving || false}
                className="w-full sm:w-auto bg-secondary hover:bg-secondary/90"
                data-testid="save-hero-btn"
              >
                {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                {'Guardar'}
              </Button>
              <Button 
                onClick={() => autoTranslateAndSave('hero', content.hero)} 
                disabled={saving || false}
                variant="outline"
                className="w-full sm:w-auto border-blue-500 text-blue-600 hover:bg-blue-50"
                data-testid="auto-translate-hero-btn"
              >
                {false ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Languages className="w-4 h-4 mr-2" />}
                {'Traduzir Automático'}
              </Button>
            </div>
          </div>
        </TabsContent>

        {/* Services Editor */}
        <TabsContent value="services">
          <div className="bg-white border border-border p-4 sm:p-6 rounded-xl shadow-sm space-y-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-primary">Serviços</h2>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  const newServices = [...content.services, {
                    id: String(content.services.length + 1),
                    icon: "Monitor",
                    title: "",
                    description: "",
                    features: []
                  }];
                  setContent({ ...content, services: newServices });
                }}
              >
                <Plus className="w-4 h-4 mr-2" />
                Adicionar
              </Button>
            </div>

            <div className="space-y-6">
              {content.services.map((service, index) => (
                <div key={index} className="border border-border p-4 rounded-lg space-y-3">
                  <div className="flex justify-between items-start">
                    <span className="text-sm font-medium text-muted-foreground">Serviço {index + 1}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        const newServices = content.services.filter((_, i) => i !== index);
                        setContent({ ...content, services: newServices });
                      }}
                      className="text-destructive"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm font-medium mb-1">Ícone</label>
                      <Select 
                        value={service.icon}
                        onValueChange={(value) => {
                          const newServices = [...content.services];
                          newServices[index].icon = value;
                          setContent({ ...content, services: newServices });
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Monitor">Monitor (Web)</SelectItem>
                          <SelectItem value="Smartphone">Smartphone (Mobile)</SelectItem>
                          <SelectItem value="Code2">Code (iOS)</SelectItem>
                          <SelectItem value="Rocket">Rocket (Soluções)</SelectItem>
                          <SelectItem value="Database">Database</SelectItem>
                          <SelectItem value="Cloud">Cloud</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Título</label>
                      <Input 
                        value={service.title}
                        onChange={(e) => {
                          const newServices = [...content.services];
                          newServices[index].title = e.target.value;
                          setContent({ ...content, services: newServices });
                        }}
                        placeholder="Título do serviço"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Descrição</label>
                    <Textarea 
                      value={service.description}
                      onChange={(e) => {
                        const newServices = [...content.services];
                        newServices[index].description = e.target.value;
                        setContent({ ...content, services: newServices });
                      }}
                      placeholder="Descrição do serviço..."
                      rows={2}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Funcionalidades (separadas por vírgula)</label>
                    <Input 
                      value={service.features?.join(", ") || ""}
                      onChange={(e) => {
                        const newServices = [...content.services];
                        newServices[index].features = e.target.value.split(",").map(f => f.trim()).filter(f => f);
                        setContent({ ...content, services: newServices });
                      }}
                      placeholder="Ex: React, Node.js, MongoDB"
                    />
                  </div>
                </div>
              ))}
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <Button 
                onClick={saveServices} 
                disabled={saving || false}
                className="w-full sm:w-auto bg-secondary hover:bg-secondary/90"
                data-testid="save-services-btn"
              >
                {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                {'Guardar'}
              </Button>
              <Button 
                onClick={() => autoTranslateAndSave('services', content.services)} 
                disabled={saving || false}
                variant="outline"
                className="w-full sm:w-auto border-blue-500 text-blue-600 hover:bg-blue-50"
                data-testid="auto-translate-services-btn"
              >
                {false ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Languages className="w-4 h-4 mr-2" />}
                {'Traduzir Automático'}
              </Button>
            </div>
          </div>
        </TabsContent>

        {/* Portfolio Editor */}
        <TabsContent value="portfolio">
          <div className="bg-white border border-border p-4 sm:p-6 rounded-xl shadow-sm space-y-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-primary">Portfolio</h2>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  const newPortfolio = [...content.portfolio, {
                    id: String(content.portfolio.length + 1),
                    title: "",
                    description: "",
                    image_url: "",
                    category: "Web",
                    technologies: [],
                    link: null
                  }];
                  setContent({ ...content, portfolio: newPortfolio });
                }}
              >
                <Plus className="w-4 h-4 mr-2" />
                Adicionar
              </Button>
            </div>

            <div className="space-y-6">
              {content.portfolio.map((item, index) => (
                <div key={index} className="border border-border p-4 rounded-lg space-y-3">
                  <div className="flex justify-between items-start">
                    <span className="text-sm font-medium text-muted-foreground">Projeto {index + 1}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        const newPortfolio = content.portfolio.filter((_, i) => i !== index);
                        setContent({ ...content, portfolio: newPortfolio });
                      }}
                      className="text-destructive"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm font-medium mb-1">Título</label>
                      <Input 
                        value={item.title}
                        onChange={(e) => {
                          const newPortfolio = [...content.portfolio];
                          newPortfolio[index].title = e.target.value;
                          setContent({ ...content, portfolio: newPortfolio });
                        }}
                        placeholder="Nome do projeto"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Categoria</label>
                      <Select 
                        value={item.category}
                        onValueChange={(value) => {
                          const newPortfolio = [...content.portfolio];
                          newPortfolio[index].category = value;
                          setContent({ ...content, portfolio: newPortfolio });
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Web">Web</SelectItem>
                          <SelectItem value="Mobile">Mobile</SelectItem>
                          <SelectItem value="Desktop">Desktop</SelectItem>
                          <SelectItem value="API">API</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Descrição</label>
                    <Input 
                      value={item.description}
                      onChange={(e) => {
                        const newPortfolio = [...content.portfolio];
                        newPortfolio[index].description = e.target.value;
                        setContent({ ...content, portfolio: newPortfolio });
                      }}
                      placeholder="Breve descrição do projeto"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">URL da Imagem</label>
                    <Input 
                      value={item.image_url}
                      onChange={(e) => {
                        const newPortfolio = [...content.portfolio];
                        newPortfolio[index].image_url = e.target.value;
                        setContent({ ...content, portfolio: newPortfolio });
                      }}
                      placeholder="https://..."
                    />
                    {item.image_url && (
                      <img src={item.image_url} alt="Preview" className="mt-2 w-32 h-20 object-cover rounded" />
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Tecnologias (separadas por vírgula)</label>
                    <Input 
                      value={item.technologies?.join(", ") || ""}
                      onChange={(e) => {
                        const newPortfolio = [...content.portfolio];
                        newPortfolio[index].technologies = e.target.value.split(",").map(t => t.trim()).filter(t => t);
                        setContent({ ...content, portfolio: newPortfolio });
                      }}
                      placeholder="Ex: React, Node.js, MongoDB"
                    />
                  </div>
                </div>
              ))}
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <Button 
                onClick={savePortfolio} 
                disabled={saving || false}
                className="w-full sm:w-auto bg-secondary hover:bg-secondary/90"
                data-testid="save-portfolio-btn"
              >
                {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                {'Guardar'}
              </Button>
              <Button 
                onClick={() => autoTranslateAndSave('portfolio', content.portfolio)} 
                disabled={saving || false}
                variant="outline"
                className="w-full sm:w-auto border-blue-500 text-blue-600 hover:bg-blue-50"
                data-testid="auto-translate-portfolio-btn"
              >
                {false ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Languages className="w-4 h-4 mr-2" />}
                {'Traduzir Automático'}
              </Button>
            </div>
          </div>
        </TabsContent>

        {/* Testimonials Editor */}
        <TabsContent value="testimonials">
          <div className="bg-white border border-border p-4 sm:p-6 rounded-xl shadow-sm space-y-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-primary">Testemunhos</h2>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  const newTestimonials = [...content.testimonials, {
                    id: String(content.testimonials.length + 1),
                    name: "",
                    role: "",
                    image: "",
                    text: ""
                  }];
                  setContent({ ...content, testimonials: newTestimonials });
                }}
              >
                <Plus className="w-4 h-4 mr-2" />
                Adicionar
              </Button>
            </div>

            <div className="space-y-6">
              {content.testimonials.map((item, index) => (
                <div key={index} className="border border-border p-4 rounded-lg space-y-3">
                  <div className="flex justify-between items-start">
                    <span className="text-sm font-medium text-muted-foreground">Testemunho {index + 1}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        const newTestimonials = content.testimonials.filter((_, i) => i !== index);
                        setContent({ ...content, testimonials: newTestimonials });
                      }}
                      className="text-destructive"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm font-medium mb-1">Nome</label>
                      <Input 
                        value={item.name}
                        onChange={(e) => {
                          const newTestimonials = [...content.testimonials];
                          newTestimonials[index].name = e.target.value;
                          setContent({ ...content, testimonials: newTestimonials });
                        }}
                        placeholder="Nome do cliente"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Cargo/Empresa</label>
                      <Input 
                        value={item.role}
                        onChange={(e) => {
                          const newTestimonials = [...content.testimonials];
                          newTestimonials[index].role = e.target.value;
                          setContent({ ...content, testimonials: newTestimonials });
                        }}
                        placeholder="Ex: CEO, TechStart"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">URL da Foto</label>
                    <Input 
                      value={item.image}
                      onChange={(e) => {
                        const newTestimonials = [...content.testimonials];
                        newTestimonials[index].image = e.target.value;
                        setContent({ ...content, testimonials: newTestimonials });
                      }}
                      placeholder="https://..."
                    />
                    {item.image && (
                      <img src={item.image} alt="Preview" className="mt-2 w-12 h-12 object-cover rounded-full" />
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Testemunho</label>
                    <Textarea 
                      value={item.text}
                      onChange={(e) => {
                        const newTestimonials = [...content.testimonials];
                        newTestimonials[index].text = e.target.value;
                        setContent({ ...content, testimonials: newTestimonials });
                      }}
                      placeholder="O que o cliente disse..."
                      rows={3}
                    />
                  </div>
                </div>
              ))}
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <Button 
                onClick={saveTestimonials} 
                disabled={saving || false}
                className="w-full sm:w-auto bg-secondary hover:bg-secondary/90"
                data-testid="save-testimonials-btn"
              >
                {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                {'Guardar'}
              </Button>
              <Button 
                onClick={() => autoTranslateAndSave('testimonials', content.testimonials)} 
                disabled={saving || false}
                variant="outline"
                className="w-full sm:w-auto border-blue-500 text-blue-600 hover:bg-blue-50"
                data-testid="auto-translate-testimonials-btn"
              >
                {false ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Languages className="w-4 h-4 mr-2" />}
                {'Traduzir Automático'}
              </Button>
            </div>
          </div>
        </TabsContent>

        {/* Contact Info Editor */}
        <TabsContent value="contact">
          <div className="bg-white border border-border p-4 sm:p-6 rounded-xl shadow-sm space-y-4">
            <h2 className="text-lg font-semibold text-primary mb-4">Informação de Contacto</h2>

            <div>
              <label className="block text-sm font-medium mb-2">Email</label>
              <Input 
                value={content.contact_info.email}
                onChange={(e) => setContent({
                  ...content,
                  contact_info: { ...content.contact_info, email: e.target.value }
                })}
                placeholder="email@exemplo.com"
                data-testid="contact-email-input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Telefone</label>
              <Input 
                value={content.contact_info.phone}
                onChange={(e) => setContent({
                  ...content,
                  contact_info: { ...content.contact_info, phone: e.target.value }
                })}
                placeholder="+351 000 000 000"
                data-testid="contact-phone-input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Localização</label>
              <Input 
                value={content.contact_info.location}
                onChange={(e) => setContent({
                  ...content,
                  contact_info: { ...content.contact_info, location: e.target.value }
                })}
                placeholder="Cidade, País"
                data-testid="contact-location-input"
              />
            </div>

            <Button 
              onClick={saveContactInfo} 
              disabled={saving || false}
              className="w-full sm:w-auto bg-secondary hover:bg-secondary/90"
              data-testid="save-contact-btn"
            >
              {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
              {'Guardar'}
            </Button>
          </div>
        </TabsContent>

        {/* Email Templates Tab */}
        <TabsContent value="emails" className="bg-white border border-border rounded-xl p-4 sm:p-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
            <div>
              <h2 className="text-lg font-semibold text-primary">Templates de Email</h2>
              <p className="text-sm text-muted-foreground">
                Personalize os emails enviados aos clientes. Use variáveis como: {"{{nome}}"}, {"{{projeto}}"}, {"{{email}}"}
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={async () => {
                if (window.confirm('Restaurar todos os templates para os valores padrão?')) {
                  try {
                    await axios.post(`${API}/admin/email-templates/reset`, {}, {
                      headers: getAuthHeaders()
                    });
                    toast.success('Templates restaurados');
                    fetchEmailTemplates();
                  } catch (error) {
                    toast.error('Erro ao restaurar templates');
                  }
                }
              }}
              data-testid="reset-templates-btn"
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              Restaurar Padrão
            </Button>
          </div>

          {loadingTemplates ? (
            <div className="flex items-center justify-center h-32">
              <Loader2 className="w-8 h-8 animate-spin text-secondary" />
            </div>
          ) : (
            <div className="space-y-6">
              {emailTemplates.map((template, index) => (
                <div key={template.template_id} className="border border-border rounded-lg p-4">
                  <h3 className="font-medium text-primary mb-4 flex items-center gap-2">
                    <Mail className="w-4 h-4 text-secondary" />
                    {template.name}
                  </h3>
                  
                  <div className="grid gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">Assunto do Email</label>
                      <Input
                        value={template.subject}
                        onChange={(e) => {
                          const updated = [...emailTemplates];
                          updated[index] = { ...updated[index], subject: e.target.value };
                          setEmailTemplates(updated);
                        }}
                        placeholder="Assunto do email"
                        data-testid={`email-subject-${template.template_id}`}
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium mb-2">Título no Email</label>
                      <Input
                        value={template.title}
                        onChange={(e) => {
                          const updated = [...emailTemplates];
                          updated[index] = { ...updated[index], title: e.target.value };
                          setEmailTemplates(updated);
                        }}
                        placeholder="Título que aparece no corpo do email"
                        data-testid={`email-title-${template.template_id}`}
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Conteúdo (HTML)
                        <span className="text-xs text-muted-foreground ml-2">
                          Variáveis disponíveis variam por template
                        </span>
                      </label>
                      <Textarea
                        value={template.content}
                        onChange={(e) => {
                          const updated = [...emailTemplates];
                          updated[index] = { ...updated[index], content: e.target.value };
                          setEmailTemplates(updated);
                        }}
                        rows={8}
                        className="font-mono text-sm"
                        placeholder="Conteúdo HTML do email"
                        data-testid={`email-content-${template.template_id}`}
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        {template.template_id === 'password_reset' && 'Variáveis: {{nome}}'}
                        {template.template_id === 'new_project' && 'Variáveis: {{cliente}}, {{email_cliente}}, {{projeto}}, {{tipo}}, {{orcamento}}, {{descricao}}'}
                        {template.template_id === 'status_change' && 'Variáveis: {{nome}}, {{projeto}}, {{estado}}, {{cor_estado}}'}
                        {template.template_id === 'budget_accepted' && 'Variáveis: {{nome}}, {{projeto}}, {{valor}}, {{notas}}'}
                        {template.template_id === 'budget_counter' && 'Variáveis: {{nome}}, {{projeto}}, {{orcamento_original}}, {{contraproposta}}, {{notas}}'}
                        {template.template_id === 'welcome_client' && 'Variáveis: {{nome}}, {{email}}, {{password}}'}
                      </p>
                    </div>
                  </div>
                </div>
              ))}

              <Button 
                onClick={async () => {
                  setSaving(true);
                  try {
                    await axios.put(`${API}/admin/email-templates`, 
                      { templates: emailTemplates },
                      { headers: getAuthHeaders() }
                    );
                    toast.success('Templates de email guardados!');
                  } catch (error) {
                    toast.error('Erro ao guardar templates');
                  } finally {
                    setSaving(false);
                  }
                }} 
                disabled={saving}
                className="w-full sm:w-auto bg-secondary hover:bg-secondary/90"
                data-testid="save-email-templates-btn"
              >
                {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                Guardar Templates
              </Button>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
