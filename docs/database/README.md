# Banco de Dados — Supabase/PostgreSQL

## Hierarquia principal

Escola → Turma/Série → Grupo experimental → Experimento → Medições → Resultado → Relatório.

## Tabelas oficiais iniciais

- `escolas`
- `turmas`
- `grupos_experimentais`
- `participantes`
- `experimentos`
- `medicoes`
- `resultados_experimentais`
- `relatorios`
- `preferencias_acessibilidade`

View analítica: `vw_experimentos_resumo`.

## Segurança

RLS deve permanecer habilitado nas tabelas públicas. Nesta fase não há política de acesso público direto às tabelas. O acesso administrativo ocorrerá pelo backend Flask com credencial secreta armazenada somente no Render.

Nunca versionar `SUPABASE_URL`, secret/service-role key, senhas ou tokens.

## Privacidade

Participantes devem ser pseudonimizados sempre que possível. Preferências de acessibilidade devem registrar recursos funcionais ativados, evitando armazenar diagnóstico de deficiência sem necessidade e base adequada. Vídeo, imagem facial e gravações da câmera não devem ser persistidos por padrão.
