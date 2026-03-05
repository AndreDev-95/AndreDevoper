from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
import json
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import base64
import aiofiles
import resend
import stripe
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Table, TableStyle
# Security imports
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import pyotp
import qrcode

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Resend Configuration
resend.api_key = os.environ.get('RESEND_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'no-reply@andredev.pt')

# Stripe Configuration
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Create uploads directory
UPLOADS_DIR = ROOT_DIR / 'uploads'
UPLOADS_DIR.mkdir(exist_ok=True)
(UPLOADS_DIR / 'previews').mkdir(exist_ok=True)
(UPLOADS_DIR / 'files').mkdir(exist_ok=True)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']

# Only use TLS/SSL for remote MongoDB (Atlas), not for localhost
if 'localhost' in mongo_url or '127.0.0.1' in mongo_url:
    client = AsyncIOMotorClient(
        mongo_url,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000
    )
else:
    import certifi
    client = AsyncIOMotorClient(
        mongo_url,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000
    )
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'andre-dev-secret-key-2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# ==================== RATE LIMITER ====================
def get_real_ip(request: Request) -> str:
    """Get real IP address from X-Forwarded-For or X-Real-IP header"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return get_remote_address(request)

limiter = Limiter(key_func=get_real_ip)

# ==================== AUDIT LOGGER ====================
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# Create audit log file handler
audit_handler = logging.FileHandler('/var/log/supervisor/audit.log')
audit_handler.setFormatter(logging.Formatter(
    '%(asctime)s | %(levelname)s | %(message)s'
))
audit_logger.addHandler(audit_handler)

async def log_audit(action: str, user_id: str = None, user_email: str = None, 
                    ip_address: str = None, details: dict = None, status: str = "success"):
    """Log security-relevant actions for audit trail"""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "user_id": user_id,
        "user_email": user_email,
        "ip_address": ip_address,
        "status": status,
        "details": details or {}
    }
    
    # Log to file
    audit_logger.info(json.dumps(log_entry))
    
    # Store in database for querying
    try:
        await db.audit_logs.insert_one(log_entry)
    except Exception as e:
        logger.error(f"Failed to store audit log: {e}")

# Create the main app
app = FastAPI(title="Andre Dev API")

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Mount static files for uploads under /api/uploads so it routes through Kubernetes ingress
app.mount("/api/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Create router with /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== MODELS ====================

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    company: Optional[str] = None

class AdminCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    email: str
    company: Optional[str] = None
    role: str = "client"  # client, admin
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class ProjectCreate(BaseModel):
    name: str
    description: str
    project_type: str  # web, android, ios
    status: str = "pending"  # pending, in_progress, completed
    budget: str  # Now required

class ProjectResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    name: str
    description: str
    project_type: str
    status: str
    budget: str
    budget_status: str = "pending"  # pending, accepted, counter_proposal
    counter_proposal: Optional[str] = None
    admin_notes: Optional[str] = None
    official_value: Optional[str] = None  # Set when budget is accepted
    created_at: str
    updated_at: str

class ProjectMessage(BaseModel):
    content: str
    attachment: Optional[dict] = None  # {filename, file_data (base64)}

class ProjectMessageUpdate(BaseModel):
    content: str

class ProjectFile(BaseModel):
    filename: str
    file_data: str  # base64 encoded file
    
class ProjectFileUpload(BaseModel):
    filename: str
    file_url: Optional[str] = None
    file_data: Optional[str] = None  # base64
    
class ProjectPreview(BaseModel):
    image_url: Optional[str] = None
    image_data: Optional[str] = None  # base64
    mime_type: Optional[str] = None
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[str] = None

class BudgetResponse(BaseModel):
    budget_status: str  # accepted, counter_proposal
    counter_proposal: Optional[str] = None
    admin_notes: Optional[str] = None

class MessageCreate(BaseModel):
    subject: str
    content: str

class MessageResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    subject: str
    content: str
    is_read: bool
    admin_reply: Optional[str] = None
    created_at: str

class ContactCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    message: str
    service_type: Optional[str] = None

class ContactResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    message: str
    service_type: Optional[str] = None
    created_at: str

class PortfolioItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    title: str
    description: str
    image_url: str
    category: str
    technologies: List[str]
    link: Optional[str] = None

# ==================== CMS MODELS ====================

class HeroContent(BaseModel):
    tagline: str = "Agência de Desenvolvimento"
    title: str = "Criamos o seu"
    highlight: str = "futuro digital"
    description: str = "Desenvolvemos websites e aplicações móveis que transformam ideias em experiências digitais extraordinárias. Android, iOS e Web."
    cta_text: str = "Começar Projeto"
    stats: List[dict] = []

class ServiceItem(BaseModel):
    id: Optional[str] = None
    icon: str = "Monitor"
    title: str
    description: str
    features: List[str]

class PortfolioItemCreate(BaseModel):
    title: str
    description: str
    image_url: str
    category: str
    technologies: List[str]
    link: Optional[str] = None

class TestimonialItem(BaseModel):
    id: Optional[str] = None
    name: str
    role: str
    image: str
    text: str

class ContactInfo(BaseModel):
    email: str = "contacto@andredev.pt"
    phone: str = "+351 912 345 678"
    location: str = "Lisboa, Portugal"

class SiteContent(BaseModel):
    hero: Optional[HeroContent] = None
    services: Optional[List[ServiceItem]] = None
    portfolio: Optional[List[PortfolioItemCreate]] = None
    testimonials: Optional[List[TestimonialItem]] = None
    contact_info: Optional[ContactInfo] = None

class AdminCreateClient(BaseModel):
    name: str
    email: EmailStr
    password: str
    company: Optional[str] = None

class EmailTemplate(BaseModel):
    template_id: str
    name: str
    subject: str
    title: str
    content: str

class EmailTemplatesUpdate(BaseModel):
    templates: List[EmailTemplate]


# ==================== EMAIL SERVICE ====================

# Modern table style with icons
TABLE_STYLE = """
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    margin: 25px 0;
    background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
"""

ROW_STYLE = "border-bottom: 1px solid #e2e8f0;"
CELL_STYLE = "padding: 16px 20px; vertical-align: middle;"
LABEL_STYLE = "color: #64748b; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;"
VALUE_STYLE = "color: #1e293b; font-size: 15px; font-weight: 500;"

# Default email templates
DEFAULT_EMAIL_TEMPLATES = {
    "password_reset": {
        "template_id": "password_reset",
        "name": "Reset de Password",
        "subject": "🔐 Redefinir Password - Andre Dev",
        "title": "Redefinir Password",
        "content": """<p style="font-size: 16px;">Olá <strong>{{nome}}</strong>,</p>
<p>Recebemos um pedido para redefinir a password da sua conta Andre Dev.</p>
<div style="background: linear-gradient(145deg, #fef3c7 0%, #fde68a 100%); border-left: 4px solid #f59e0b; padding: 16px 20px; border-radius: 8px; margin: 20px 0;">
    <p style="margin: 0; color: #92400e; font-weight: 500;">⏰ Este link expira em <strong>1 hora</strong>.</p>
</div>
<p>Clique no botão abaixo para criar uma nova password:</p>
<p style="color: #64748b; font-size: 14px; margin-top: 25px;">Se não solicitou esta alteração, pode ignorar este email com segurança.</p>"""
    },
    "new_project": {
        "template_id": "new_project",
        "name": "Novo Projeto (Admin)",
        "subject": "🚀 Novo Projeto: {{projeto}} - Andre Dev",
        "title": "Novo Projeto Criado",
        "content": """<p style="font-size: 16px;">Um novo projeto foi criado na plataforma!</p>
<table style="width: 100%; border-collapse: separate; border-spacing: 0; margin: 25px 0; background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%); border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
<tr style="border-bottom: 1px solid #e2e8f0;">
    <td style="padding: 16px 20px; width: 40px;">👤</td>
    <td style="padding: 16px 0;"><span style="color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Cliente</span><br><strong style="color: #1e293b; font-size: 15px;">{{cliente}}</strong><br><span style="color: #64748b; font-size: 13px;">{{email_cliente}}</span></td>
</tr>
<tr style="border-bottom: 1px solid #e2e8f0;">
    <td style="padding: 16px 20px;">📁</td>
    <td style="padding: 16px 0;"><span style="color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Projeto</span><br><strong style="color: #1e293b; font-size: 15px;">{{projeto}}</strong></td>
</tr>
<tr style="border-bottom: 1px solid #e2e8f0;">
    <td style="padding: 16px 20px;">🏷️</td>
    <td style="padding: 16px 0;"><span style="color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Tipo</span><br><strong style="color: #1e293b; font-size: 15px;">{{tipo}}</strong></td>
</tr>
<tr style="border-bottom: 1px solid #e2e8f0;">
    <td style="padding: 16px 20px;">💰</td>
    <td style="padding: 16px 0;"><span style="color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Orçamento</span><br><strong style="color: #22c55e; font-size: 18px;">{{orcamento}}</strong></td>
</tr>
<tr>
    <td style="padding: 16px 20px;">📝</td>
    <td style="padding: 16px 0;"><span style="color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Descrição</span><br><span style="color: #475569; font-size: 14px; line-height: 1.5;">{{descricao}}</span></td>
</tr>
</table>
<p>Aceda ao painel de administração para responder ao orçamento.</p>"""
    },
    "status_change": {
        "template_id": "status_change",
        "name": "Mudança de Estado",
        "subject": "📊 Projeto {{projeto}} - Estado Atualizado",
        "title": "Estado do Projeto Atualizado",
        "content": """<p style="font-size: 16px;">Olá <strong>{{nome}}</strong>,</p>
<p>O estado do seu projeto foi atualizado!</p>
<table style="width: 100%; border-collapse: separate; border-spacing: 0; margin: 25px 0; background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%); border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
<tr style="border-bottom: 1px solid #e2e8f0;">
    <td style="padding: 16px 20px; width: 40px;">📁</td>
    <td style="padding: 16px 0;"><span style="color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Projeto</span><br><strong style="color: #1e293b; font-size: 15px;">{{projeto}}</strong></td>
</tr>
<tr>
    <td style="padding: 16px 20px;">🎯</td>
    <td style="padding: 16px 0;"><span style="color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Novo Estado</span><br><span style="display: inline-block; margin-top: 8px; background: {{cor_estado}}; color: white; padding: 8px 20px; border-radius: 25px; font-size: 14px; font-weight: 600; box-shadow: 0 2px 8px rgba(0,0,0,0.15);">{{estado}}</span></td>
</tr>
</table>
<p>Aceda à sua área de cliente para mais detalhes.</p>"""
    },
    "budget_accepted": {
        "template_id": "budget_accepted",
        "name": "Orçamento Aprovado",
        "subject": "✅ Orçamento Aprovado - {{projeto}}",
        "title": "Orçamento Aprovado!",
        "content": """<p style="font-size: 16px;">Olá <strong>{{nome}}</strong>,</p>
<div style="background: linear-gradient(145deg, #dcfce7 0%, #bbf7d0 100%); border-radius: 12px; padding: 20px; margin: 20px 0; text-align: center;">
    <span style="font-size: 40px;">🎉</span>
    <p style="color: #166534; font-size: 18px; font-weight: 600; margin: 10px 0 0 0;">Ótimas notícias! O seu orçamento foi aprovado!</p>
</div>
<table style="width: 100%; border-collapse: separate; border-spacing: 0; margin: 25px 0; background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%); border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
<tr style="border-bottom: 1px solid #e2e8f0;">
    <td style="padding: 16px 20px; width: 40px;">📁</td>
    <td style="padding: 16px 0;"><span style="color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Projeto</span><br><strong style="color: #1e293b; font-size: 15px;">{{projeto}}</strong></td>
</tr>
<tr>
    <td style="padding: 16px 20px;">💰</td>
    <td style="padding: 16px 0;"><span style="color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Valor Aprovado</span><br><strong style="color: #22c55e; font-size: 24px;">{{valor}}</strong></td>
</tr>
</table>
{{notas}}
<p>Aceda à sua área de cliente para confirmar e iniciar o projeto.</p>"""
    },
    "budget_counter": {
        "template_id": "budget_counter",
        "name": "Contraproposta",
        "subject": "💬 Contraproposta de Orçamento - {{projeto}}",
        "title": "Contraproposta de Orçamento",
        "content": """<p style="font-size: 16px;">Olá <strong>{{nome}}</strong>,</p>
<div style="background: linear-gradient(145deg, #fef3c7 0%, #fde68a 100%); border-radius: 12px; padding: 20px; margin: 20px 0; text-align: center;">
    <span style="font-size: 40px;">💬</span>
    <p style="color: #92400e; font-size: 16px; font-weight: 600; margin: 10px 0 0 0;">Recebeu uma contraproposta para o seu projeto</p>
</div>
<table style="width: 100%; border-collapse: separate; border-spacing: 0; margin: 25px 0; background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%); border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
<tr style="border-bottom: 1px solid #e2e8f0;">
    <td style="padding: 16px 20px; width: 40px;">📁</td>
    <td style="padding: 16px 0;"><span style="color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Projeto</span><br><strong style="color: #1e293b; font-size: 15px;">{{projeto}}</strong></td>
</tr>
<tr style="border-bottom: 1px solid #e2e8f0;">
    <td style="padding: 16px 20px;">📤</td>
    <td style="padding: 16px 0;"><span style="color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Seu Orçamento</span><br><span style="color: #64748b; font-size: 16px; text-decoration: line-through;">{{orcamento_original}}</span></td>
</tr>
<tr>
    <td style="padding: 16px 20px;">📥</td>
    <td style="padding: 16px 0;"><span style="color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Contraproposta</span><br><strong style="color: #f59e0b; font-size: 24px;">{{contraproposta}}</strong></td>
</tr>
</table>
{{notas}}
<p>Aceda à sua área de cliente para aceitar ou discutir a proposta.</p>"""
    },
    "welcome_client": {
        "template_id": "welcome_client",
        "name": "Boas-vindas ao Cliente",
        "subject": "🎉 Bem-vindo à Andre Dev - Dados de Acesso",
        "title": "Bem-vindo à Andre Dev!",
        "content": """<p style="font-size: 16px;">Olá <strong>{{nome}}</strong>,</p>
<div style="background: linear-gradient(145deg, #dbeafe 0%, #bfdbfe 100%); border-radius: 12px; padding: 20px; margin: 20px 0; text-align: center;">
    <span style="font-size: 40px;">👋</span>
    <p style="color: #1e40af; font-size: 18px; font-weight: 600; margin: 10px 0 0 0;">A sua conta foi criada com sucesso!</p>
</div>
<p>Aqui estão os seus dados de acesso:</p>
<table style="width: 100%; border-collapse: separate; border-spacing: 0; margin: 25px 0; background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%); border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
<tr style="border-bottom: 1px solid #e2e8f0;">
    <td style="padding: 16px 20px; width: 40px;">📧</td>
    <td style="padding: 16px 0;"><span style="color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Email</span><br><strong style="color: #1e293b; font-size: 15px;">{{email}}</strong></td>
</tr>
<tr>
    <td style="padding: 16px 20px;">🔑</td>
    <td style="padding: 16px 0;"><span style="color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Password</span><br><code style="background: #1e293b; color: #22c55e; padding: 8px 16px; border-radius: 6px; font-size: 15px; font-family: monospace;">{{password}}</code></td>
</tr>
</table>
<div style="background: linear-gradient(145deg, #fef3c7 0%, #fde68a 100%); border-left: 4px solid #f59e0b; padding: 16px 20px; border-radius: 8px; margin: 20px 0;">
    <p style="margin: 0; color: #92400e; font-weight: 500;">⚠️ Recomendamos que altere a sua password após o primeiro login.</p>
</div>"""
    }
}

async def get_email_template(template_id: str) -> dict:
    """Get email template from database or return default"""
    templates_doc = await db.email_templates.find_one({"type": "email_templates"}, {"_id": 0})
    if templates_doc and "templates" in templates_doc:
        for template in templates_doc["templates"]:
            if template.get("template_id") == template_id:
                return template
    return DEFAULT_EMAIL_TEMPLATES.get(template_id, {})

def replace_template_variables(text: str, variables: dict) -> str:
    """Replace {{variable}} placeholders with actual values"""
    for key, value in variables.items():
        text = text.replace(f"{{{{{key}}}}}", str(value) if value else "")
    return text

async def send_email(to_email: str, subject: str, html_content: str):
    """Send email using Resend (non-blocking)"""
    if not resend.api_key:
        logger.warning("Resend API key not configured, skipping email")
        return None
    
    params = {
        "from": SENDER_EMAIL,
        "to": [to_email],
        "subject": subject,
        "html": html_content
    }
    
    try:
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Email sent to {to_email}: {subject}")
        return result
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return None

def get_base_email_template(title: str, content: str, button_text: str = None, button_url: str = None):
    """Generate HTML email template with modern design"""
    button_html = ""
    if button_text and button_url:
        button_html = f'''
        <tr>
            <td style="padding: 30px 0 10px 0; text-align: center;">
                <a href="{button_url}" style="
                    display: inline-block;
                    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
                    color: white;
                    padding: 16px 40px;
                    text-decoration: none;
                    border-radius: 50px;
                    font-weight: 600;
                    font-size: 15px;
                    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
                    transition: all 0.3s ease;
                ">
                    {button_text}
                </a>
            </td>
        </tr>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f4f8;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background: linear-gradient(180deg, #f0f4f8 0%, #e2e8f0 100%); padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: white; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.1), 0 2px 10px rgba(0,0,0,0.05);">
                        <!-- Header with Gradient -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 50%, #3b82f6 100%); padding: 40px 30px; text-align: center;">
                                <!-- Logo Icon -->
                                <div style="margin-bottom: 15px;">
                                    <span style="display: inline-block; background: rgba(255,255,255,0.15); padding: 12px 16px; border-radius: 12px;">
                                        <span style="color: white; font-size: 28px; font-weight: bold;">&lt;/&gt;</span>
                                    </span>
                                </div>
                                <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 700; letter-spacing: -0.5px;">Andre Dev</h1>
                                <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0 0; font-size: 14px; font-weight: 500;">Agência de Desenvolvimento Web & Mobile</p>
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding: 45px 35px;">
                                <h2 style="color: #1e3a5f; margin: 0 0 25px 0; font-size: 22px; font-weight: 700; letter-spacing: -0.3px;">{title}</h2>
                                <div style="color: #4b5563; line-height: 1.7; font-size: 15px;">
                                    {content}
                                </div>
                            </td>
                        </tr>
                        {button_html}
                        <!-- Footer -->
                        <tr>
                            <td style="background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%); padding: 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                                <div style="margin-bottom: 15px;">
                                    <a href="#" style="display: inline-block; margin: 0 8px; color: #64748b; text-decoration: none;">
                                        <span style="display: inline-block; width: 36px; height: 36px; background: #e2e8f0; border-radius: 50%; line-height: 36px; font-size: 14px;">🌐</span>
                                    </a>
                                    <a href="#" style="display: inline-block; margin: 0 8px; color: #64748b; text-decoration: none;">
                                        <span style="display: inline-block; width: 36px; height: 36px; background: #e2e8f0; border-radius: 50%; line-height: 36px; font-size: 14px;">📧</span>
                                    </a>
                                    <a href="#" style="display: inline-block; margin: 0 8px; color: #64748b; text-decoration: none;">
                                        <span style="display: inline-block; width: 36px; height: 36px; background: #e2e8f0; border-radius: 50%; line-height: 36px; font-size: 14px;">📱</span>
                                    </a>
                                </div>
                                <p style="color: #64748b; margin: 0; font-size: 13px; font-weight: 500;">
                                    © 2024 Andre Dev. Todos os direitos reservados.
                                </p>
                                <p style="color: #94a3b8; margin: 8px 0 0 0; font-size: 12px;">
                                    Este email foi enviado automaticamente. Por favor, não responda.
                                </p>
                            </td>
                        </tr>
                    </table>
                    <!-- Bottom Shadow Effect -->
                    <div style="height: 8px; background: linear-gradient(180deg, rgba(0,0,0,0.05) 0%, transparent 100%); border-radius: 0 0 16px 16px; width: 580px; margin: 0 auto;"></div>
                </td>
            </tr>
        </table>
    </body>
    </html>
    '''


# ==================== HELPERS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_reset_token(email: str) -> str:
    """Create a password reset token valid for 1 hour"""
    payload = {
        "email": email,
        "type": "password_reset",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_reset_token(token: str) -> dict:
    """Decode and validate password reset token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "password_reset":
            raise HTTPException(status_code=400, detail="Token inválido")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token expirado. Por favor, solicite um novo link.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Token inválido")

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)
    user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Utilizador não encontrado")
    return user

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return current_user


# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register", response_model=TokenResponse)
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserRegister):
    ip_address = get_remote_address(request)
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        await log_audit("REGISTER_FAILED", user_email=user_data.email, 
                       ip_address=ip_address, status="failed",
                       details={"reason": "Email já registado"})
        raise HTTPException(status_code=400, detail="Email já registado")
    
    # Create user
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "name": user_data.name,
        "email": user_data.email,
        "password": hash_password(user_data.password),
        "company": user_data.company,
        "role": "client",
        "two_factor_enabled": False,
        "two_factor_secret": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    # Log successful registration
    await log_audit("USER_REGISTERED", user_id=user_id, user_email=user_data.email,
                   ip_address=ip_address, details={"name": user_data.name})
    
    # Create token
    token = create_token(user_id)
    
    user_response = UserResponse(
        id=user_id,
        name=user_data.name,
        email=user_data.email,
        company=user_data.company,
        role="client",
        created_at=user_doc["created_at"]
    )
    
    return TokenResponse(access_token=token, user=user_response)

@api_router.post("/auth/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, credentials: UserLogin):
    ip_address = get_remote_address(request)
    
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user:
        await log_audit("LOGIN_FAILED", user_email=credentials.email,
                       ip_address=ip_address, status="failed",
                       details={"reason": "User not found"})
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    if not verify_password(credentials.password, user["password"]):
        await log_audit("LOGIN_FAILED", user_id=user["id"], user_email=credentials.email,
                       ip_address=ip_address, status="failed",
                       details={"reason": "Invalid password"})
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    # Check if 2FA is enabled
    if user.get("two_factor_enabled") and user.get("two_factor_secret"):
        # Return partial response indicating 2FA is required
        return JSONResponse(content={
            "requires_2fa": True,
            "user_id": user["id"],
            "message": "2FA verification required"
        })
    
    # Log successful login
    await log_audit("LOGIN_SUCCESS", user_id=user["id"], user_email=credentials.email,
                   ip_address=ip_address)
    
    token = create_token(user["id"])
    
    user_response = UserResponse(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        company=user.get("company"),
        role=user.get("role", "client"),
        created_at=user["created_at"]
    )
    
    return TokenResponse(access_token=token, user=user_response)

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        name=current_user["name"],
        email=current_user["email"],
        company=current_user.get("company"),
        role=current_user.get("role", "client"),
        created_at=current_user["created_at"]
    )

@api_router.put("/auth/profile")
async def update_profile(
    name: Optional[str] = None,
    company: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    update_data = {}
    if name:
        update_data["name"] = name
    if company is not None:
        update_data["company"] = company
    
    if update_data:
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$set": update_data}
        )
    
    updated_user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0, "password": 0})
    return updated_user


# ==================== TWO-FACTOR AUTHENTICATION (2FA) ====================

@api_router.post("/auth/2fa/setup")
async def setup_2fa(current_user: dict = Depends(get_current_user)):
    """Generate 2FA secret and QR code for setup"""
    # Generate new secret
    secret = pyotp.random_base32()
    
    # Create TOTP object
    totp = pyotp.TOTP(secret)
    
    # Generate provisioning URI for QR code
    provisioning_uri = totp.provisioning_uri(
        name=current_user["email"],
        issuer_name="Andre Dev"
    )
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    # Store secret temporarily (not enabled yet)
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {"two_factor_secret_pending": secret}}
    )
    
    await log_audit("2FA_SETUP_INITIATED", user_id=current_user["id"], 
                   user_email=current_user["email"])
    
    return {
        "secret": secret,
        "qr_code": f"data:image/png;base64,{qr_base64}",
        "message": "Escaneie o QR code com o seu app de autenticação (Google Authenticator, Authy, etc.)"
    }


