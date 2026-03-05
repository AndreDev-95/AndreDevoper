import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import axios from 'axios';
import usePageTitle from '@/hooks/usePageTitle';
import { ThemeToggle } from '@/components/SettingsBar';
import { 
  Monitor, 
  Smartphone, 
  Code2, 
  Rocket, 
  CheckCircle2, 
  ArrowRight,
  Menu,
  X,
  Star,
  Mail,
  Phone,
  MapPin,
  Database,
  Cloud
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Icon mapping
const iconMap = {
  Monitor: Monitor,
  Smartphone: Smartphone,
  Code2: Code2,
  Rocket: Rocket,
  Database: Database,
  Cloud: Cloud
};

// Header Component
const Header = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/20">
      <div className="max-w-7xl mx-auto px-6 lg:px-12">
        <div className="flex items-center justify-between h-16 lg:h-20">
          <Link to="/" className="flex items-center gap-2" data-testid="logo-link">
            <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
              <Code2 className="w-6 h-6 text-white" />
            </div>
            <span className="font-sans font-bold text-xl text-primary">Andre Dev</span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden lg:flex items-center gap-8">
            <a href="#servicos" className="text-foreground/80 hover:text-primary transition-colors font-medium" data-testid="nav-services">Serviços</a>
            <a href="#portfolio" className="text-foreground/80 hover:text-primary transition-colors font-medium" data-testid="nav-portfolio">Portfolio</a>
            <a href="#testemunhos" className="text-foreground/80 hover:text-primary transition-colors font-medium" data-testid="nav-testimonials">Testemunhos</a>
            <a href="#contacto" className="text-foreground/80 hover:text-primary transition-colors font-medium" data-testid="nav-contact">Contacto</a>
          </nav>

          <div className="hidden lg:flex items-center gap-4">
            <ThemeToggle />
            <Link to="/login">
              <Button variant="ghost" className="font-medium" data-testid="login-btn">
                Entrar
              </Button>
            </Link>
            <Link to="/register">
              <Button className="bg-secondary hover:bg-secondary/90 text-white rounded-none px-6 font-semibold" data-testid="register-btn">
                Área de Cliente
              </Button>
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button 
            className="lg:hidden p-2"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            data-testid="mobile-menu-btn"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="lg:hidden py-4 border-t border-border animate-fade-in">
            <nav className="flex flex-col gap-4">
              <a href="#servicos" className="text-foreground/80 hover:text-primary transition-colors font-medium py-2">Serviços</a>
              <a href="#portfolio" className="text-foreground/80 hover:text-primary transition-colors font-medium py-2">Portfolio</a>
              <a href="#testemunhos" className="text-foreground/80 hover:text-primary transition-colors font-medium py-2">Testemunhos</a>
              <a href="#contacto" className="text-foreground/80 hover:text-primary transition-colors font-medium py-2">Contacto</a>
              <div className="flex flex-col gap-2 pt-4 border-t border-border">
                <Link to="/login">
                  <Button variant="outline" className="w-full">Entrar</Button>
                </Link>
                <Link to="/register">
                  <Button className="w-full bg-secondary hover:bg-secondary/90">Área de Cliente</Button>
                </Link>
              </div>
            </nav>
          </div>
        )}
      </div>
    </header>
  );
};

