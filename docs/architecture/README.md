# Arquitetura

Arquitetura-alvo do Física Web:

Usuário → Interface Web acessível → Flask/Render → camada de serviços → Supabase/PostgreSQL → análise → relatório multimodal.

## Responsabilidades

- Frontend: interação experimental e recursos de acessibilidade.
- Backend Flask: validação, cálculos físicos, estatística, relatórios e acesso seguro ao banco.
- Supabase: persistência estruturada e relações escolares/experimentais.
- Render: execução pública da aplicação.
- GitHub: código, documentação, histórico e rastreabilidade.

## Regra

Credenciais do banco ficam exclusivamente em variáveis de ambiente do servidor. O navegador não recebe chave administrativa do Supabase.
