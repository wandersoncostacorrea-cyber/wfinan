# 💰 Gerenciador Financeiro Pessoal - FASE 2

Sistema web moderno e completo para gerenciamento de finanças pessoais desenvolvido com Python/Flask.

## 🎉 NOVIDADES DA FASE 2

### ✨ Funcionalidades Implementadas

#### 💳 **Cartões de Crédito**
- Cadastro ilimitado de cartões com limites personalizados
- Configuração de datas de fechamento e vencimento
- Visualização de fatura atual em tempo real
- Controle de limite disponível e percentual utilizado
- Dashboard individual por cartão

#### 📅 **Compras Parceladas**
- Parcelamento automático de compras (até 24x)
- Controle de parcelas pagas e pendentes
- Visualização de comprometimento futuro (3 meses)
- Baixa manual ou automática de parcelas
- Suporte a parcelamento em débito e crédito

#### 🔄 **Transferências entre Contas**
- Transferência rápida entre contas próprias
- Histórico completo de transferências
- Atualização automática de saldos
- Reversão fácil de transferências

#### 📊 **Relatórios Avançados**
- Gráfico de evolução mensal (últimos 6 meses)
- Análise de despesas por categoria com percentuais
- Comparativo de receitas vs despesas
- Previsão de gastos futuros com parcelas
- Visualização de comprometimento financeiro

#### 📎 **Anexos de Comprovantes**
- Upload de imagens (JPG, PNG) ou PDFs
- Visualização direta dos comprovantes
- Limite de 5MB por arquivo
- Armazenamento seguro

## 📋 Funcionalidades Completas

### Fase 1 + Fase 2:
- ✅ Sistema de autenticação completo
- ✅ Dashboard inteligente com indicadores
- ✅ Transações (receitas e despesas)
- ✅ Contas bancárias múltiplas
- ✅ Categorias customizáveis
- ✅ Filtros avançados
- ✅ **Cartões de crédito com faturas**
- ✅ **Despesas parceladas**
- ✅ **Transferências entre contas**
- ✅ **Relatórios detalhados**
- ✅ **Anexos de comprovantes**

## 🚀 Como Executar

### Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Instalação

1. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

2. **Execute a aplicação**:
```bash
python app.py
```

3. **Acesse no navegador**:
```
http://localhost:5000
```

## 📝 Guia Rápido de Uso

### Cartões de Crédito
1. Acesse **Menu → Cartões**
2. Clique em **"Novo Cartão"**
3. Preencha: Nome, Limite, Dia de Fechamento e Vencimento
4. Visualize suas faturas e limite disponível

### Compras Parceladas
1. Ao adicionar uma **nova transação**
2. Marque a opção **"Parcelar esta compra"**
3. Escolha o número de parcelas (2-24x)
4. As parcelas serão criadas automaticamente
5. Acompanhe em **Menu → Parcelas**

### Transferências
1. Acesse **Menu → Transferências**
2. Clique em **"Nova Transferência"**
3. Selecione conta de origem e destino
4. Informe o valor
5. Os saldos são atualizados automaticamente

### Relatórios
1. Acesse **Menu → Relatórios**
2. Veja evolução dos últimos 6 meses
3. Analise gastos por categoria
4. Verifique comprometimento futuro

## 🎨 Recursos de Design

- Interface moderna e intuitiva
- Gráficos interativos (Chart.js)
- Cores indicativas por tipo
- Badges de status
- Barras de progresso para limites
- Design totalmente responsivo

## 📊 Estrutura do Banco de Dados

### Novas Tabelas (Fase 2):
- **CreditCard**: Cartões de crédito com limites e datas
- **Installment**: Parcelas de compras parceladas
- **Transfer**: Transferências entre contas

### Tabelas Atualizadas:
- **Transaction**: Agora suporta cartão de crédito e anexos
- **Account**: Relacionamentos com transferências

## 🔐 Segurança

