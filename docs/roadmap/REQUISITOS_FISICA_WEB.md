# Requisitos Oficiais — Física Web

## Missão

Desenvolver um laboratório web de Física inclusivo, multimodal e extensível, como evolução tecnológica da pesquisa sobre o estudo da ação da gravidade no ensino inclusivo.

O Física Web não será limitado a um conjunto fechado de práticas. A arquitetura deverá sustentar ambientes laboratoriais de diferentes áreas da Física, experimentos pré-configurados e experimentos criados pelo professor.

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

## Arquitetura universal do laboratório

Todos os ambientes deverão reutilizar o mesmo ciclo experimental:

Contexto escolar → Grupo/participantes → Ambiente de Física → Experimento → Configuração → Aquisição → Dados brutos → Conversão/calibração → Dados físicos → Cálculos → Estatística/incerteza → Gráficos → Interpretação → Relatório multimodal → Persistência.

A origem dos dados não altera o núcleo analítico. Cada medição deve registrar sua origem como manual, dispositivo/sensor, híbrida ou importação.

## Ambientes laboratoriais

### 1. Mecânica

Queda livre, pêndulo simples, plano inclinado, MRU, MRUV, lançamento horizontal, lançamento oblíquo, leis de Newton, atrito, energia mecânica, quantidade de movimento, colisões, movimento circular, força centrípeta, lei de Hooke, sistema massa-mola, oscilações, torque, equilíbrio e máquinas simples.

### 2. Termologia e Termodinâmica

Temperatura, equilíbrio térmico, aquecimento e resfriamento, calorimetria, calor específico, mudanças de estado, dilatação, condução térmica e experimentos escolares com gases.

### 3. Ondulatória e Acústica

Período, frequência, comprimento de onda, velocidade de propagação, ondas em cordas, ressonância, ondas estacionárias, intensidade sonora, velocidade do som e efeito Doppler.

### 4. Óptica

Reflexão, refração, lei de Snell, índice de refração, ângulo crítico, espelhos, lentes, distância focal, formação de imagens, intensidade luminosa e, em fases posteriores, difração e interferência.

### 5. Eletricidade e Eletrônica

Lei de Ohm, resistores, associações série/paralelo, potência elétrica, resistividade, carga e descarga de capacitores, divisores de tensão, LDR, termistores e instrumentação eletrônica educacional.

### 6. Magnetismo e Eletromagnetismo

Campo magnético, eletroímã, sensores Hall, indução eletromagnética, lei de Faraday e transformadores em configurações educacionais seguras.

### 7. Fluidos

Densidade, pressão, pressão hidrostática, empuxo, princípio de Arquimedes, princípio de Pascal, vazão, continuidade e experimentos introdutórios relacionados a Bernoulli.

### 8. Física Moderna

Espectroscopia, LEDs e estimativas experimentais compatíveis com o ensino de Física Moderna. Experimentos que envolvam fontes ou equipamentos de risco somente poderão ser incluídos mediante protocolos específicos de segurança.

### 9. Laboratório Livre

O professor poderá criar experimentos próprios sem necessidade de alterar o código-fonte para cada nova atividade. O experimento configurável deverá permitir definir, progressivamente:

- título e área da Física;
- objetivo e questão investigativa;
- referencial teórico;
- variáveis independentes, dependentes e de controle;
- grandezas e unidades;
- instrumentos e sensores;
- fórmulas e transformações;
- valores de referência quando aplicáveis;
- número e sequência de medições;
- gráficos esperados;
- critérios de validação;
- análise estatística e incertezas;
- perguntas investigativas;
- critérios de interpretação;
- formatos acessíveis de apresentação.

## Núcleo experimental reutilizável

A expansão para novos experimentos não deverá gerar uma tabela exclusiva para cada prática. A modelagem deverá evoluir para entidades genéricas, preservando compatibilidade com os experimentos já implementados.

Entidades previstas para essa evolução:

- ambientes_fisica;
- catalogo_experimentos;
- variaveis_experimentais;
- configuracoes_experimento;
- dispositivos;
- sensores;
- canais_aquisicao;
- sessoes_aquisicao;
- leituras;
- transformacoes_calibracao.

Essas entidades deverão complementar, e não substituir abruptamente, a estrutura existente.

## Modos de aquisição

Todo experimento compatível deverá oferecer:

