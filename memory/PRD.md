# PRD - Andre Dev Agency Platform

## Original Problem Statement
Importar o projeto https://github.com/emanuelprogrammer1995-dev/Agency-Andre-Dev com MongoDB Atlas.

## Project Overview
Andre Dev é uma plataforma completa de agência de desenvolvimento web e mobile.

## Tech Stack
- **Backend**: FastAPI (Python)
- **Frontend**: React.js com Tailwind CSS
- **Database**: MongoDB Atlas
- **Pagamentos**: Stripe (PRODUÇÃO com Webhooks)
- **Email**: Resend (domínio verificado)
- **Auth**: JWT + 2FA (TOTP)
- **Segurança**: Rate Limiting, Audit Logs

## What's Been Implemented

### Date: 2026-02-24 (Initial Import)
- [x] Projeto importado do GitHub
- [x] MongoDB Atlas configurado

### Date: 2026-02-25 (Produção & Funcionalidades)
- [x] Stripe LIVE + Webhooks
- [x] Sistema de Notificações
- [x] Sistema de Chat
- [x] Analytics Avançado

### Date: 2026-02-25 (Segurança)
- [x] Rate Limiting (slowapi)
- [x] 2FA (Two-Factor Authentication)
- [x] Audit Logs

### Date: 2026-02-25 (Dark Mode Fix) ✅ NEW
- [x] **Problemas de contraste corrigidos**
  - Substituído `bg-white` por `bg-card` (adapta ao tema)
  - Substituído `text-primary` por `text-foreground` (adapta ao tema)
  - Botões CTA mudados de `bg-primary` para `bg-secondary` (melhor contraste)
  - Glass effect com variante dark: `rgba(30, 41, 59, 0.8)`
  
- [x] **Landing Page Dark Mode**
  - Header transparente com backdrop blur
  - Cards de serviços com fundo escuro
  - Botões com contraste adequado
  - Textos legíveis em todas as seções
  
- [x] **Dashboard Dark Mode**
  - Navbar com fundo escuro
  - Stats cards com bordas visíveis
  - Toggle de tema adicionado à navbar
  - Todos os textos com bom contraste

## Dark Mode Color Scheme
| Element | Light Mode | Dark Mode |
|---------|------------|-----------|
| Background | rgb(255, 255, 255) | rgb(11, 17, 30) |
| Card | rgb(255, 255, 255) | rgb(29, 40, 58) |
| Text | rgb(26, 26, 46) | rgb(248, 250, 252) |
| Glass | rgba(255, 255, 255, 0.7) | rgba(30, 41, 59, 0.8) |

## Test Results (Latest)
- Dark Mode Landing: 100%
- Dark Mode Dashboard: 100%
- Theme Toggle: 100%
- Text Readability: 100%
- **Overall: 100%**

## Status: PRODUÇÃO ✅

## URLs
- **Frontend**: https://agency-andre-dev.preview.emergentagent.com
- **API**: https://agency-andre-dev.preview.emergentagent.com/api/

## Backlog
- [ ] WebSockets para chat em tempo real
- [ ] Push notifications
- [ ] PWA (Progressive Web App)