- Senhas criptografadas (Werkzeug)
- Sessões seguras (Flask-Login)
- Upload de arquivos com validação
- Dados isolados por usuário
- Proteção contra SQL Injection (SQLAlchemy ORM)

## 💡 Dicas de Uso

### Organize suas Finanças
1. **Cadastre primeiro**: Todas as contas e cartões
2. **Lance diariamente**: Não acumule lançamentos
3. **Use categorias**: Facilita análise posterior
4. **Parcele conscientemente**: Acompanhe comprometimento futuro
5. **Anexe comprovantes**: Facilita conferências

### Melhores Práticas
- Configure corretamente as datas dos cartões
- Revise suas faturas antes do vencimento
- Acompanhe o dashboard semanalmente
- Use transferências para organizar seu dinheiro
- Consulte relatórios mensalmente

## 📱 Responsividade

O sistema funciona perfeitamente em:
- 💻 Desktop (experiência completa)
- 📱 Tablet (interface adaptada)
- 📱 Smartphone (otimizado para touch)

## 🎯 Próximas Melhorias (Fase 3 - Planejada)

- 🎯 Metas financeiras e objetivos
- 🔔 Notificações de vencimentos
- 📥 Importação de extratos (OFX/CSV)
- 🤖 Categorização inteligente por IA
- 🌙 Modo escuro
- 📧 Alertas por email
- 📱 App mobile nativo
- 💱 Suporte a múltiplas moedas

## 🐛 Solução de Problemas

### Erro ao fazer upload
→ Verifique se o arquivo tem menos de 5MB
→ Formatos aceitos: JPG, PNG, PDF

### Parcela não aparece na fatura
→ Verifique se a data de vencimento está no período da fatura
→ Confira as datas de fechamento do cartão

### Saldo inconsistente
→ Verifique se todas as transações foram lançadas corretamente
→ Confira se não há transferências duplicadas

## 📖 Documentação Adicional

- `GUIA_DE_USO.md` - Manual completo do usuário
- `CHANGELOG.md` - Histórico de alterações
- Comentários no código para desenvolvedores

## 🤝 Contribuindo

Este é um projeto pessoal em constante evolução. Sugestões são bem-vindas!

## 📄 Licença

Uso pessoal e educacional.

## 🎓 Tecnologias Utilizadas

- **Backend**: Flask 3.0 + SQLAlchemy
- **Frontend**: HTML5 + Tailwind CSS + JavaScript
- **Banco de Dados**: SQLite (dev) / PostgreSQL (prod)
- **Gráficos**: Chart.js 4.x
- **Ícones**: FontAwesome 6.x
- **Autenticação**: Flask-Login

## 📞 Suporte

Para dúvidas ou problemas:
1. Consulte o `GUIA_DE_USO.md`
2. Verifique os exemplos no código
3. Revise este README

---

## ⚡ Mudanças da Fase 1 para Fase 2

### Banco de Dados
- ✨ 3 novas tabelas (CreditCard, Installment, Transfer)
- ✨ 2 novos campos em Transaction (credit_card_id, attachment)
- ✨ Relacionamentos complexos entre tabelas

### Interface
- ✨ 9 novas páginas/telas
- ✨ Dashboard expandido com novos cards
- ✨ Menu de navegação com novos itens
- ✨ Formulários inteligentes com validações

### Funcionalidades
- ✨ Gestão completa de cartões de crédito
- ✨ Sistema de parcelamento automático
- ✨ Transferências entre contas
- ✨ Relatórios visuais avançados
- ✨ Upload e visualização de anexos

### Performance
- ⚡ Consultas otimizadas com SQLAlchemy
- ⚡ Cálculos de fatura em tempo real
- ⚡ Carregamento progressivo de dados

---

**Versão**: 2.0.0  
**Data**: Janeiro 2026  
**Status**: ✅ Estável e Funcional

Desenvolvido com ❤️ usando Python, Flask e muito café ☕
