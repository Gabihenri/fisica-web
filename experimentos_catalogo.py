"""Catálogo inicial de novos experimentos do Física Web.

Os experimentos são descritos de forma declarativa para que o catálogo possa
crescer sem duplicar a lógica científica dos experimentos existentes.
"""

EXPERIMENTOS_NOVOS = [
    {
        "slug": "colisoes",
        "titulo": "Colisões e Conservação do Momento",
        "area": "Mecânica",
        "descricao": "Investigue colisões, momento linear e conservação da quantidade de movimento.",
        "status": "disponivel",
        "objetivos": ["medir velocidades antes e depois", "comparar momento inicial e final"],
    },
    {
        "slug": "energia",
        "titulo": "Energia e Conservação da Energia",
        "area": "Mecânica",
        "descricao": "Analise transformações entre energia cinética e potencial e teste a conservação da energia mecânica.",
        "status": "disponivel",
        "objetivos": ["calcular energia cinética", "calcular energia potencial", "comparar energia inicial e final"],
    },
    {
        "slug": "lei-de-ohm",
        "titulo": "Lei de Ohm",
        "area": "Eletricidade",
        "descricao": "Investigue a relação entre tensão, corrente e resistência em um circuito resistivo.",
        "status": "disponivel",
        "objetivos": ["medir tensão", "medir corrente", "estimar resistência"],
    },
    {
        "slug": "campo-magnetico",
        "titulo": "Campo Magnético e Indução",
        "area": "Magnetismo",
        "descricao": "Explore campos magnéticos e a indução eletromagnética por meio de medições e modelos.",
        "status": "disponivel",
        "objetivos": ["observar variações de campo", "relacionar movimento e indução"],
    },
    {
        "slug": "termodinamica",
        "titulo": "Aquecimento e Resfriamento",
        "area": "Termodinâmica",
        "descricao": "Registre a variação de temperatura ao longo do tempo e investigue processos térmicos.",
        "status": "disponivel",
        "objetivos": ["registrar temperatura", "construir curva térmica", "comparar taxas de aquecimento e resfriamento"],
    },
    {
        "slug": "ondas-e-acustica",
        "titulo": "Ondas e Acústica",
        "area": "Ondulatória",
        "descricao": "Investigue frequência, período, amplitude e características de ondas sonoras.",
        "status": "disponivel",
        "objetivos": ["medir frequência", "comparar períodos", "analisar sinais sonoros"],
    },
    {
        "slug": "optica",
        "titulo": "Reflexão e Refração da Luz",
        "area": "Óptica",
        "descricao": "Investigue reflexão, refração e relações entre ângulos e meios ópticos.",
        "status": "disponivel",
        "objetivos": ["medir ângulos", "testar leis da reflexão", "estimar índice de refração"],
    },
    {
        "slug": "fisica-moderna",
        "titulo": "Física Moderna: Luz, Energia e Espectros",
        "area": "Física Moderna",
        "descricao": "Explore relações entre frequência, energia e espectros com atividades acessíveis e investigativas.",
        "status": "disponivel",
        "objetivos": ["relacionar frequência e energia", "analisar espectros", "investigar modelos da Física Moderna"],
    },
]


def listar_experimentos_novos():
    """Retorna uma cópia do catálogo para consumo seguro pela aplicação."""
    return [dict(experimento) for experimento in EXPERIMENTOS_NOVOS]