@api_router.post("/auth/2fa/verify-setup")
async def verify_2fa_setup(
    code: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Verify 2FA code and enable 2FA for user"""
    user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0})
    
    pending_secret = user.get("two_factor_secret_pending")
    if not pending_secret:
        raise HTTPException(status_code=400, detail="Nenhuma configuração 2FA pendente")
    
    # Verify code
    totp = pyotp.TOTP(pending_secret)
    if not totp.verify(code):
        await log_audit("2FA_SETUP_FAILED", user_id=current_user["id"],
                       user_email=current_user["email"], status="failed",
                       details={"reason": "Invalid code"})
        raise HTTPException(status_code=400, detail="Código inválido")
    
    # Enable 2FA
    await db.users.update_one(
        {"id": current_user["id"]},
        {
            "$set": {
                "two_factor_enabled": True,
                "two_factor_secret": pending_secret
            },
            "$unset": {"two_factor_secret_pending": ""}
        }
    )
    
    await log_audit("2FA_ENABLED", user_id=current_user["id"],
                   user_email=current_user["email"])
    
    return {"message": "2FA ativado com sucesso!", "enabled": True}


@api_router.post("/auth/2fa/verify")
@limiter.limit("5/minute")
async def verify_2fa(
    request: Request,
    user_id: str = Form(...),
    code: str = Form(...)
):
    """Verify 2FA code during login"""
    ip_address = get_remote_address(request)
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    
    if not user.get("two_factor_enabled") or not user.get("two_factor_secret"):
        raise HTTPException(status_code=400, detail="2FA não está ativado")
    
    # Verify code
    totp = pyotp.TOTP(user["two_factor_secret"])
    if not totp.verify(code):
        await log_audit("2FA_VERIFY_FAILED", user_id=user_id,
                       user_email=user["email"], ip_address=ip_address,
                       status="failed", details={"reason": "Invalid code"})
        raise HTTPException(status_code=400, detail="Código inválido")
    
    # Log successful 2FA verification
    await log_audit("2FA_VERIFY_SUCCESS", user_id=user_id,
                   user_email=user["email"], ip_address=ip_address)
    
    # Create token
    token = create_token(user_id)
    
    user_response = UserResponse(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        company=user.get("company"),
        role=user.get("role", "client"),
        created_at=user["created_at"]
    )
    
    return TokenResponse(access_token=token, user=user_response)


@api_router.post("/auth/2fa/disable")
async def disable_2fa(
    code: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Disable 2FA for user"""
    user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0})
    
    if not user.get("two_factor_enabled"):
        raise HTTPException(status_code=400, detail="2FA não está ativado")
    
    # Verify code before disabling
    totp = pyotp.TOTP(user["two_factor_secret"])
    if not totp.verify(code):
        await log_audit("2FA_DISABLE_FAILED", user_id=current_user["id"],
                       user_email=current_user["email"], status="failed",
                       details={"reason": "Invalid code"})
        raise HTTPException(status_code=400, detail="Código inválido")
    
    # Disable 2FA
    await db.users.update_one(
        {"id": current_user["id"]},
        {
            "$set": {"two_factor_enabled": False},
            "$unset": {"two_factor_secret": ""}
        }
    )
    
    await log_audit("2FA_DISABLED", user_id=current_user["id"],
                   user_email=current_user["email"])
    
    return {"message": "2FA desativado com sucesso!", "enabled": False}


@api_router.get("/auth/2fa/status")
async def get_2fa_status(current_user: dict = Depends(get_current_user)):
    """Get 2FA status for current user"""
    user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0})
    return {
        "enabled": user.get("two_factor_enabled", False),
        "email": user["email"]
    }


# ==================== AUDIT LOGS ROUTES ====================

@api_router.get("/admin/audit-logs")
async def get_audit_logs(
    page: int = 1,
    limit: int = 50,
    action: str = None,
    user_email: str = None,
    status: str = None,
    admin: dict = Depends(get_admin_user)
):
    """Get audit logs (admin only)"""
    query = {}
    
    if action:
        query["action"] = {"$regex": action, "$options": "i"}
    if user_email:
        query["user_email"] = {"$regex": user_email, "$options": "i"}
    if status:
        query["status"] = status
    
    skip = (page - 1) * limit
    
    logs = await db.audit_logs.find(
        query,
        {"_id": 0}
    ).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    
    total = await db.audit_logs.count_documents(query)
    
    return {
        "logs": logs,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }


@api_router.get("/admin/security-stats")
async def get_security_stats(admin: dict = Depends(get_admin_user)):
    """Get security statistics (admin only)"""
    now = datetime.now(timezone.utc)
    last_24h = (now - timedelta(hours=24)).isoformat()
    last_7d = (now - timedelta(days=7)).isoformat()
    
    # Login stats
    login_success_24h = await db.audit_logs.count_documents({
        "action": "LOGIN_SUCCESS",
        "timestamp": {"$gte": last_24h}
    })
    
    login_failed_24h = await db.audit_logs.count_documents({
        "action": "LOGIN_FAILED",
        "timestamp": {"$gte": last_24h}
    })
    
    # Registration stats
    registrations_7d = await db.audit_logs.count_documents({
        "action": "USER_REGISTERED",
        "timestamp": {"$gte": last_7d}
    })
    
    # 2FA stats
    users_with_2fa = await db.users.count_documents({"two_factor_enabled": True})
    total_users = await db.users.count_documents({})
    
    # Recent suspicious activity (multiple failed logins from same IP)
    suspicious_ips = await db.audit_logs.aggregate([
        {
            "$match": {
                "action": "LOGIN_FAILED",
                "timestamp": {"$gte": last_24h}
            }
        },
        {
            "$group": {
                "_id": "$ip_address",
                "count": {"$sum": 1}
            }
        },
        {
            "$match": {"count": {"$gte": 5}}
        },
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    return {
        "login_success_24h": login_success_24h,
        "login_failed_24h": login_failed_24h,
        "registrations_7d": registrations_7d,
        "users_with_2fa": users_with_2fa,
        "total_users": total_users,
        "two_factor_adoption": round((users_with_2fa / total_users * 100), 1) if total_users > 0 else 0,
        "suspicious_ips": suspicious_ips
    }


# ==================== PASSWORD RESET ROUTES ====================

@api_router.post("/auth/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(request: Request, data: PasswordResetRequest):
    """Request password reset - generates token"""
    ip_address = get_remote_address(request)
    user = await db.users.find_one({"email": data.email}, {"_id": 0})
    
    # Log the attempt
    await log_audit("PASSWORD_RESET_REQUESTED", user_email=data.email, ip_address=ip_address)
    
    # Always return success to prevent email enumeration
    if not user:
        return {"message": "Se o email existir, receberá instruções para recuperar a password."}
    
    # Generate reset token
    reset_token = create_reset_token(data.email)
    
    # Store reset token in database (optional, for additional security)
    await db.password_resets.update_one(
        {"email": data.email},
        {
            "$set": {
                "email": data.email,
                "token": reset_token,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "used": False
            }
        },
        upsert=True
    )
    
    # Send password reset email
    frontend_url = os.environ.get('FRONTEND_URL', 'https://appagency-fix.preview.emergentagent.com')
    reset_url = f"{frontend_url}/reset-password?token={reset_token}"
    
    # Get template from database
    template = await get_email_template("password_reset")
    content = replace_template_variables(template.get("content", ""), {
        "nome": user.get("name", "")
    })
    
    # Add button
    content += f'''
        <p style="margin: 25px 0;">
            <a href="{reset_url}" style="background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">
                Redefinir Password
            </a>
        </p>
    '''
    
    subject = replace_template_variables(template.get("subject", "Redefinir Password"), {"nome": user.get("name", "")})
    
    await send_email(
        to_email=data.email,
        subject=subject,
        html_content=get_base_email_template(template.get("title", "Redefinir Password"), content)
    )
    
    logger.info(f"Password reset requested for {data.email}")
    
    return {
        "message": "Se o email existir, receberá instruções para recuperar a password."
    }

@api_router.post("/auth/reset-password")
async def reset_password(data: PasswordResetConfirm):
    """Reset password using token"""
    # Decode and validate token
    payload = decode_reset_token(data.token)
    email = payload.get("email")
    
    if not email:
        raise HTTPException(status_code=400, detail="Token inválido")
    
    # Check if token was already used
    reset_record = await db.password_resets.find_one({"email": email, "token": data.token})
    if reset_record and reset_record.get("used"):
        raise HTTPException(status_code=400, detail="Este link já foi utilizado. Por favor, solicite um novo.")
    
    # Find user
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=400, detail="Utilizador não encontrado")
    
    # Validate password
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="A password deve ter pelo menos 6 caracteres")
    
    # Update password
    hashed_password = hash_password(data.new_password)
    await db.users.update_one(
        {"email": email},
        {"$set": {"password": hashed_password}}
    )
    
    # Mark token as used
    await db.password_resets.update_one(
        {"email": email, "token": data.token},
        {"$set": {"used": True}}
    )
    
    logger.info(f"Password reset successful for {email}")
    return {"message": "Password alterada com sucesso! Pode agora fazer login."}

@api_router.get("/auth/verify-reset-token")
async def verify_reset_token(token: str):
    """Verify if a reset token is valid"""
    try:
        payload = decode_reset_token(token)
        email = payload.get("email")
        
        # Check if token was already used
        reset_record = await db.password_resets.find_one({"email": email, "token": token})
        if reset_record and reset_record.get("used"):
            return {"valid": False, "message": "Este link já foi utilizado."}
        
        return {"valid": True, "email": email}
    except HTTPException as e:
        return {"valid": False, "message": e.detail}


# ==================== PROJECT ROUTES ====================

@api_router.post("/projects", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: dict = Depends(get_current_user)
):
    project_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    project_doc = {
        "id": project_id,
        "user_id": current_user["id"],
        "name": project_data.name,
        "description": project_data.description,
        "project_type": project_data.project_type,
        "status": project_data.status,
        "budget": project_data.budget,
        "budget_status": "pending",
        "counter_proposal": None,
        "admin_notes": None,
        "official_value": None,
        "messages": [],
        "files": [],
        "previews": [],
        "created_at": now,
        "updated_at": now
    }
    
    await db.projects.insert_one(project_doc)
    
    # Notify admin about new project
    admin = await db.users.find_one({"role": "admin"}, {"_id": 0})
    if admin:
        project_types = {"web": "Website", "android": "Android", "ios": "iOS"}
        template = await get_email_template("new_project")
        
        variables = {
            "cliente": current_user["name"],
            "email_cliente": current_user["email"],
            "projeto": project_data.name,
            "tipo": project_types.get(project_data.project_type, project_data.project_type),
            "orcamento": project_data.budget,
            "descricao": project_data.description
        }
        
        content = replace_template_variables(template.get("content", ""), variables)
        subject = replace_template_variables(template.get("subject", f"Novo Projeto: {project_data.name}"), variables)
        
        await send_email(
            to_email=admin["email"],
            subject=subject,
            html_content=get_base_email_template(template.get("title", "Novo Projeto"), content)
        )
    
    return ProjectResponse(**{k: v for k, v in project_doc.items() if k != "_id"})

@api_router.get("/projects", response_model=List[ProjectResponse])
async def get_projects(
    current_user: dict = Depends(get_current_user),
    search: Optional[str] = None,
    status: Optional[str] = None,
    project_type: Optional[str] = None
):
    """Get user projects with optional search and filters"""
    query = {"user_id": current_user["id"]}
    
    # Add search filter
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    # Add status filter
    if status:
        query["status"] = status
    
    # Add project type filter
    if project_type:
        query["project_type"] = project_type
    
    projects = await db.projects.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).to_list(None)
    
    return [ProjectResponse(**project) for project in projects]