1. Manual — valores digitados pelo usuário a partir de instrumentos convencionais;
2. Automático — dados recebidos de dispositivo/sensor;
3. Híbrido — combinação de dados manuais e automáticos;
4. Importação — futura entrada estruturada de conjuntos de dados previamente coletados.

## Instrumentação física e aquisição de dados

### Dispositivos previstos

- Arduino Uno, Nano, Mega e placas compatíveis;
- Raspberry Pi e outros computadores de placa única compatíveis;
- ESP32 e dispositivos equivalentes em fase posterior;
- sensores e interfaces conectados por portas analógicas ou digitais.

### Tipos de entrada

- entradas analógicas para sensores de tensão, luz, força, pressão, posição, temperatura e outros transdutores compatíveis;
- entradas digitais para fotogates, chaves, sensores de presença, encoders, pulsos e eventos temporais;
- comunicação serial USB para Arduino;
- GPIO para Raspberry Pi;
- possibilidade futura de Web Serial, Bluetooth, Wi-Fi e Web Bluetooth quando tecnicamente adequados.

### Arquitetura de instrumentação

Sensor → Arduino/Raspberry Pi → camada de aquisição → Física Web → validação/calibração → experimento → Supabase → análise → gráfico → relatório multimodal.

### Configuração de canais

Cada canal deverá poder registrar dispositivo, porta/pino, tipo analógico/digital, sensor, grandeza física, unidade, taxa de amostragem, fator de calibração, offset, resolução, intervalo válido, estado de conexão e timestamp.

### Transparência pedagógica

A instrumentação não deverá transformar o experimento em caixa-preta. O estudante deverá poder compreender o sensor utilizado, a grandeza medida, o sinal bruto, a conversão para grandeza física, a calibração, os dados processados, o gráfico e as limitações/incertezas da medida.

## Acessibilidade transversal

A acessibilidade pertence ao núcleo e não a um ambiente isolado. Todos os experimentos deverão poder produzir representações visual/gráfica, textual, áudio/audiodescrição e Libras conforme disponibilidade tecnológica.

O usuário escolhe voluntariamente os recursos funcionais. Não inferir deficiência pela câmera. Dados adquiridos por sensores deverão alimentar as mesmas saídas acessíveis. Alertas poderão ser apresentados por som, vibração ou sinais visuais quando tecnicamente disponíveis.

## Banco oficial atual

Hierarquia atual: Escola → Turma/Série → Grupo → Experimento → Medições → Resultado → Relatório.

Entidades atuais: escolas, turmas, grupos_experimentais, participantes, experimentos, medicoes, resultados_experimentais, relatorios e preferencias_acessibilidade.

A evolução para o núcleo universal deverá ser incremental e migrável, sem perda da estrutura validada.

## Segurança

O navegador não deverá executar comandos arbitrários no hardware. A comunicação deve utilizar protocolos controlados, lista explícita de comandos permitidos e validação de limites. Saídas digitais capazes de acionar atuadores deverão ser tratadas separadamente das entradas de aquisição e exigir salvaguardas adicionais quando houver risco físico.

## Visão computacional futura

Pesquisar reconhecimento de Libras por mãos, corpo e componentes não manuais. Priorizar processamento local e não armazenar vídeo/rosto por padrão.

## Privacidade e pesquisa

Minimizar dados pessoais; pseudonimizar participantes; separar contexto escolar de identidade pessoal; não armazenar diagnóstico de deficiência quando preferências funcionais forem suficientes; documentar consentimento e governança antes de pesquisa formal com participantes.

## Próximas prioridades

1. validar definitivamente a conexão Flask → Supabase por rota de diagnóstico;
2. persistir escola, turma/série e grupo experimental;
3. persistir experimentos e medições existentes;
4. persistir resultados e relatórios;
5. conectar audiodescrição à API acessível e controles de reprodução;
6. aperfeiçoar responsividade e validar PDF/gráficos em dispositivos móveis;
7. projetar o catálogo de ambientes e experimentos sem quebrar a aplicação atual;
8. projetar a camada genérica de variáveis e medições;
9. implementar primeiro novo experimento sobre o núcleo reutilizável;
10. projetar Hardware Lab e protocolo de aquisição;
11. criar autenticação e perfis quando a fase de uso exigir;
12. desenvolver protocolo de pesquisa e governança dos dados.

## Regra de engenharia

Auditoria → diagnóstico → uma alteração controlada por vez → commit → deploy → validação → documentação. Não substituir estruturas comprovadamente funcionais sem validação.