// Hero Section
const HeroSection = ({ content }) => {
  const hero = content?.hero || {};
  const stats = hero.stats || [
    { value: "50+", label: "Projetos Entregues" },
    { value: "100%", label: "Clientes Satisfeitos" },
    { value: "5+", label: "Anos de Experiência" }
  ];

  return (
    <section className="min-h-screen flex items-center pt-20 lg:pt-0">
      <div className="max-w-7xl mx-auto px-6 lg:px-12 py-12 lg:py-24">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-24 items-center">
          <div className="space-y-8">
            <div className="space-y-4 opacity-0 animate-fade-up">
              <p className="text-sm font-medium tracking-wider uppercase text-secondary">
                {hero.tagline || "Agência de Desenvolvimento"}
              </p>
              <h1 className="text-3xl sm:text-5xl md:text-7xl font-bold tracking-tight leading-none text-primary">
                {hero.title || "Criamos o seu"} <span className="text-secondary">{hero.highlight || "futuro digital"}</span>
              </h1>
            </div>
            <p className="text-lg text-muted-foreground leading-relaxed max-w-lg opacity-0 animate-fade-up animation-delay-200">
              {hero.description || "Desenvolvemos websites e aplicações móveis que transformam ideias em experiências digitais extraordinárias. Android, iOS e Web."}
            </p>
            <div className="flex flex-col sm:flex-row gap-4 opacity-0 animate-fade-up animation-delay-300">
              <a href="#contacto">
                <Button 
                  className="bg-secondary text-white hover:bg-secondary/90 rounded-none px-8 py-6 text-lg font-semibold shadow-lg shadow-secondary/20 hover:translate-y-[-2px] transition-all"
                  data-testid="hero-cta-btn"
                >
                  {hero.cta_text || "Começar Projeto"}
                  <ArrowRight className="ml-2 w-5 h-5" />
                </Button>
              </a>
              <a href="#portfolio">
                <Button 
                  variant="outline" 
                  className="border-border hover:border-secondary hover:bg-secondary/5 rounded-none px-8 py-6 text-lg font-medium text-foreground"
                  data-testid="hero-portfolio-btn"
                >
                  Ver Portfolio
                </Button>
              </a>
            </div>
            <div className="flex flex-wrap items-center gap-4 sm:gap-8 pt-4 opacity-0 animate-fade-up animation-delay-400">
              {stats.map((stat, index) => (
                <div key={index} className="min-w-[80px]">
                  <p className="text-2xl sm:text-3xl font-bold text-primary">{stat.value}</p>
                  <p className="text-xs sm:text-sm text-muted-foreground">{stat.label}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="relative opacity-0 animate-fade-up animation-delay-300">
            <div className="aspect-square rounded-2xl overflow-hidden shadow-[0_8px_30px_rgb(0,0,0,0.08)]">
              <img 
                src="https://images.unsplash.com/photo-1748346918817-0b1b6b2f9bab?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjY2NzZ8MHwxfHNlYXJjaHw0fHxtb2Rlcm4lMjBkaWdpdGFsJTIwYWdlbmN5JTIwdGVhbSUyMGNvbGxhYm9yYXRpb24lMjBvZmZpY2V8ZW58MHx8fHwxNzcxNTE3NDAyfDA&ixlib=rb-4.1.0&q=85"
                alt="Team collaboration"
                className="w-full h-full object-cover"
              />
            </div>
            <div className="absolute -bottom-4 -left-4 sm:-bottom-6 sm:-left-6 bg-card p-4 sm:p-6 rounded-xl shadow-lg border border-border">
              <div className="flex items-center gap-2 sm:gap-3">
                <div className="w-10 h-10 sm:w-12 sm:h-12 bg-secondary/10 rounded-full flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5 sm:w-6 sm:h-6 text-secondary" />
                </div>
                <div>
                  <p className="font-semibold text-foreground text-sm sm:text-base">Qualidade Garantida</p>
                  <p className="text-xs sm:text-sm text-muted-foreground">Entrega no prazo</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

// Services Section
const ServicesSection = ({ content }) => {
  const services = content?.services || [];

  return (
    <section id="servicos" className="py-12 sm:py-16 md:py-24 bg-muted/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-12">
        <div className="text-center mb-8 sm:mb-12 md:mb-16">
          <p className="text-xs sm:text-sm font-medium tracking-wider uppercase text-secondary mb-2 sm:mb-4">
            Nossos Serviços
          </p>
          <h2 className="text-2xl sm:text-4xl md:text-5xl font-semibold tracking-tight text-primary">
            Soluções digitais completas para o seu negócio
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
          {services.map((service, index) => {
            const IconComponent = iconMap[service.icon] || Monitor;
            return (
              <div 
                key={index}
                className="bg-card border border-border p-5 sm:p-8 rounded-2xl hover:border-secondary/50 transition-all duration-300 hover:shadow-md group"
                data-testid={`service-card-${index}`}
              >
                <div className="w-12 h-12 sm:w-14 sm:h-14 bg-secondary/10 rounded-xl flex items-center justify-center mb-4 sm:mb-6 group-hover:bg-secondary/20 transition-colors">
                  <IconComponent className="w-6 h-6 sm:w-7 sm:h-7 text-secondary" />
                </div>
                <h3 className="text-xl sm:text-2xl font-medium text-foreground mb-2 sm:mb-3">{service.title}</h3>
                <p className="text-sm sm:text-base text-muted-foreground mb-4 sm:mb-6 leading-relaxed">{service.description}</p>
                <div className="flex flex-wrap gap-2">
                  {service.features?.map((feature, i) => (
                    <span key={i} className="text-xs sm:text-sm bg-muted px-2 sm:px-3 py-1 rounded-full text-muted-foreground">
                      {feature}
                    </span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

// Portfolio Section
const PortfolioSection = ({ content }) => {
  const projects = content?.portfolio || [];

  return (
    <section id="portfolio" className="py-12 sm:py-16 md:py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-12">
        <div className="text-center mb-8 sm:mb-12 md:mb-16">
          <p className="text-xs sm:text-sm font-medium tracking-wider uppercase text-secondary mb-2 sm:mb-4">
            Portfolio
          </p>
          <h2 className="text-2xl sm:text-4xl md:text-5xl font-semibold tracking-tight text-primary">
            Alguns dos nossos trabalhos recentes
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
          {projects.map((project, index) => (
            <div 
              key={index}
              className="group relative overflow-hidden rounded-2xl bg-card border border-border hover:border-secondary/50 transition-all duration-300"
              data-testid={`portfolio-item-${index}`}
            >
              <div className="aspect-video overflow-hidden">
                <img 
                  src={project.image_url}
                  alt={project.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                />
              </div>
              <div className="p-4 sm:p-6">
                <span className="text-xs sm:text-sm text-secondary font-medium">{project.category}</span>
                <h3 className="text-lg sm:text-xl font-medium text-foreground mt-1 sm:mt-2">{project.title}</h3>
                <p className="text-sm text-muted-foreground mt-1">{project.description}</p>
                <div className="flex flex-wrap gap-1.5 sm:gap-2 mt-3 sm:mt-4">
                  {project.technologies?.map((tech, i) => (
                    <span key={i} className="text-xs bg-muted px-2 py-1 rounded text-muted-foreground">
                      {tech}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

// Testimonials Section
const TestimonialsSection = ({ content }) => {
  const testimonials = content?.testimonials || [];

  return (
    <section id="testemunhos" className="py-12 sm:py-16 md:py-24 bg-primary">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-12">
        <div className="text-center mb-8 sm:mb-12 md:mb-16">
          <p className="text-xs sm:text-sm font-medium tracking-wider uppercase text-secondary mb-2 sm:mb-4">
            O que dizem os nossos clientes
          </p>
          <h2 className="text-2xl sm:text-4xl md:text-5xl font-semibold tracking-tight text-white">
            Feedback de quem confia no nosso trabalho
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 md:gap-8">
          {testimonials.map((testimonial, index) => (
            <div 
              key={index}
              className="bg-white/10 backdrop-blur-sm p-5 sm:p-8 rounded-2xl border border-white/10"
              data-testid={`testimonial-${index}`}
            >
              <div className="flex gap-1 mb-4 sm:mb-6">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-4 h-4 sm:w-5 sm:h-5 fill-secondary text-secondary" />
                ))}
              </div>
              <p className="text-white/90 text-base sm:text-lg leading-relaxed mb-4 sm:mb-6">
                "{testimonial.text}"
              </p>
              <div className="flex items-center gap-3 sm:gap-4">
                <img 
                  src={testimonial.image}
                  alt={testimonial.name}
                  className="w-10 h-10 sm:w-12 sm:h-12 rounded-full object-cover"
                />
                <div>
                  <p className="font-semibold text-white text-sm sm:text-base">{testimonial.name}</p>
                  <p className="text-white/60 text-xs sm:text-sm">{testimonial.role}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

// Contact Section
const ContactSection = ({ content }) => {
  const contactInfo = content?.contact_info || {};
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    message: '',
    service_type: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(`${API}/contact`, formData);
      toast.success('Mensagem enviada com sucesso!');
      setFormData({ name: '', email: '', phone: '', message: '', service_type: '' });
    } catch (error) {
      toast.error('Erro ao enviar mensagem');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="contacto" className="py-12 sm:py-16 md:py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-12">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-24">
          <div>
            <p className="text-xs sm:text-sm font-medium tracking-wider uppercase text-secondary mb-2 sm:mb-4">
              Entre em Contacto
            </p>
            <h2 className="text-2xl sm:text-4xl md:text-5xl font-semibold tracking-tight text-foreground mb-4 sm:mb-6">
              Estamos prontos para transformar a sua ideia em realidade
            </h2>
            <p className="text-muted-foreground text-base sm:text-lg leading-relaxed mb-6 sm:mb-8">
              Tem um projeto em mente? Entre em contacto connosco e vamos discutir como podemos ajudar a transformar a sua ideia em realidade.
            </p>

            <div className="space-y-4 sm:space-y-6">
              <div className="flex items-center gap-3 sm:gap-4">
                <div className="w-10 h-10 sm:w-12 sm:h-12 bg-secondary/10 rounded-xl flex items-center justify-center flex-shrink-0">
                  <Mail className="w-4 h-4 sm:w-5 sm:h-5 text-secondary" />
                </div>
                <div className="min-w-0">
                  <p className="text-xs sm:text-sm text-muted-foreground">Email</p>
                  <p className="font-medium text-foreground text-sm sm:text-base truncate">{contactInfo.email || "contacto@andredev.pt"}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 sm:gap-4">
                <div className="w-10 h-10 sm:w-12 sm:h-12 bg-secondary/10 rounded-xl flex items-center justify-center flex-shrink-0">
                  <Phone className="w-4 h-4 sm:w-5 sm:h-5 text-secondary" />
                </div>
                <div className="min-w-0">
                  <p className="text-xs sm:text-sm text-muted-foreground">Telefone</p>
                  <p className="font-medium text-foreground text-sm sm:text-base">{contactInfo.phone || "+351 912 345 678"}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 sm:gap-4">
                <div className="w-10 h-10 sm:w-12 sm:h-12 bg-secondary/10 rounded-xl flex items-center justify-center flex-shrink-0">
                  <MapPin className="w-4 h-4 sm:w-5 sm:h-5 text-secondary" />
                </div>
                <div className="min-w-0">
                  <p className="text-xs sm:text-sm text-muted-foreground">Localização</p>
                  <p className="font-medium text-foreground text-sm sm:text-base">{contactInfo.location || "Lisboa, Portugal"}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-card border border-border p-5 sm:p-8 rounded-2xl shadow-sm">
            <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">Nome</label>
                <Input 
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="O seu nome"
                  required
                  data-testid="contact-name-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">Email</label>
                <Input 
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  placeholder="email@exemplo.com"
                  required
                  data-testid="contact-email-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">Telefone</label>
                <Input 
                  value={formData.phone}
                  onChange={(e) => setFormData({...formData, phone: e.target.value})}
                  placeholder="+351 912 345 678"
                  data-testid="contact-phone-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">Mensagem</label>
                <Textarea 
                  value={formData.message}
                  onChange={(e) => setFormData({...formData, message: e.target.value})}
                  placeholder="Descreva o seu projeto..."
                  rows={4}
                  required
                  data-testid="contact-message-input"
                />
              </div>
              <Button 
                type="submit" 
                disabled={loading}
                className="w-full bg-secondary text-white hover:bg-secondary/90 rounded-none py-6 font-semibold"
                data-testid="contact-submit-btn"
              >
                {loading ? 'A enviar...' : 'Enviar Mensagem'}
              </Button>
            </form>
          </div>
        </div>
      </div>
    </section>
  );
};

// Footer
const Footer = () => {
  return (
    <footer className="bg-primary py-8 sm:py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-12">
        <div className="flex flex-col items-center gap-4 sm:gap-6 md:flex-row md:justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 sm:w-10 sm:h-10 bg-white rounded-lg flex items-center justify-center">
              <Code2 className="w-5 h-5 sm:w-6 sm:h-6 text-primary" />
            </div>
            <span className="font-sans font-bold text-lg sm:text-xl text-white">Andre Dev</span>
          </div>
          <p className="text-white/60 text-xs sm:text-sm text-center">
            © 2024 Andre Dev. Todos os direitos reservados.
          </p>
          <div className="flex gap-4 sm:gap-6">
            <a href="#servicos" className="text-white/60 hover:text-white transition-colors text-xs sm:text-sm">Serviços</a>
            <a href="#portfolio" className="text-white/60 hover:text-white transition-colors text-xs sm:text-sm">Portfolio</a>
            <a href="#contacto" className="text-white/60 hover:text-white transition-colors text-xs sm:text-sm">Contacto</a>
          </div>
        </div>
      </div>
    </footer>
  );
};

// Main Landing Page
export default function LandingPage() {
  usePageTitle('Início');
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchContent = async () => {
      try {
        const response = await axios.get(`${API}/content`);
        setContent(response.data);
      } catch (error) {
        console.error('Error fetching content:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchContent();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-secondary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" data-testid="landing-page">
      <Header />
      <HeroSection content={content} />
      <ServicesSection content={content} />
      <PortfolioSection content={content} />
      <TestimonialsSection content={content} />
      <ContactSection content={content} />
      <Footer />
    </div>
  );
}
