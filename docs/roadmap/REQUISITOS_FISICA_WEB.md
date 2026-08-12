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
- RLS habilitado nas tabelas do banco;
- camada de conexão Supabase adicionada ao backend Flask.

## Próximas prioridades

1. validar definitivamente a conexão Flask → Supabase por rota de diagnóstico;
2. persistir escola, turma/série e grupo experimental;
3. persistir experimentos e medições;
4. persistir resultados e relatórios;
5. conectar botão de audiodescrição à API acessível;
6. oferecer controles ouvir, pausar, continuar e parar;
7. aperfeiçoar interface responsiva sem comprometer as rotas Flask;
8. validar relatório PDF e gráfico em dispositivos móveis;
9. criar autenticação e perfis quando a fase de uso exigir;
10. desenvolver protocolo de pesquisa e governança dos dados;
11. criar a camada de instrumentação física para aquisição automática de dados por microcontroladores e computadores de placa única.

## Banco oficial

Hierarquia: Escola → Turma/Série → Grupo → Experimento → Medições → Resultado → Relatório.

Entidades: escolas, turmas, grupos_experimentais, participantes, experimentos, medicoes, resultados_experimentais, relatorios e preferencias_acessibilidade.

## Acessibilidade

O sistema deve suportar múltiplas representações do mesmo resultado: visual/gráfica, textual, áudio/audiodescrição e Libras. O usuário escolhe voluntariamente recursos funcionais. Não inferir deficiência pela câmera.

## Instrumentação física e aquisição de dados

O Física Web deverá oferecer um modo universal de uso manual e um modo de aquisição automática por hardware externo.

### Dispositivos previstos

- Arduino Uno, Nano, Mega e placas compatíveis;
- Raspberry Pi e outros computadores de placa única compatíveis;
- futuramente ESP32 e dispositivos equivalentes;
- sensores e interfaces conectados por portas analógicas ou digitais.

### Tipos de entrada

- entradas analógicas para sensores de tensão, luz, força, pressão, posição, temperatura e outros transdutores compatíveis;
- entradas digitais para fotogates, chaves, sensores de presença, encoders, pulsos e eventos temporais;
- comunicação serial USB para Arduino;
- GPIO para Raspberry Pi;
- possibilidade futura de conexão por Bluetooth, Wi-Fi, Web Serial e Web Bluetooth quando o navegador e o dispositivo permitirem.

### Arquitetura prevista

Sensor → Arduino/Raspberry Pi → camada de aquisição → Física Web → validação/calibração → experimento → banco Supabase → análise → gráfico → relatório multimodal.

A aplicação deve permitir ao usuário escolher entre:

1. entrada manual de dados;
2. aquisição automática por dispositivo;
3. modo híbrido, no qual parte dos dados vem do sensor e parte é informada pelo usuário.

### Configuração de canais

Cada canal de aquisição deverá poder registrar:

- dispositivo;
- tipo de porta: analógica ou digital;
- número/pino da porta;
- sensor conectado;
- grandeza física;
- unidade;
- taxa de amostragem;
- fator de calibração;
- offset;
- resolução;
- intervalo válido;
- estado de conexão;
- timestamp de cada amostra.

### Requisitos pedagógicos

A instrumentação não deve transformar o experimento em uma caixa-preta. O estudante deverá conseguir visualizar:

- qual sensor está sendo utilizado;
- qual grandeza está sendo medida;
- como o sinal bruto é convertido em grandeza física;
- calibração utilizada;
- gráfico em tempo real;
- dados brutos e dados processados;
- incertezas e limitações do sensor.

### Inclusão

Os dados adquiridos por sensores devem alimentar as mesmas saídas acessíveis já previstas: gráfico, texto, audiodescrição, síntese de voz e Libras. Alertas experimentais poderão também ser apresentados por som, vibração ou sinais visuais quando tecnicamente disponíveis.

### Segurança

O navegador não deverá executar comandos arbitrários no hardware. A comunicação deve utilizar protocolos controlados, lista explícita de comandos permitidos e validação de limites. Saídas digitais capazes de acionar atuadores deverão ser tratadas separadamente das entradas de aquisição e exigir confirmação explícita quando houver risco físico.

## Visão computacional futura

Pesquisar reconhecimento de Libras por mãos, corpo e componentes não manuais. Priorizar processamento local e não armazenar vídeo/rosto por padrão.

## Privacidade e pesquisa

Minimizar dados pessoais; pseudonimizar participantes; separar contexto escolar de identidade pessoal; não armazenar diagnóstico de deficiência quando preferências funcionais forem suficientes; documentar consentimento e governança antes de pesquisa formal com participantes.

## Regra de engenharia

Auditoria → diagnóstico → uma alteração controlada por vez → commit → deploy → validação → documentação. Não substituir estruturas comprovadamente funcionais sem validação.
