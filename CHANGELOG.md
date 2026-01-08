# Changelog

Todas as mudanças notáveis do projeto serão documentadas neste arquivo.

## [2.0.0] - 2026-01-07

### 🎉 FASE 2 - Funcionalidades Intermediárias

#### ✨ Adicionado
- **Cartões de Crédito**
  - Cadastro completo de cartões com limite
  - Configuração de dias de fechamento e vencimento
  - Visualização de fatura atual
  - Controle de limite disponível e percentual de uso
  - Dashboard individual por cartão com detalhamento

- **Compras Parceladas**
  - Suporte a parcelamento de 2x até 24x
  - Criação automática de todas as parcelas
  - Controle de parcelas pagas e pendentes
  - Pagamento/despagamento manual de parcelas
  - Parcelamento em débito e crédito
  - Visualização de comprometimento futuro (3 meses)

- **Transferências entre Contas**
  - Interface para transferência rápida
  - Atualização automática de saldos
  - Histórico completo de transferências
  - Possibilidade de reversão/exclusão

- **Relatórios Avançados**
  - Gráfico de evolução mensal (últimos 6 meses)
  - Análise detalhada por categorias com percentuais
  - Visualização de comprometimento futuro
  - Comparativo receitas vs despesas

- **Sistema de Anexos**
  - Upload de comprovantes (imagens e PDFs)
  - Limite de 5MB por arquivo
  - Visualização direta dos anexos
  - Indicador visual de transações com anexo

#### 🔄 Modificado
- **Dashboard**
  - Adicionado card de Parcelas Pendentes
  - Seção de Cartões de Crédito
  - Alert de comprometimento futuro
  - Indicador de anexos nas transações
  
- **Formulário de Transações**
  - Opção de escolha entre débito e crédito
  - Checkbox para parcelamento
  - Campo de upload de anexo
  - Validações aprimoradas

- **Menu de Navegação**
  - Novos itens: Parcelas, Cartões, Transferências, Relatórios
  - Reorganização dos menus
  - Indicadores visuais de seção ativa

#### 🗄️ Banco de Dados
- Nova tabela: `credit_card`
- Nova tabela: `installment`
- Nova tabela: `transfer`
- Campos adicionados em `transaction`:
  - `credit_card_id`
  - `attachment`
  - `attachment_type`
- Novos relacionamentos entre tabelas

#### 🎨 Interface
- 9 novos templates HTML
- Gráficos adicionais nos relatórios
- Barras de progresso para limites de cartão
- Badges de status para parcelas
- Design responsivo aprimorado

## [1.0.0] - 2026-01-06

### 🚀 FASE 1 - Funcionalidades Essenciais

#### ✨ Funcionalidades Iniciais
- Sistema de autenticação (login/registro)
- Dashboard com visão geral financeira
- Cadastro de transações (receitas e despesas)
- Gerenciamento de contas bancárias
- Sistema de categorias
- Filtros avançados de transações
- Gráfico de despesas por categoria
- Últimas 10 transações no dashboard

#### 🎨 Design
- Interface moderna com Tailwind CSS
- Ícones FontAwesome
- Gráficos com Chart.js
- Design totalmente responsivo
- Cores indicativas por tipo de transação

#### 🔐 Segurança
- Senhas criptografadas
- Sessões seguras com Flask-Login
- Isolamento de dados por usuário
- Proteção contra SQL Injection

#### 🗄️ Banco de Dados
- Modelo inicial com SQLite
- Tabelas: User, Account, Category, Transaction
- Relacionamentos básicos
- Categorias padrão pré-definidas

---

## Formato do Changelog

Este changelog segue o formato [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).

### Tipos de Mudanças
- `✨ Adicionado` - Novas funcionalidades
- `🔄 Modificado` - Mudanças em funcionalidades existentes
- `🗑️ Removido` - Funcionalidades removidas
- `🐛 Corrigido` - Correção de bugs
- `🔒 Segurança` - Vulnerabilidades corrigidas
- `📝 Documentação` - Mudanças na documentação
- `⚡ Performance` - Melhorias de performance

## Próximas Versões

### [3.0.0] - Planejado (Fase 3)
- Metas financeiras
- Notificações de vencimentos
- Importação de extratos (OFX/CSV)
- Categorização inteligente
- Modo escuro
- Alertas por email
- Recorrências automáticas
- Múltiplas moedas
