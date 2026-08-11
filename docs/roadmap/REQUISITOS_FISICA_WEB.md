# Requisitos Oficiais — Física Web

## Missão

Desenvolver um laboratório web de Física inclusivo e multimodal, como evolução tecnológica da pesquisa sobre o estudo da ação da gravidade no ensino inclusivo.

## Estado funcional

- aplicação Flask publicada no Render;
- experimentos de queda livre, pêndulo simples e plano inclinado;
- cálculo experimental de g;
- estatísticas: média, desvio padrão, erro percentual, mínimo e máximo;
- gráfico de g por medição com referência teórica e média experimental;
- PDF experimental;
- base de interpretação pedagógica;
- perfil de acessibilidade no frontend;
- integração VLibras;
- API de relatório acessível/audiodescrição;
- modelo inicial Supabase criado;
- RLS habilitado nas tabelas do banco.

## Próximas prioridades

1. conectar Flask ao Supabase com credenciais somente no Render;
2. persistir escola, turma/série e grupo experimental;
3. persistir experimentos e medições;
4. persistir resultados e relatórios;
5. conectar botão de audiodescrição à API acessível;
6. oferecer controles ouvir, pausar, continuar e parar;
7. aperfeiçoar interface responsiva sem comprometer as rotas Flask;
8. validar relatório PDF e gráfico em dispositivos móveis;
9. criar autenticação e perfis quando a fase de uso exigir;
10. desenvolver protocolo de pesquisa e governança dos dados.

## Banco oficial

Hierarquia: Escola → Turma/Série → Grupo → Experimento → Medições → Resultado → Relatório.

Entidades: escolas, turmas, grupos_experimentais, participantes, experimentos, medicoes, resultados_experimentais, relatorios e preferencias_acessibilidade.

## Acessibilidade

O sistema deve suportar múltiplas representações do mesmo resultado: visual/gráfica, textual, áudio/audiodescrição e Libras. O usuário escolhe voluntariamente recursos funcionais. Não inferir deficiência pela câmera.

## Visão computacional futura

Pesquisar reconhecimento de Libras por mãos, corpo e componentes não manuais. Priorizar processamento local e não armazenar vídeo/rosto por padrão.

## Privacidade e pesquisa

Minimizar dados pessoais; pseudonimizar participantes; separar contexto escolar de identidade pessoal; não armazenar diagnóstico de deficiência quando preferências funcionais forem suficientes; documentar consentimento e governança antes de pesquisa formal com participantes.

## Regra de engenharia

Auditoria → diagnóstico → uma alteração controlada por vez → commit → deploy → validação → documentação. Não substituir estruturas comprovadamente funcionais sem validação.
