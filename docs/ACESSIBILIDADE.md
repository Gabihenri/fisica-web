# Física Web — acessibilidade inclusiva

## Objetivo

O Física Web deve permitir que estudantes com diferentes necessidades de acesso realizem os experimentos, registrem evidências e interpretem resultados com autonomia crescente.

## Recursos implementados

- Navegação e orientação falada em português do Brasil.
- Leitura resumida da tela e identificação de seções, menus e controles.
- Orientação contextual do experimento quando a página fornece dados do experimento.
- Comandos de voz quando o navegador oferece Speech Recognition.
- Compatibilidade com VoiceOver, TalkBack e navegação por teclado.
- Região `aria-live` para comunicar mudanças importantes.
- Foco visual reforçado durante a orientação guiada.
- Rótulos acessíveis para controles e campos quando a marcação original não os fornece.
- Tabelas com `caption`, cabeçalhos e descrição estrutural.
- Gráficos em `canvas`/`svg` expostos como imagens acessíveis e relacionados a tabelas de dados quando disponíveis.
- Campos de medição associados a rótulos e unidades quando identificáveis.
- Mensagens de resultado e erro comunicadas como regiões vivas.

## Padrão pedagógico para cada experimento

Cada laboratório deve, progressivamente, fornecer:

1. objetivo;
2. pré-requisitos;
3. materiais e sensores;
4. montagem;
5. configuração de parâmetros;
6. procedimento passo a passo;
7. orientação sobre cada campo;
8. registro das medições;
9. tabela de dados acessível;
10. descrição do gráfico;
11. interpretação física;
12. conclusão;
13. geração do relatório.

## Voz e leitor de tela

A voz própria do aplicativo complementa, mas não substitui, o leitor de tela do sistema operacional. No iOS, o teste prioritário é VoiceOver; no Android, TalkBack.

O reconhecimento de voz é opcional e depende do suporte/permissão do navegador. A aplicação deve continuar totalmente utilizável sem reconhecimento de voz.

## Critérios de aceite

Um laboratório só deve ser considerado plenamente inclusivo quando um usuário que não enxerga consegue, com leitor de tela e/ou orientação falada:

- identificar onde está;
- localizar o experimento;
- ouvir o objetivo;
- descobrir os materiais e parâmetros;
- preencher os campos;
- iniciar e executar o procedimento;
- registrar medições;
- acessar os dados em tabela;
- compreender a representação gráfica por uma descrição alternativa;
- ouvir a interpretação dos resultados;
- gerar e acessar o relatório.

## Próximas evoluções

- descrições científicas específicas por experimento, em vez de apenas descrições genéricas da interface;
- descrição automática de tendências e grandezas dos gráficos a partir dos dados calculados;
- navegação por regiões e etapas do experimento;
- testes reais com VoiceOver e TalkBack;
- auditoria WCAG 2.2 AA dos templates;
- expansão para Libras/VLibras e outros recursos de comunicação acessível.
