# Deploy e Operação

## Produção

Aplicação Flask publicada no Render a partir da branch `main` do repositório GitHub.

## Banco

Supabase/PostgreSQL será utilizado para persistência. O Render deve receber as credenciais exclusivamente por variáveis de ambiente.

Variáveis previstas:

- `SUPABASE_URL`
- chave secreta apropriada para o backend, com nome definido na implementação

Nunca inserir valores reais destas variáveis no GitHub.

## Fluxo de mudança

1. auditar estado atual;
2. alterar um componente controlado;
3. commit;
4. deploy automático;
5. validar logs;
6. validar interface e funcionalidade;
7. documentar resultado.

No plano gratuito do Render, a instância pode entrar em repouso após inatividade; portanto a persistência não deve depender da memória do processo ou do filesystem local.