@api_router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, current_user: dict = Depends(get_current_user)):
    project = await db.projects.find_one(
        {"id": project_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return project

@api_router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: dict = Depends(get_current_user)
):
    project = await db.projects.find_one(
        {"id": project_id, "user_id": current_user["id"]}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    update_data = {k: v for k, v in project_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.projects.update_one(
        {"id": project_id},
        {"$set": update_data}
    )
    
    updated = await db.projects.find_one({"id": project_id}, {"_id": 0})
    return updated

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.projects.delete_one(
        {"id": project_id, "user_id": current_user["id"]}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return {"message": "Projeto eliminado com sucesso"}


# ==================== PROJECT DETAILS ROUTES ====================

@api_router.post("/projects/{project_id}/messages")
async def add_project_message(
    project_id: str,
    message_data: ProjectMessage,
    current_user: dict = Depends(get_current_user)
):
    """Add a message to project chat"""
    project = await db.projects.find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Check if user has access (owner or admin)
    if project["user_id"] != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    message = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "user_name": current_user["name"],
        "content": message_data.content,
        "attachment": message_data.attachment,
        "edited": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.projects.update_one(
        {"id": project_id},
        {
            "$push": {"messages": message},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    return {"message": "Mensagem adicionada", "data": message}

@api_router.get("/projects/{project_id}/messages")
async def get_project_messages(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all messages from a project"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Check if user has access
    if project["user_id"] != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    return project.get("messages", [])

@api_router.put("/projects/{project_id}/messages/{message_id}")
async def update_project_message(
    project_id: str,
    message_id: str,
    message_data: ProjectMessageUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Edit a message"""
    project = await db.projects.find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Find message and check ownership
    message_to_update = None
    for msg in project.get("messages", []):
        if msg["id"] == message_id:
            message_to_update = msg
            break
    
    if not message_to_update:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    
    if message_to_update["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Sem permissão para editar esta mensagem")
    
    # Update message
    await db.projects.update_one(
        {"id": project_id, "messages.id": message_id},
        {
            "$set": {
                "messages.$.content": message_data.content,
                "messages.$.edited": True,
                "messages.$.updated_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"message": "Mensagem atualizada"}

@api_router.delete("/projects/{project_id}/messages/{message_id}")
async def delete_project_message(
    project_id: str,
    message_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a message"""
    project = await db.projects.find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Find message and check ownership
    message_to_delete = None
    for msg in project.get("messages", []):
        if msg["id"] == message_id:
            message_to_delete = msg
            break
    
    if not message_to_delete:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    
    if message_to_delete["user_id"] != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    # Delete message
    await db.projects.update_one(
        {"id": project_id},
        {
            "$pull": {"messages": {"id": message_id}},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    return {"message": "Mensagem eliminada"}


@api_router.post("/projects/{project_id}/files")
async def add_project_file(
    project_id: str,
    file_data: ProjectFileUpload,
    current_user: dict = Depends(get_current_user)
):
    """Add a file to the project (supports URL or base64 upload - saves to disk)"""
    project = await db.projects.find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Check if user has access
    if project["user_id"] != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    file_id = str(uuid.uuid4())
    file_url = file_data.file_url
    
    # If base64 data provided, save to disk
    if file_data.file_data:
        try:
            # Decode base64 and save to file
            file_bytes = base64.b64decode(file_data.file_data)
            
            # Generate unique filename
            ext = Path(file_data.filename).suffix or ''
            disk_filename = f"{file_id}{ext}"
            file_path = UPLOADS_DIR / 'files' / disk_filename
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_bytes)
            
            # Store the URL path instead of base64 - use /api/uploads for proper routing
            file_url = f"/api/uploads/files/{disk_filename}"
            logger.info(f"File saved to disk: {file_path}")
        except Exception as e:
            logger.error(f"Error saving file to disk: {e}")
            raise HTTPException(status_code=500, detail="Erro ao guardar ficheiro")
    
    file_entry = {
        "id": file_id,
        "filename": file_data.filename,
        "file_url": file_url,
        "uploaded_by": current_user["id"],
        "uploaded_by_name": current_user["name"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.projects.update_one(
        {"id": project_id},
        {
            "$push": {"files": file_entry},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    return {"message": "Ficheiro adicionado", "data": file_entry}

@api_router.get("/projects/{project_id}/files")
async def get_project_files(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all files from a project"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    if project["user_id"] != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    return project.get("files", [])

@api_router.post("/projects/{project_id}/previews")
async def add_project_preview(
    project_id: str,
    preview_data: ProjectPreview,
    current_user: dict = Depends(get_admin_user)
):
    """Add a preview to the project (Admin only) - saves files to disk"""
    project = await db.projects.find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    preview_id = str(uuid.uuid4())
    image_url = preview_data.image_url
    
    # If base64 data provided, save to disk
    if preview_data.image_data:
        try:
            # Decode base64 and save to file
            file_bytes = base64.b64decode(preview_data.image_data)
            
            # Determine file extension from mime type
            ext = '.bin'
            if preview_data.mime_type:
                if 'jpeg' in preview_data.mime_type or 'jpg' in preview_data.mime_type:
                    ext = '.jpg'
                elif 'png' in preview_data.mime_type:
                    ext = '.png'
                elif 'gif' in preview_data.mime_type:
                    ext = '.gif'
                elif 'webp' in preview_data.mime_type:
                    ext = '.webp'
                elif 'mp4' in preview_data.mime_type:
                    ext = '.mp4'
                elif 'webm' in preview_data.mime_type:
                    ext = '.webm'
                elif 'mov' in preview_data.mime_type or 'quicktime' in preview_data.mime_type:
                    ext = '.mov'
                elif 'avi' in preview_data.mime_type:
                    ext = '.avi'
            
            disk_filename = f"{preview_id}{ext}"
            file_path = UPLOADS_DIR / 'previews' / disk_filename
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_bytes)
            
            # Store the URL path instead of base64 - use /api/uploads for proper routing
            image_url = f"/api/uploads/previews/{disk_filename}"
            logger.info(f"Preview saved to disk: {file_path} ({len(file_bytes) / (1024*1024):.2f}MB)")
        except Exception as e:
            logger.error(f"Error saving preview to disk: {e}")
            raise HTTPException(status_code=500, detail="Erro ao guardar preview")
    
    preview = {
        "id": preview_id,
        "image_url": image_url,
        "mime_type": preview_data.mime_type,
        "description": preview_data.description,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.projects.update_one(
        {"id": project_id},
        {
            "$push": {"previews": preview},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    return {"message": "Preview adicionado", "data": preview}

@api_router.get("/projects/{project_id}/previews")
async def get_project_previews(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all previews from a project"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    if project["user_id"] != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    return project.get("previews", [])

@api_router.post("/projects/{project_id}/accept-proposal")
async def accept_proposal(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Client accepts the budget proposal (sets official value)"""
    project = await db.projects.find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    if project["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    if project["budget_status"] not in ["accepted", "counter_proposal"]:
        raise HTTPException(status_code=400, detail="Aguarda resposta do administrador")
    
    # Set official value based on counter_proposal or original budget
    official_value = project.get("counter_proposal") or project["budget"]
    
    await db.projects.update_one(
        {"id": project_id},
        {
            "$set": {
                "official_value": official_value,
                "budget_status": "accepted",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"message": "Proposta aceite", "official_value": official_value}



# ==================== MESSAGE ROUTES ====================

@api_router.post("/messages", response_model=MessageResponse)
async def create_message(
    message_data: MessageCreate,
    current_user: dict = Depends(get_current_user)
):
    message_id = str(uuid.uuid4())
    
    message_doc = {
        "id": message_id,
        "user_id": current_user["id"],
        "subject": message_data.subject,
        "content": message_data.content,
        "is_read": False,
        "admin_reply": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.messages.insert_one(message_doc)
    
    return MessageResponse(**{k: v for k, v in message_doc.items() if k != "_id"})

@api_router.get("/messages", response_model=List[MessageResponse])
async def get_messages(current_user: dict = Depends(get_current_user)):
    messages = await db.messages.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return messages


# ==================== CONTACT ROUTES (PUBLIC) ====================

@api_router.post("/contact", response_model=ContactResponse)
async def submit_contact(contact_data: ContactCreate):
    contact_id = str(uuid.uuid4())
    
    contact_doc = {
        "id": contact_id,
        "name": contact_data.name,
        "email": contact_data.email,
        "phone": contact_data.phone,
        "message": contact_data.message,
        "service_type": contact_data.service_type,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.contacts.insert_one(contact_doc)
    
    return ContactResponse(**{k: v for k, v in contact_doc.items() if k != "_id"})


# ==================== PORTFOLIO ROUTES (PUBLIC) ====================

@api_router.get("/portfolio", response_model=List[PortfolioItem])
async def get_portfolio():
    # Return sample portfolio items
    portfolio_items = [
        {
            "id": "1",
            "title": "E-Commerce Platform",
            "description": "Plataforma completa de e-commerce com pagamentos integrados",
            "image_url": "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=600",
            "category": "web",
            "technologies": ["React", "Node.js", "MongoDB", "Stripe"],
            "link": None
        },
        {
            "id": "2",
            "title": "App de Fitness",
            "description": "Aplicação móvel para tracking de exercícios e nutrição",
            "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=600",
            "category": "mobile",
            "technologies": ["React Native", "Firebase", "HealthKit"],
            "link": None
        },
        {
            "id": "3",
            "title": "Sistema de Gestão",
            "description": "Dashboard completo para gestão empresarial",
            "image_url": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=600",
            "category": "web",
            "technologies": ["Vue.js", "Python", "PostgreSQL"],
            "link": None
        },
        {
            "id": "4",
            "title": "App de Delivery",
            "description": "Aplicação de entregas com tracking em tempo real",
            "image_url": "https://images.unsplash.com/photo-1526367790999-0150786686a2?w=600",
            "category": "mobile",
            "technologies": ["Flutter", "Google Maps", "Node.js"],
            "link": None
        }
    ]
    return portfolio_items


# ==================== STATS ROUTES ====================

@api_router.get("/stats")
async def get_stats(current_user: dict = Depends(get_current_user)):
    total_projects = await db.projects.count_documents({"user_id": current_user["id"]})
    pending = await db.projects.count_documents({"user_id": current_user["id"], "status": "pending"})
    in_progress = await db.projects.count_documents({"user_id": current_user["id"], "status": "in_progress"})
    completed = await db.projects.count_documents({"user_id": current_user["id"], "status": "completed"})
    unread_messages = await db.messages.count_documents({"user_id": current_user["id"], "is_read": False})
    
    return {
        "total_projects": total_projects,
        "pending": pending,
        "in_progress": in_progress,
        "completed": completed,
        "unread_messages": unread_messages
    }


# ==================== ROOT ROUTE ====================

@api_router.get("/")
async def root():
    return {"message": "Andre Dev API - Bem-vindo!"}


# ==================== ADMIN ROUTES ====================

@api_router.post("/admin/setup", response_model=TokenResponse)
async def setup_admin(admin_data: AdminCreate):
    """Create initial admin account (only works if no admin exists)"""
    existing_admin = await db.users.find_one({"role": "admin"})
    if existing_admin:
        raise HTTPException(status_code=400, detail="Já existe um administrador")
    
    admin_id = str(uuid.uuid4())
    admin_doc = {
        "id": admin_id,
        "name": admin_data.name,
        "email": admin_data.email,
        "password": hash_password(admin_data.password),
        "company": None,
        "role": "admin",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(admin_doc)
    token = create_token(admin_id)
    
    user_response = UserResponse(
        id=admin_id,
        name=admin_data.name,
        email=admin_data.email,
        company=None,
        role="admin",
        created_at=admin_doc["created_at"]
    )
    
    return TokenResponse(access_token=token, user=user_response)

@api_router.get("/admin/check")
async def check_admin_exists():
    """Check if admin account exists"""
    existing_admin = await db.users.find_one({"role": "admin"}, {"_id": 0, "password": 0})
    return {"admin_exists": existing_admin is not None}

@api_router.get("/admin/contacts")
async def get_all_contacts(admin: dict = Depends(get_admin_user)):
    """Get all contact form submissions"""
    contacts = await db.contacts.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return contacts

@api_router.delete("/admin/contacts/{contact_id}")
async def delete_contact(contact_id: str, admin: dict = Depends(get_admin_user)):
    """Delete a contact submission"""
    result = await db.contacts.delete_one({"id": contact_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Contacto não encontrado")
    return {"message": "Contacto eliminado"}

@api_router.get("/admin/users")
async def get_all_users(admin: dict = Depends(get_admin_user)):
    """Get all registered users"""
    users = await db.users.find({"role": "client"}, {"_id": 0, "password": 0}).sort("created_at", -1).to_list(100)
    return users

@api_router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(get_admin_user)):
    """Delete a user and their projects/messages"""
    user = await db.users.find_one({"id": user_id, "role": "client"})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    
    await db.users.delete_one({"id": user_id})
    await db.projects.delete_many({"user_id": user_id})
    await db.messages.delete_many({"user_id": user_id})
    
    return {"message": "Utilizador eliminado"}

@api_router.post("/admin/users", response_model=UserResponse)
async def admin_create_user(user_data: AdminCreateClient, admin: dict = Depends(get_admin_user)):
    """Admin creates a new client account"""
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email já registado")
    
    # Create user
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "name": user_data.name,
        "email": user_data.email,
        "password": hash_password(user_data.password),
        "company": user_data.company,
        "role": "client",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    # Send welcome email to new client
    frontend_url = os.environ.get('FRONTEND_URL', 'https://appagency-fix.preview.emergentagent.com')
    
    # Get template from database
    template = await get_email_template("welcome_client")
    variables = {
        "nome": user_data.name,
        "email": user_data.email,
        "password": user_data.password
    }
    
    content = replace_template_variables(template.get("content", ""), variables)
    content += f'''
        <p style="margin: 25px 0;">
            <a href="{frontend_url}/login" style="background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">
                Aceder à Plataforma
            </a>
        </p>
    '''
    
    subject = replace_template_variables(template.get("subject", "Bem-vindo à Andre Dev"), variables)
    
    await send_email(
        to_email=user_data.email,
        subject=subject,
        html_content=get_base_email_template(template.get("title", "Bem-vindo à Andre Dev!"), content)
    )
    
    logger.info(f"Admin created client account: {user_data.email}")
    
    return UserResponse(
        id=user_id,
        name=user_data.name,
        email=user_data.email,
        company=user_data.company,
        role="client",
        created_at=user_doc["created_at"]
    )

@api_router.get("/admin/projects")
async def get_all_projects(admin: dict = Depends(get_admin_user)):
    """Get all projects from all users"""
    projects = await db.projects.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    # Add user info to each project
    for project in projects:
        user = await db.users.find_one({"id": project["user_id"]}, {"_id": 0, "password": 0})
        project["user"] = {"name": user["name"], "email": user["email"]} if user else None
    return projects


@api_router.get("/admin/projects/{project_id}")
async def get_admin_project(project_id: str, admin: dict = Depends(get_admin_user)):
    """Get a specific project (admin view)"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Add user info
    user = await db.users.find_one({"id": project["user_id"]}, {"_id": 0, "password": 0})
    project["user"] = {"name": user["name"], "email": user["email"]} if user else None
    
    return project

@api_router.put("/admin/projects/{project_id}/status")
async def update_project_status(
    project_id: str,
    status: str,
    admin: dict = Depends(get_admin_user)
):
    """Update project status"""
    if status not in ["pending", "in_progress", "completed"]:
        raise HTTPException(status_code=400, detail="Estado inválido")
    
    # Get project and user before update
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    old_status = project.get("status")
    
    result = await db.projects.update_one(
        {"id": project_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Notify client about status change
    if old_status != status:
        user = await db.users.find_one({"id": project["user_id"]}, {"_id": 0})
        if user:
            status_labels = {
                "pending": "Pendente",
                "in_progress": "Em Progresso",
                "completed": "Concluído"
            }
            status_colors = {
                "pending": "#eab308",
                "in_progress": "#3b82f6",
                "completed": "#22c55e"
            }
            
            template = await get_email_template("status_change")
            variables = {
                "nome": user["name"],
                "projeto": project["name"],
                "estado": status_labels.get(status, status),
                "cor_estado": status_colors.get(status, "#6b7280")
            }
            
            content = replace_template_variables(template.get("content", ""), variables)
            subject = replace_template_variables(template.get("subject", f"Projeto {project['name']} - Estado Atualizado"), variables)
            
            await send_email(
                to_email=user["email"],
                subject=subject,
                html_content=get_base_email_template(template.get("title", "Estado do Projeto Atualizado"), content)
            )
    
    return {"message": "Estado atualizado"}

@api_router.put("/admin/projects/{project_id}/budget-response")
async def respond_to_budget(
    project_id: str,
    budget_response: BudgetResponse,
    admin: dict = Depends(get_admin_user)
):
    """Admin responds to project budget - accept or counter-proposal"""
    if budget_response.budget_status not in ["accepted", "counter_proposal"]:
        raise HTTPException(status_code=400, detail="Estado de orçamento inválido")
    
    # Get project and user before update
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    update_data = {
        "budget_status": budget_response.budget_status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if budget_response.budget_status == "counter_proposal":
        if not budget_response.counter_proposal:
            raise HTTPException(status_code=400, detail="Contraproposta é obrigatória")
        update_data["counter_proposal"] = budget_response.counter_proposal
    
    if budget_response.admin_notes:
        update_data["admin_notes"] = budget_response.admin_notes
    
    result = await db.projects.update_one(
        {"id": project_id},
        {"$set": update_data}
    )
    
    # Notify client about budget response
    user = await db.users.find_one({"id": project["user_id"]}, {"_id": 0})
    if user:
        notas_html = f'<p><strong>Notas:</strong> {budget_response.admin_notes}</p>' if budget_response.admin_notes else ''
        
        if budget_response.budget_status == "accepted":
            template = await get_email_template("budget_accepted")
            variables = {
                "nome": user["name"],
                "projeto": project["name"],
                "valor": project["budget"],
                "notas": notas_html
            }
        else:
            template = await get_email_template("budget_counter")
            variables = {
                "nome": user["name"],
                "projeto": project["name"],
                "orcamento_original": project["budget"],
                "contraproposta": budget_response.counter_proposal,
                "notas": notas_html
            }
        
        content = replace_template_variables(template.get("content", ""), variables)
        subject = replace_template_variables(template.get("subject", f"Orçamento - {project['name']}"), variables)
        
        await send_email(
            to_email=user["email"],
            subject=subject,
            html_content=get_base_email_template(template.get("title", "Resposta ao Orçamento"), content)
        )
    
    return {"message": "Resposta ao orçamento enviada"}

@api_router.get("/admin/messages")
async def get_all_messages(admin: dict = Depends(get_admin_user)):
    """Get all messages from all users"""
    messages = await db.messages.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    # Add user info
    for message in messages:
        user = await db.users.find_one({"id": message["user_id"]}, {"_id": 0, "password": 0})
        message["user"] = {"name": user["name"], "email": user["email"]} if user else None
    return messages

@api_router.put("/admin/messages/{message_id}/reply")
async def reply_to_message(
    message_id: str,
    reply: str,
    admin: dict = Depends(get_admin_user)
):
    """Reply to a user message"""
    result = await db.messages.update_one(
        {"id": message_id},
        {"$set": {"admin_reply": reply, "is_read": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    
    return {"message": "Resposta enviada"}

@api_router.get("/admin/stats")
async def get_admin_stats(admin: dict = Depends(get_admin_user)):
    """Get overall statistics"""
    total_users = await db.users.count_documents({"role": "client"})
    total_contacts = await db.contacts.count_documents({})
    total_projects = await db.projects.count_documents({})
    pending_projects = await db.projects.count_documents({"status": "pending"})
    in_progress_projects = await db.projects.count_documents({"status": "in_progress"})
    completed_projects = await db.projects.count_documents({"status": "completed"})
    total_messages = await db.messages.count_documents({})
    unread_messages = await db.messages.count_documents({"is_read": False})
    
    return {
        "total_users": total_users,
        "total_contacts": total_contacts,
        "total_projects": total_projects,
        "pending_projects": pending_projects,
        "in_progress_projects": in_progress_projects,
        "completed_projects": completed_projects,
        "total_messages": total_messages,
        "unread_messages": unread_messages
    }


# ==================== PDF GENERATION ====================

def generate_budget_pdf(project: dict, user: dict, is_invoice: bool = False):
    """Generate a professional PDF for budget/invoice"""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Colors
    primary = HexColor('#1e3a5f')
    secondary = HexColor('#3b82f6')
    gray = HexColor('#64748b')
    light_gray = HexColor('#f1f5f9')
    green = HexColor('#22c55e')
    
    # Header background
    c.setFillColor(primary)
    c.rect(0, height - 120, width, 120, fill=True, stroke=False)
    
    # Logo text
    c.setFillColor(HexColor('#ffffff'))
    c.setFont("Helvetica-Bold", 28)
    c.drawString(50, height - 60, "</> Andre Dev")
    c.setFont("Helvetica", 11)
    c.drawString(50, height - 80, "Agência de Desenvolvimento Web & Mobile")
    
    # Document type
    doc_type = "FATURA" if is_invoice else "ORÇAMENTO"
    c.setFont("Helvetica-Bold", 20)
    c.drawRightString(width - 50, height - 55, doc_type)
    
    # Document number
    doc_num = f"{'FAT' if is_invoice else 'ORC'}-{project['id'][:8].upper()}"
    c.setFont("Helvetica", 11)
    c.drawRightString(width - 50, height - 75, f"Nº: {doc_num}")
    c.drawRightString(width - 50, height - 90, f"Data: {datetime.now().strftime('%d/%m/%Y')}")
    
    # Reset to black
    c.setFillColor(HexColor('#1e293b'))
    
    # Client info box
    y_pos = height - 170
    c.setFillColor(light_gray)
    c.roundRect(50, y_pos - 80, (width - 100) / 2 - 10, 90, 8, fill=True, stroke=False)
    
    c.setFillColor(gray)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(60, y_pos - 5, "CLIENTE")
    c.setFillColor(HexColor('#1e293b'))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(60, y_pos - 25, user.get('name', 'N/A'))
    c.setFont("Helvetica", 10)
    c.drawString(60, y_pos - 42, user.get('email', 'N/A'))
    if user.get('company'):
        c.drawString(60, y_pos - 57, user.get('company'))
    
    # Project info box
    c.setFillColor(light_gray)
    c.roundRect(width / 2 + 10, y_pos - 80, (width - 100) / 2 - 10, 90, 8, fill=True, stroke=False)
    
    c.setFillColor(gray)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(width / 2 + 20, y_pos - 5, "PROJETO")
    c.setFillColor(HexColor('#1e293b'))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(width / 2 + 20, y_pos - 25, project.get('name', 'N/A'))
    c.setFont("Helvetica", 10)
    project_types = {"web": "Website", "android": "Android", "ios": "iOS"}
    c.drawString(width / 2 + 20, y_pos - 42, f"Tipo: {project_types.get(project.get('project_type', ''), project.get('project_type', 'N/A'))}")
    status_labels = {"pending": "Pendente", "in_progress": "Em Progresso", "completed": "Concluído"}
    c.drawString(width / 2 + 20, y_pos - 57, f"Estado: {status_labels.get(project.get('status', ''), project.get('status', 'N/A'))}")
    
    # Description section
    y_pos = height - 290
    c.setFillColor(HexColor('#1e293b'))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_pos, "Descrição do Projeto")
    c.setFont("Helvetica", 10)
    
    # Word wrap for description
    description = project.get('description', 'Sem descrição')
    max_width = width - 100
    words = description.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + " " + word if current_line else word
        if c.stringWidth(test_line, "Helvetica", 10) < max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    y_pos -= 20
    for line in lines[:5]:  # Max 5 lines
        c.drawString(50, y_pos, line)
        y_pos -= 15
    
    # Budget table
    y_pos -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_pos, "Valores")
    
    y_pos -= 25
    # Table header
    c.setFillColor(primary)
    c.roundRect(50, y_pos - 5, width - 100, 25, 4, fill=True, stroke=False)
    c.setFillColor(HexColor('#ffffff'))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, y_pos + 3, "Descrição")
    c.drawRightString(width - 60, y_pos + 3, "Valor")
    
    # Table rows
    y_pos -= 35
    c.setFillColor(HexColor('#1e293b'))
    c.setFont("Helvetica", 10)
    
    budget_value = project.get('budget', '0')
    if project.get('budget_status') == 'counter_proposal' and project.get('counter_proposal'):
        # Show original and counter proposal
        c.drawString(60, y_pos, "Orçamento Original")
        c.setFillColor(gray)
        c.drawRightString(width - 60, y_pos, budget_value)
        y_pos -= 25
        c.setFillColor(HexColor('#1e293b'))
        c.drawString(60, y_pos, "Contraproposta")
        c.setFillColor(secondary)
        c.setFont("Helvetica-Bold", 11)
        c.drawRightString(width - 60, y_pos, project.get('counter_proposal'))
        budget_value = project.get('counter_proposal')
    else:
        c.drawString(60, y_pos, "Desenvolvimento do Projeto")
        c.drawRightString(width - 60, y_pos, budget_value)
    
    # Total
    y_pos -= 35
    c.setFillColor(light_gray)
    c.roundRect(50, y_pos - 5, width - 100, 30, 4, fill=True, stroke=False)
    c.setFillColor(HexColor('#1e293b'))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(60, y_pos + 5, "TOTAL")
    c.setFillColor(green)
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(width - 60, y_pos + 5, budget_value)
    
    # Notes
    if project.get('admin_notes'):
        y_pos -= 50
        c.setFillColor(HexColor('#1e293b'))
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y_pos, "Notas:")
        c.setFont("Helvetica", 10)
        c.drawString(50, y_pos - 18, project.get('admin_notes', '')[:100])
    
    # Footer
    c.setFillColor(gray)
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, 50, "Andre Dev - Agência de Desenvolvimento Web & Mobile")
    c.drawCentredString(width / 2, 38, "contacto@andredev.pt | +351 912 345 678 | Lisboa, Portugal")
    c.drawCentredString(width / 2, 26, f"Documento gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
    
    c.save()
    buffer.seek(0)
    return buffer

@api_router.get("/projects/{project_id}/pdf")
async def download_project_pdf(
    project_id: str,
    doc_type: str = "budget",
    current_user: dict = Depends(get_current_user)
):
    """Download project budget/invoice as PDF"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Check permission
    if current_user["role"] != "admin" and project["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    user = await db.users.find_one({"id": project["user_id"]}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    
    is_invoice = doc_type == "invoice"
    pdf_buffer = generate_budget_pdf(project, user, is_invoice)
    
    filename = f"{'fatura' if is_invoice else 'orcamento'}_{project['name'].replace(' ', '_')}_{project_id[:8]}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ==================== STRIPE PAYMENT ====================

@api_router.post("/projects/{project_id}/create-payment")
async def create_payment_intent(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Create a Stripe payment intent for a project"""
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Pagamentos não configurados")
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    if project["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    if project.get("budget_status") != "accepted":
        raise HTTPException(status_code=400, detail="Orçamento não aprovado")
    
    # Parse budget value
    budget = project.get("counter_proposal") or project.get("budget", "0")
    # Remove currency symbols and convert to cents
    amount_str = budget.replace("€", "").replace("$", "").replace(",", ".").strip()
    try:
        amount = int(float(amount_str) * 100)  # Convert to cents
    except ValueError:
        raise HTTPException(status_code=400, detail="Valor do orçamento inválido")
    
    if amount < 50:  # Stripe minimum is 50 cents
        raise HTTPException(status_code=400, detail="Valor mínimo é €0.50")
    
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="eur",
            metadata={
                "project_id": project_id,
                "project_name": project["name"],
                "user_id": current_user["id"],
                "user_email": current_user["email"]
            }
        )
        
        return {
            "client_secret": intent.client_secret,
            "amount": amount / 100
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/projects/{project_id}/confirm-payment")
async def confirm_payment(
    project_id: str,
    payment_intent_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Confirm payment and update project status"""
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Pagamentos não configurados")
    
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    if project["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if intent.status == "succeeded":
            # Update project with payment info
            await db.projects.update_one(
                {"id": project_id},
                {"$set": {
                    "payment_status": "paid",
                    "payment_id": payment_intent_id,
                    "payment_date": datetime.now(timezone.utc).isoformat(),
                    "status": "in_progress",  # Auto-start project after payment
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Notify admin
            admin = await db.users.find_one({"role": "admin"}, {"_id": 0})
            if admin:
                budget = project.get("counter_proposal") or project.get("budget", "0")
                email_content = f'''
                    <p style="font-size: 16px;">Pagamento recebido!</p>
                    <div style="background: linear-gradient(145deg, #dcfce7 0%, #bbf7d0 100%); border-radius: 12px; padding: 20px; margin: 20px 0; text-align: center;">
                        <span style="font-size: 40px;">💰</span>
                        <p style="color: #166534; font-size: 18px; font-weight: 600; margin: 10px 0 0 0;">Pagamento Confirmado!</p>
                    </div>
                    <table style="width: 100%; border-collapse: separate; border-spacing: 0; margin: 25px 0; background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%); border-radius: 12px; overflow: hidden;">
                        <tr style="border-bottom: 1px solid #e2e8f0;">
                            <td style="padding: 16px 20px; width: 40px;">👤</td>
                            <td style="padding: 16px 0;"><span style="color: #64748b; font-size: 12px;">CLIENTE</span><br><strong>{current_user["name"]}</strong></td>
                        </tr>
                        <tr style="border-bottom: 1px solid #e2e8f0;">
                            <td style="padding: 16px 20px;">📁</td>
                            <td style="padding: 16px 0;"><span style="color: #64748b; font-size: 12px;">PROJETO</span><br><strong>{project["name"]}</strong></td>
                        </tr>
                        <tr>
                            <td style="padding: 16px 20px;">💰</td>
                            <td style="padding: 16px 0;"><span style="color: #64748b; font-size: 12px;">VALOR PAGO</span><br><strong style="color: #22c55e; font-size: 18px;">{budget}</strong></td>
                        </tr>
                    </table>
                    <p>O projeto foi iniciado automaticamente.</p>
                '''
                await send_email(
                    to_email=admin["email"],
                    subject=f"💰 Pagamento Recebido - {project['name']}",
                    html_content=get_base_email_template("Pagamento Recebido", email_content)
                )
            
            return {"status": "paid", "message": "Pagamento confirmado com sucesso"}
        else:
            return {"status": intent.status, "message": "Pagamento pendente"}
            
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Stripe Webhook endpoint
@api_router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events for payment confirmation"""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # If no webhook secret, just log and return (for testing)
    if not webhook_secret:
        logger.warning("Stripe webhook secret not configured")
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid payload")
    else:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    event_type = event.get('type', '')
    logger.info(f"Stripe webhook received: {event_type}")
    
    if event_type == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        payment_id = payment_intent['id']
        
        # Find project with this payment intent
        project = await db.projects.find_one({"payment_id": payment_id})
        
        if project:
            # Update project status
            await db.projects.update_one(
                {"id": project["id"]},
                {"$set": {
                    "payment_status": "paid",
                    "payment_confirmed_at": datetime.now(timezone.utc).isoformat(),
                    "status": "in_progress",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            logger.info(f"Payment confirmed for project {project['id']}")
            
            # Send confirmation email to client
            try:
                client = await db.users.find_one({"id": project.get("client_id", project.get("user_id"))})
                if client:
                    amount = payment_intent.get('amount', 0) / 100
                    await send_email(
                        to_email=client["email"],
                        subject="💳 Pagamento Confirmado - Andre Dev",
                        html_content=f"""
                        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                            <h2 style="color: #1a1a2e;">Pagamento Confirmado!</h2>
                            <p>Olá {client['name']},</p>
                            <p>O seu pagamento de <strong>€{amount:.2f}</strong> para o projeto <strong>{project['name']}</strong> foi confirmado com sucesso.</p>
                            <p>O projeto foi iniciado e em breve entraremos em contacto.</p>
                            <br>
                            <p>Obrigado pela confiança!</p>
                            <p>Equipa Andre Dev</p>
                        </div>
                        """
                    )
            except Exception as e:
                logger.error(f"Error sending payment confirmation email: {e}")
        else:
            logger.warning(f"No project found for payment intent {payment_id}")
    
    elif event_type == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        payment_id = payment_intent['id']
        
        project = await db.projects.find_one({"payment_id": payment_id})
        if project:
            await db.projects.update_one(
                {"id": project["id"]},
                {"$set": {
                    "payment_status": "failed",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            logger.info(f"Payment failed for project {project['id']}")
            
            # Notify client about failed payment
            try:
                await create_notification(
                    user_id=project.get("client_id", project.get("user_id")),
                    title="Pagamento Falhou",
                    message=f"O pagamento para o projeto {project['name']} falhou. Por favor, tente novamente.",
                    notification_type="warning",
                    link=f"/dashboard/projects/{project['id']}"
                )
            except:
                pass
    
    elif event_type == 'charge.refunded':
        # Handle refunds
        charge = event['data']['object']
        payment_id = charge.get('payment_intent')
        
        if payment_id:
            project = await db.projects.find_one({"payment_id": payment_id})
            if project:
                refund_amount = charge.get('amount_refunded', 0) / 100
                await db.projects.update_one(
                    {"id": project["id"]},
                    {"$set": {
                        "payment_status": "refunded",
                        "refund_amount": refund_amount,
                        "refund_date": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                logger.info(f"Refund processed for project {project['id']}: €{refund_amount}")
                
                # Notify client about refund
                try:
                    client = await db.users.find_one({"id": project.get("client_id", project.get("user_id"))})
                    if client:
                        await send_email(
                            to_email=client["email"],
                            subject="💸 Reembolso Processado - Andre Dev",
                            html_content=f"""
                            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                                <h2 style="color: #1a1a2e;">Reembolso Processado</h2>
                                <p>Olá {client['name']},</p>
                                <p>O reembolso de <strong>€{refund_amount:.2f}</strong> para o projeto <strong>{project['name']}</strong> foi processado com sucesso.</p>
                                <p>O valor será creditado na sua conta em 5-10 dias úteis.</p>
                                <br>
                                <p>Equipa Andre Dev</p>
                            </div>
                            """
                        )
                        await create_notification(
                            user_id=project.get("client_id", project.get("user_id")),
                            title="Reembolso Processado",
                            message=f"Reembolso de €{refund_amount:.2f} processado para o projeto {project['name']}",
                            notification_type="info",
                            link=f"/dashboard/projects/{project['id']}"
                        )
                except Exception as e:
                    logger.error(f"Error sending refund notification: {e}")
    
    elif event_type == 'charge.dispute.created':
        # Handle disputes
        dispute = event['data']['object']
        charge_id = dispute.get('charge')
        
        # Find project by charge
        logger.warning(f"Dispute created for charge {charge_id}")
        
        # Notify admin about dispute
        admin = await db.users.find_one({"role": "admin"}, {"_id": 0, "id": 1})
        if admin:
            await create_notification(
                user_id=admin["id"],
                title="⚠️ Disputa de Pagamento",
                message=f"Uma disputa foi aberta para o pagamento {charge_id}. Ação necessária!",
                notification_type="warning",
                link="/admin/dashboard"
            )
    
    return {"status": "success"}


# ==================== ANALYTICS/STATS ====================

@api_router.get("/admin/analytics")
async def get_analytics(admin: dict = Depends(get_admin_user)):
    """Get detailed analytics for dashboard charts"""
    now = datetime.now(timezone.utc)
    
    # Projects by month (last 6 months)
    projects_by_month = []
    for i in range(5, -1, -1):
        month_start = now.replace(day=1) - timedelta(days=i*30)
        month_end = month_start + timedelta(days=30)
        count = await db.projects.count_documents({
            "created_at": {
                "$gte": month_start.isoformat(),
                "$lt": month_end.isoformat()
            }
        })
        projects_by_month.append({
            "month": month_start.strftime("%b"),
            "count": count
        })
    
    # Projects by type
    web_count = await db.projects.count_documents({"project_type": "web"})
    android_count = await db.projects.count_documents({"project_type": "android"})
    ios_count = await db.projects.count_documents({"project_type": "ios"})
    
    # Budget status distribution
    pending_budget = await db.projects.count_documents({"budget_status": "pending"})
    accepted_budget = await db.projects.count_documents({"budget_status": "accepted"})
    counter_budget = await db.projects.count_documents({"budget_status": "counter_proposal"})
    
    # Recent activity
    recent_projects = await db.projects.find({}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    recent_contacts = await db.contacts.find({}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "projects_by_month": projects_by_month,
        "projects_by_type": [
            {"type": "Web", "count": web_count},
            {"type": "Android", "count": android_count},
            {"type": "iOS", "count": ios_count}
        ],
        "budget_distribution": [
            {"status": "Pendente", "count": pending_budget},
            {"status": "Aprovado", "count": accepted_budget},
            {"status": "Contraproposta", "count": counter_budget}
        ],
        "recent_projects": recent_projects,
        "recent_contacts": recent_contacts
    }


# ==================== ADVANCED ANALYTICS ====================

@api_router.get("/admin/analytics/revenue")
async def get_revenue_analytics(admin: dict = Depends(get_admin_user)):
    """Get revenue analytics with detailed breakdown"""
    now = datetime.now(timezone.utc)
    
    # Revenue by month (last 12 months)
    revenue_by_month = []
    for i in range(11, -1, -1):
        month_start = now.replace(day=1) - timedelta(days=i*30)
        month_end = month_start + timedelta(days=30)
        
        # Get paid projects in this month
        paid_projects = await db.projects.find({
            "payment_status": "paid",
            "payment_date": {
                "$gte": month_start.isoformat(),
                "$lt": month_end.isoformat()
            }
        }, {"_id": 0, "official_value": 1}).to_list(100)
        
        # Calculate total revenue
        total = 0
        for p in paid_projects:
            value_str = p.get("official_value", "0")
            try:
                # Remove currency symbols and convert
                value = float(value_str.replace("€", "").replace(",", ".").strip())
                total += value
            except:
                pass
        
        revenue_by_month.append({
            "month": month_start.strftime("%b %Y"),
            "revenue": total,
            "projects": len(paid_projects)
        })
    
    # Total revenue
    all_paid = await db.projects.find({"payment_status": "paid"}, {"_id": 0, "official_value": 1}).to_list(1000)
    total_revenue = 0
    for p in all_paid:
        value_str = p.get("official_value", "0")
        try:
            value = float(value_str.replace("€", "").replace(",", ".").strip())
            total_revenue += value
        except:
            pass
    
    # Pending payments
    pending_payments = await db.projects.find({
        "budget_status": "accepted",
        "payment_status": {"$ne": "paid"}
    }, {"_id": 0, "official_value": 1}).to_list(100)
    
    pending_revenue = 0
    for p in pending_payments:
        value_str = p.get("official_value", "0")
        try:
            value = float(value_str.replace("€", "").replace(",", ".").strip())
            pending_revenue += value
        except:
            pass
    
    # Conversion rate
    total_projects = await db.projects.count_documents({})
    paid_projects_count = await db.projects.count_documents({"payment_status": "paid"})
    conversion_rate = (paid_projects_count / total_projects * 100) if total_projects > 0 else 0
    
    return {
        "revenue_by_month": revenue_by_month,
        "total_revenue": total_revenue,
        "pending_revenue": pending_revenue,
        "paid_projects": paid_projects_count,
        "conversion_rate": round(conversion_rate, 1),
        "average_project_value": round(total_revenue / paid_projects_count, 2) if paid_projects_count > 0 else 0
    }


# ==================== NOTIFICATIONS SYSTEM ====================

@api_router.get("/notifications")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    """Get notifications for the current user"""
    notifications = await db.notifications.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(50).to_list(50)
    
    unread_count = await db.notifications.count_documents({
        "user_id": current_user["id"],
        "read": False
    })
    
    return {
        "notifications": notifications,
        "unread_count": unread_count
    }


@api_router.post("/notifications/mark-read")
async def mark_notifications_read(
    notification_ids: List[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Mark notifications as read"""
    if notification_ids:
        await db.notifications.update_many(
            {"id": {"$in": notification_ids}, "user_id": current_user["id"]},
            {"$set": {"read": True}}
        )
    else:
        # Mark all as read
        await db.notifications.update_many(
            {"user_id": current_user["id"]},
            {"$set": {"read": True}}
        )
    
    return {"status": "success"}


@api_router.post("/notifications/mark-all-read")
async def mark_all_notifications_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read"""
    await db.notifications.update_many(
        {"user_id": current_user["id"]},
        {"$set": {"read": True}}
    )
    return {"status": "success"}


async def create_notification(user_id: str, title: str, message: str, notification_type: str = "info", link: str = None):
    """Helper function to create notifications"""
    notification = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": title,
        "message": message,
        "type": notification_type,  # info, success, warning, payment
        "link": link,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification)
    return notification


# ==================== CHAT SYSTEM ====================

@api_router.get("/projects/{project_id}/chat")
async def get_project_chat(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get chat messages for a project"""
    # Verify access
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    if current_user["role"] != "admin" and project.get("client_id", project.get("user_id")) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    messages = await db.chat_messages.find(
        {"project_id": project_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(500)
    
    # Mark messages as read
    await db.chat_messages.update_many(
        {"project_id": project_id, "sender_id": {"$ne": current_user["id"]}, "read": False},
        {"$set": {"read": True}}
    )
    
    return {"messages": messages, "project": project}


@api_router.post("/projects/{project_id}/chat")
async def send_chat_message(
    project_id: str,
    content: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    """Send a chat message in a project"""
    # Verify access
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    if current_user["role"] != "admin" and project.get("client_id", project.get("user_id")) != current_user["id"]:
        raise HTTPException(status_code=403, detail="Sem permissão")
    
    message = {
        "id": str(uuid.uuid4()),
        "project_id": project_id,
        "sender_id": current_user["id"],
        "sender_name": current_user["name"],
        "sender_role": current_user["role"],
        "content": content,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.chat_messages.insert_one(message)
    
    # Create notification for the other party
    if current_user["role"] == "admin":
        # Notify client
        await create_notification(
            user_id=project.get("client_id", project.get("user_id")),
            title="Nova mensagem",
            message=f"Nova mensagem no projeto {project['name']}",
            notification_type="info",
            link=f"/dashboard/projects/{project_id}"
        )
    else:
        # Notify admin
        admin = await db.users.find_one({"role": "admin"}, {"_id": 0, "id": 1})
        if admin:
            await create_notification(
                user_id=admin["id"],
                title="Nova mensagem",
                message=f"Nova mensagem de {current_user['name']} no projeto {project['name']}",
                notification_type="info",
                link=f"/admin/projects/{project_id}"
            )
    
    # Remove _id before returning
    message.pop("_id", None)
    return message


@api_router.get("/projects/{project_id}/chat/unread")
async def get_unread_chat_count(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get unread message count for a project"""
    count = await db.chat_messages.count_documents({
        "project_id": project_id,
        "sender_id": {"$ne": current_user["id"]},
        "read": False
    })
    return {"unread_count": count}


# ==================== CMS ROUTES ====================

# Default content for the site
DEFAULT_HERO = {
    "tagline": "Agência de Desenvolvimento",
    "title": "Criamos o seu",
    "highlight": "futuro digital",
    "description": "Desenvolvemos websites e aplicações móveis que transformam ideias em experiências digitais extraordinárias. Android, iOS e Web.",
    "cta_text": "Começar Projeto",
    "stats": [
        {"value": "50+", "label": "Projetos Entregues"},
        {"value": "100%", "label": "Clientes Satisfeitos"},
        {"value": "5+", "label": "Anos de Experiência"}
    ]
}

DEFAULT_SERVICES = [
    {
        "id": "1",
        "icon": "Monitor",
        "title": "Desenvolvimento Web",
        "description": "Websites modernos, responsivos e otimizados para SEO. Desde landing pages a plataformas complexas.",
        "features": ["React & Vue.js", "E-commerce", "Dashboards", "APIs RESTful"]
    },
    {
        "id": "2",
        "icon": "Smartphone",
        "title": "Aplicações Android",
        "description": "Apps nativas e híbridas para Android com performance excepcional e design intuitivo.",
        "features": ["Kotlin & Java", "Material Design", "Play Store", "Firebase"]
    },
    {
        "id": "3",
        "icon": "Code2",
        "title": "Aplicações iOS",
        "description": "Desenvolvimento de apps para iPhone e iPad com a qualidade que a Apple exige.",
        "features": ["Swift & SwiftUI", "Human Interface", "App Store", "Core Data"]
    },
    {
        "id": "4",
        "icon": "Rocket",
        "title": "Soluções Completas",
        "description": "Do conceito ao lançamento, acompanhamos todo o processo de desenvolvimento do seu projeto.",
        "features": ["UX/UI Design", "Backend", "DevOps", "Manutenção"]
    }
]

DEFAULT_PORTFOLIO = [
    {
        "id": "1",
        "title": "E-Commerce Platform",
        "description": "Plataforma completa de e-commerce com pagamentos integrados",
        "image_url": "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=600",
        "category": "Web",
        "technologies": ["React", "Node.js", "MongoDB"],
        "link": None
    },
    {
        "id": "2",
        "title": "App de Fitness",
        "description": "Aplicação móvel para tracking de exercícios e nutrição",
        "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=600",
        "category": "Mobile",
        "technologies": ["React Native", "Firebase"],
        "link": None
    },
    {
        "id": "3",
        "title": "Sistema de Gestão",
        "description": "Dashboard completo para gestão empresarial",
        "image_url": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=600",
        "category": "Web",
        "technologies": ["Vue.js", "Python"],
        "link": None
    },
    {
        "id": "4",
        "title": "App de Delivery",
        "description": "Aplicação de entregas com tracking em tempo real",
        "image_url": "https://images.unsplash.com/photo-1526367790999-0150786686a2?w=600",
        "category": "Mobile",
        "technologies": ["Flutter", "Node.js"],
        "link": None
    }
]

DEFAULT_TESTIMONIALS = [
    {
        "id": "1",
        "name": "Maria Santos",
        "role": "CEO, TechStart",
        "image": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200",
        "text": "A Andre Dev transformou completamente a nossa presença digital. O website que desenvolveram superou todas as expectativas."
    },
    {
        "id": "2",
        "name": "João Ferreira",
        "role": "Fundador, AppSolutions",
        "image": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200",
        "text": "Profissionalismo e qualidade excecional. A app que criaram para nós tem recebido feedback incrível dos utilizadores."
    }
]

DEFAULT_CONTACT_INFO = {
    "email": "contacto@andredev.pt",
    "phone": "+351 912 345 678",
    "location": "Lisboa, Portugal"
}

# ==================== EMAIL TEMPLATES ROUTES ====================

@api_router.get("/admin/email-templates")
async def get_email_templates(admin: dict = Depends(get_admin_user)):
    """Get all email templates"""
    templates_doc = await db.email_templates.find_one({"type": "email_templates"}, {"_id": 0})
    
    if templates_doc and "templates" in templates_doc:
        return {"templates": templates_doc["templates"]}
    
    # Return default templates
    return {"templates": list(DEFAULT_EMAIL_TEMPLATES.values())}

@api_router.put("/admin/email-templates")
async def update_email_templates(data: EmailTemplatesUpdate, admin: dict = Depends(get_admin_user)):
    """Update email templates"""
    await db.email_templates.update_one(
        {"type": "email_templates"},
        {
            "$set": {
                "type": "email_templates",
                "templates": [t.model_dump() for t in data.templates],
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    return {"message": "Templates atualizados com sucesso"}

@api_router.post("/admin/email-templates/reset")
async def reset_email_templates(admin: dict = Depends(get_admin_user)):
    """Reset email templates to defaults"""
    await db.email_templates.delete_one({"type": "email_templates"})
    return {"message": "Templates restaurados para os valores padrão"}

# ==================== CONTENT ROUTES ====================

@api_router.get("/content")
async def get_site_content():
    """Get all site content (public)"""
    content = await db.site_content.find_one({"type": "main"}, {"_id": 0})
    
    if not content:
        return {
            "hero": DEFAULT_HERO,
            "services": DEFAULT_SERVICES,
            "portfolio": DEFAULT_PORTFOLIO,
            "testimonials": DEFAULT_TESTIMONIALS,
            "contact_info": DEFAULT_CONTACT_INFO
        }
    
    return {
        "hero": content.get("hero", DEFAULT_HERO),
        "services": content.get("services", DEFAULT_SERVICES),
        "portfolio": content.get("portfolio", DEFAULT_PORTFOLIO),
        "testimonials": content.get("testimonials", DEFAULT_TESTIMONIALS),
        "contact_info": content.get("contact_info", DEFAULT_CONTACT_INFO)
    }

@api_router.get("/admin/content")
async def get_admin_content(admin: dict = Depends(get_admin_user)):
    """Get site content for editing"""
    content = await db.site_content.find_one({"type": "main"}, {"_id": 0})
    
    if not content:
        return {
            "hero": DEFAULT_HERO,
            "services": DEFAULT_SERVICES,
            "portfolio": DEFAULT_PORTFOLIO,
            "testimonials": DEFAULT_TESTIMONIALS,
            "contact_info": DEFAULT_CONTACT_INFO
        }
    
    return {
        "hero": content.get("hero", DEFAULT_HERO),
        "services": content.get("services", DEFAULT_SERVICES),
        "portfolio": content.get("portfolio", DEFAULT_PORTFOLIO),
        "testimonials": content.get("testimonials", DEFAULT_TESTIMONIALS),
        "contact_info": content.get("contact_info", DEFAULT_CONTACT_INFO)
    }

@api_router.put("/admin/content/hero")
async def update_hero(hero: HeroContent, admin: dict = Depends(get_admin_user)):
    """Update hero section"""
    await db.site_content.update_one(
        {"type": "main"},
        {"$set": {"hero": hero.model_dump(), "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    return {"message": "Hero atualizado com sucesso"}

@api_router.put("/admin/content/services")
async def update_services(services: List[ServiceItem], admin: dict = Depends(get_admin_user)):
    """Update services section"""
    services_data = []
    for i, service in enumerate(services):
        s = service.model_dump()
        if not s.get("id"):
            s["id"] = str(i + 1)
        services_data.append(s)
    
    await db.site_content.update_one(
        {"type": "main"},
        {"$set": {"services": services_data, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    return {"message": "Serviços atualizados com sucesso"}

@api_router.put("/admin/content/portfolio")
async def update_portfolio(portfolio: List[PortfolioItemCreate], admin: dict = Depends(get_admin_user)):
    """Update portfolio section"""
    portfolio_data = []
    for i, item in enumerate(portfolio):
        p = item.model_dump()
        p["id"] = str(i + 1)
        portfolio_data.append(p)
    
    await db.site_content.update_one(
        {"type": "main"},
        {"$set": {"portfolio": portfolio_data, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    return {"message": "Portfolio atualizado com sucesso"}

@api_router.put("/admin/content/testimonials")
async def update_testimonials(testimonials: List[TestimonialItem], admin: dict = Depends(get_admin_user)):
    """Update testimonials section"""
    testimonials_data = []
    for i, item in enumerate(testimonials):
        t = item.model_dump()
        if not t.get("id"):
            t["id"] = str(i + 1)
        testimonials_data.append(t)
    
    await db.site_content.update_one(
        {"type": "main"},
        {"$set": {"testimonials": testimonials_data, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    return {"message": "Testemunhos atualizados com sucesso"}

@api_router.put("/admin/content/contact-info")
async def update_contact_info(contact_info: ContactInfo, admin: dict = Depends(get_admin_user)):
    """Update contact info"""
    await db.site_content.update_one(
        {"type": "main"},
        {"$set": {"contact_info": contact_info.model_dump(), "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    return {"message": "Informação de contacto atualizada com sucesso"}


# ==================== TRANSLATION ROUTES ====================

class TranslateRequest(BaseModel):
    text: str
    source_lang: str = "auto"  # auto, pt, en
    target_lang: str  # pt, en

class TranslateResponse(BaseModel):
    translated_text: str
    source_lang: str
    target_lang: str

class BulkTranslateRequest(BaseModel):
    texts: List[str]
    source_lang: str = "auto"
    target_lang: str

from deep_translator import GoogleTranslator
from functools import lru_cache
from datetime import datetime, timedelta

# Translation cache (in-memory)
translation_cache = {}
CACHE_TTL = timedelta(hours=24)  # Cache por 24 horas

def get_cached_translation(text: str, source: str, target: str) -> Optional[str]:
    """Get translation from cache"""
    cache_key = f"{text}_{source}_{target}"
    if cache_key in translation_cache:
        cached_data = translation_cache[cache_key]
        # Check if cache is still valid
        if datetime.now(timezone.utc) - cached_data['timestamp'] < CACHE_TTL:
            return cached_data['translation']
        else:
            # Remove expired cache
            del translation_cache[cache_key]
    return None

def set_cached_translation(text: str, source: str, target: str, translation: str):
    """Save translation to cache"""
    cache_key = f"{text}_{source}_{target}"
    translation_cache[cache_key] = {
        'translation': translation,
        'timestamp': datetime.now(timezone.utc)
    }

@api_router.post("/translate", response_model=TranslateResponse)
async def translate_text(request: TranslateRequest):
    """Translate text between languages with caching"""
    try:
        from deep_translator import GoogleTranslator
        
        # Map language codes
        lang_map = {
            "pt": "pt",
            "en": "en",
            "es": "es",
            "fr": "fr",
            "auto": "auto"
        }
        
        source = lang_map.get(request.source_lang, "auto")
        target = lang_map.get(request.target_lang, "en")
        
        # Check cache first
        cached = get_cached_translation(request.text, source, target)
        if cached:
            logger.info(f"Translation cache hit for: {request.text[:50]}")
            return TranslateResponse(
                translated_text=cached,
                source_lang=request.source_lang,
                target_lang=request.target_lang
            )
        
        # Create translator
        translator = GoogleTranslator(source=source, target=target)
        
        # Translate
        translated = translator.translate(request.text)
        
        # Save to cache
        set_cached_translation(request.text, source, target, translated)
        
        return TranslateResponse(
            translated_text=translated,
            source_lang=request.source_lang,
            target_lang=request.target_lang
        )
    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na tradução: {str(e)}")

@api_router.post("/translate/bulk")
async def translate_bulk(request: BulkTranslateRequest):
    """Translate multiple texts at once"""
    try:
        from deep_translator import GoogleTranslator
        
        lang_map = {
            "pt": "pt",
            "en": "en",
            "es": "es",
            "fr": "fr",
            "auto": "auto"
        }
        
        source = lang_map.get(request.source_lang, "auto")
        target = lang_map.get(request.target_lang, "en")
        
        translator = GoogleTranslator(source=source, target=target)
        
        # Translate all texts
        translations = []
        for text in request.texts:
            try:
                translated = translator.translate(text)
                translations.append({
                    "original": text,
                    "translated": translated,
                    "success": True
                })
            except Exception as e:
                translations.append({
                    "original": text,
                    "translated": text,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "translations": translations,
            "source_lang": request.source_lang,
            "target_lang": request.target_lang
        }
    except Exception as e:
        logger.error(f"Bulk translation error: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na tradução: {str(e)}")

@api_router.get("/translations/{lang}")
async def get_translations(lang: str):
    """Get all translations for a specific language"""
    try:
        # Check if we have cached translations in database
        cached = await db.translations.find_one({"language": lang}, {"_id": 0})
        if cached:
            return cached
        
        # Return empty if not found
        return {"language": lang, "translations": {}}
    except Exception as e:
        logger.error(f"Error fetching translations: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar traduções")

@api_router.post("/translations/{lang}")
async def save_translations(lang: str, translations: dict, admin: dict = Depends(get_admin_user)):
    """Save translations for a language (Admin only)"""
    try:
        await db.translations.update_one(
            {"language": lang},
            {
                "$set": {
                    "language": lang,
                    "translations": translations,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            },
            upsert=True
        )
        return {"message": f"Traduções para {lang} guardadas com sucesso"}
    except Exception as e:
        logger.error(f"Error saving translations: {e}")
        raise HTTPException(status_code=500, detail="Erro ao guardar traduções")


@api_router.get("/translations/cache/stats")
async def get_cache_stats():
    """Get translation cache statistics"""
    total_cached = len(translation_cache)
    valid_cache = sum(
        1 for data in translation_cache.values()
        if datetime.now(timezone.utc) - data['timestamp'] < CACHE_TTL
    )
    return {
        "total_cached": total_cached,
        "valid_cached": valid_cache,
        "expired": total_cached - valid_cache,
        "cache_ttl_hours": CACHE_TTL.total_seconds() / 3600
    }

@api_router.post("/translations/cache/clear")
async def clear_translation_cache(admin: dict = Depends(get_admin_user)):
    """Clear translation cache (Admin only)"""
    translation_cache.clear()
    return {"message": "Cache de traduções limpo com sucesso", "items_removed": len(translation_cache)}


# ==================== CMS AUTO-TRANSLATION ====================

class CMSContentTranslate(BaseModel):
    content_type: str  # hero, services, testimonials, etc.
    content: dict  # Content to translate
    target_languages: List[str] = ["en", "es", "fr"]  # Languages to translate to

@api_router.post("/cms/auto-translate")
async def auto_translate_cms_content(
    request: CMSContentTranslate,
    admin: dict = Depends(get_admin_user)
):
    """Auto-translate CMS content to multiple languages"""
    try:
        from deep_translator import GoogleTranslator
        
        translations = {}
        source_lang = "pt"  # Assume Portuguese as source
        
        for target_lang in request.target_languages:
            if target_lang == source_lang:
                continue
            
            translated_content = {}
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            
            # Recursively translate all string values
            def translate_dict(obj, path=""):
                if isinstance(obj, dict):
                    result = {}
                    for key, value in obj.items():
                        result[key] = translate_dict(value, f"{path}.{key}")
                    return result
                elif isinstance(obj, list):
                    return [translate_dict(item, f"{path}[]") for item in obj]
                elif isinstance(obj, str) and len(obj) > 0:
                    try:
                        # Check cache first
                        cached = get_cached_translation(obj, source_lang, target_lang)
                        if cached:
                            return cached
                        
                        # Translate
                        translated = translator.translate(obj)
                        
                        # Save to cache
                        set_cached_translation(obj, source_lang, target_lang, translated)
                        
                        return translated
                    except Exception as e:
                        logger.error(f"Error translating '{obj}': {e}")
                        return obj
                else:
                    return obj
            
            translated_content = translate_dict(request.content)
            translations[target_lang] = translated_content
        
        return {
            "success": True,
            "content_type": request.content_type,
            "source_language": source_lang,
            "translations": translations
        }
    except Exception as e:
        logger.error(f"CMS auto-translation error: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na tradução: {str(e)}")

@api_router.post("/cms/save-multilang")
async def save_multilang_content(
    content_type: str,
    content_data: dict,
    admin: dict = Depends(get_admin_user)
):
    """Save multilingual CMS content"""
    try:
        # Save content for each language
        for lang, content in content_data.items():
            await db.cms_content.update_one(
                {
                    "type": content_type,
                    "language": lang
                },
                {
                    "$set": {
                        "type": content_type,
                        "language": lang,
                        "content": content,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                },
                upsert=True
            )
        
        return {
            "message": f"Conteúdo {content_type} salvo em {len(content_data)} idiomas",
            "languages": list(content_data.keys())
        }
    except Exception as e:
        logger.error(f"Error saving multilang content: {e}")
        raise HTTPException(status_code=500, detail="Erro ao salvar conteúdo")

@api_router.get("/cms/content/{content_type}")
async def get_cms_content(content_type: str, lang: str = "pt"):
    """Get CMS content for specific language"""
    try:
        content = await db.cms_content.find_one(
            {
                "type": content_type,
                "language": lang
            },
            {"_id": 0}
        )
        
        if content:
            return content
        
        # Fallback to Portuguese
        if lang != "pt":
            content = await db.cms_content.find_one(
                {
                    "type": content_type,
                    "language": "pt"
                },
                {"_id": 0}
            )
            if content:
                return content
        
        return {"type": content_type, "language": lang, "content": {}}
    except Exception as e:
        logger.error(f"Error fetching CMS content: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar conteúdo")


# Include the router
app.include_router(api_router)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
