# filepath: c:\Users\rodri\Desktop\REPLIT RPG\core\location_generator.py
import random
import logging
from typing import Dict, List, Optional

from .game_state_model import LocationCoords, LocationData, GameState
from .npc import NPC  # Assumindo que NPC está em core.npc

logger = logging.getLogger(__name__)


class LocationGenerator:
    """
    Handles the generation of new location details including names, descriptions,
    resources, events, and NPCs.
    """

    _location_types: Dict[str, List[str]] = {
        "abrigo": ["abrigo subterrâneo", "bunker", "refúgio seguro"],
        "ruina_urbana": [
            "ruas devastadas",
            "prédio abandonado",
            "zona comercial saqueada",
        ],
        "posto_avancado": ["posto de controle", "acampamento de sobreviventes"],
        "zona_perigosa": ["ninho de zumbis", "área contaminada", "hospital infestado"],
        "natureza_selvagem": [
            "floresta silenciosa",
            "estrada abandonada",
            "fazenda isolada",
        ],
    }

    @staticmethod
    def generate_new_location_data(
        location_id: str,
        game_state: GameState,
        location_type_suggestion: str = "ruina_urbana",
        name_suggestion: Optional[str] = None,
        description_suggestion: Optional[str] = None,
    ) -> LocationData:
        """
        Generates the core data for a new location.
        Coordinates and connections are handled by GameEngine.
        """
        location_name = name_suggestion or LocationGenerator._generate_location_name(
            location_type_suggestion
        )
        description = (
            description_suggestion
            or LocationGenerator._generate_location_description(
                location_type_suggestion
            )
        )

        # NPCs são gerados e adicionados ao game_state.known_npcs aqui.
        # A lista retornada contém os nomes dos NPCs para esta localização específica.
        npcs_list = LocationGenerator._generate_location_npcs(
            location_type_suggestion, game_state
        )

        location_data: LocationData = {
            "name": location_name,
            "coordinates": {
                "x": 0,
                "y": 0,
                "z": 0,
            },  # Placeholder, será definido pelo GameEngine
            "type": location_type_suggestion,
            "description": description,
            "visited": True,  # Nova localização é visitada ao ser gerada
            "connections": {},  # Placeholder, será definido pelo GameEngine
            "resources": LocationGenerator._generate_location_resources(
                location_type_suggestion
            ),
            "danger_level": random.randint(1, 5),
            "events": LocationGenerator._generate_location_events(
                location_type_suggestion
            ),
            "npcs": npcs_list,  # Lista de nomes de NPCs presentes nesta localização
        }
        return location_data

    @staticmethod
    def _generate_location_name(location_type: str) -> str:
        prefixes = {
            "abrigo": ["Abrigo", "Bunker", "Refúgio"],
            "ruina_urbana": ["Ruínas de", "Distrito de", "Setor"],
            "posto_avancado": ["Posto Avançado", "Acampamento", "Barricada"],
            "zona_perigosa": ["Zona Infestada de", "Ninho de", "Covil de"],
            "natureza_selvagem": ["Estrada para", "Floresta de", "Campos de"],
        }
        suffixes = [
            "Perdido",
            "Esquecido",
            "Devastado",
            "Silencioso",
            "da Esperança",
            "do Desespero",
            "Sombrio",
            "Antigo",
        ]
        feminine_prefixes = [
            "Abrigo",
            "Refúgio",
            "Ruínas de",
            "Zona Infestada de",
            "Estrada para",
            "Floresta de",
            "Barricada",
        ]
        prefix = random.choice(prefixes.get(location_type, ["Local"]))
        is_feminine_prefix = any(fp in prefix for fp in feminine_prefixes)

        if is_feminine_prefix:
            feminine_suffixes = [
                "Perdida",
                "Esquecida",
                "Devastada",
                "Silenciosa",
                "da Esperança",
                "do Desespero",
                "Sombria",
                "Antiga",
            ]
            suffix = random.choice(feminine_suffixes)
        else:
            suffix = random.choice(suffixes)

        base_name = f"{prefix} {suffix}"
        if random.random() < 0.2:  # 20% de chance de adicionar um qualificador
            qualifier = random.choice(
                ["Alfa", "Beta", "Gama", "Delta", "Zeta", "7", "9", "X"]
            )
            base_name = f"{base_name} {qualifier}"
        return base_name

    @staticmethod
    def _generate_location_description(location_type: str) -> str:
        descriptions = {
            "abrigo": "Um refúgio improvisado, mas relativamente seguro. As paredes são frias e úmidas, e o ar é pesado com o cheiro de mofo e desinfetante barato.",
            "ruina_urbana": "Prédios em ruínas se erguem como esqueletos contra o céu cinzento. Carros abandonados e destroços bloqueiam as ruas, e um silêncio fantasmagórico é quebrado apenas pelo vento uivante.",
            "posto_avancado": "Uma barricada feita às pressas com arame farpado e sucata protege este pequeno bolsão de civilização. Sentinelas observam nervosamente os arredores, armas em punho.",
            "zona_perigosa": "Um silêncio opressor paira aqui, quebrado apenas por sons guturais distantes ou o zumbido de insetos mutantes. O cheiro de morte e decomposição é forte e nauseante.",
            "natureza_selvagem": "A natureza tenta retomar o que era seu, com vegetação densa crescendo sobre as cicatrizes da civilização. Mesmo aqui, a ameaça dos infectados e da escassez é constante.",
        }
        base_desc = descriptions.get(
            location_type,
            "Um local desolado e perigoso. Você sente um arrepio na espinha e a sensação constante de estar sendo observado.",
        )
        details = [
            "Pichações estranhas cobrem algumas paredes.",
            "Há um veículo capotado e enferrujado nas proximidades.",
            "O som de água pingando ecoa de algum lugar próximo.",
            "Um odor metálico paira no ar.",
            "Você nota rastros recentes no chão poeirento.",
            "Um vento frio varre a área, trazendo consigo sussurros indecifráveis.",
        ]
        return base_desc + " " + random.choice(details)

    @staticmethod
    def _generate_location_resources(location_type: str) -> Optional[Dict[str, int]]:
        if random.random() > 0.7:  # 30% de chance de não haver recursos
            return None
        base_resources = {
            "Comida Enlatada": (1, 3),
            "Garrafa de Água": (1, 2),
            "Bandagens": (0, 2),
            "Sucata de Metal": (1, 5),
            "Retalhos de Tecido": (1, 4),
            "Componentes Eletrônicos": (0, 2),
            "Munição (Pistola)": (0, 5),
            "Munição (Espingarda)": (0, 3),
            "Gasolina (lata pequena)": (0, 1),
            "Madeira": (1, 4),
            "Ervas Medicinais": (0, 2),
            "Pilhas": (0, 3),
        }
        type_specific_boost = {
            "abrigo": {"Comida Enlatada": 2, "Garrafa de Água": 2, "Bandagens": 1},
            "ruina_urbana": {"Sucata de Metal": 2, "Componentes Eletrônicos": 1},
            "posto_avancado": {
                "Munição (Pistola)": 3,
                "Munição (Espingarda)": 2,
                "Bandagens": 1,
            },
            "zona_perigosa": {},  # Zonas perigosas têm menos recursos diretos
            "natureza_selvagem": {"Madeira": 2, "Ervas Medicinais": 1},
        }
        generated_resources: Dict[str, int] = {}
        num_resource_types_to_find = random.randint(1, 3)

        possible_resources_for_type = list(base_resources.keys())
        # Aumentar a chance de encontrar recursos específicos do tipo
        if location_type in type_specific_boost:
            for _ in range(2):
                possible_resources_for_type.extend(
                    type_specific_boost[location_type].keys()
                )

        for _ in range(num_resource_types_to_find):
            if not possible_resources_for_type:
                break
            resource_name = random.choice(possible_resources_for_type)
            # Não remover para permitir que o mesmo tipo de recurso seja escolhido novamente se a lista for pequena,
            # mas isso pode levar a menos variedade. Para garantir variedade, remova:
            # possible_resources_for_type.remove(resource_name)

            min_q, max_q = base_resources[resource_name]
            quantity_boost = 0
            if (
                location_type in type_specific_boost
                and resource_name in type_specific_boost[location_type]
            ):
                quantity_boost = type_specific_boost[location_type][resource_name]

            quantity = random.randint(min_q, max_q + quantity_boost)
            if quantity > 0:
                generated_resources[resource_name] = (
                    generated_resources.get(resource_name, 0) + quantity
                )
        return generated_resources if generated_resources else None

    @staticmethod
    def _generate_location_events(location_type: str) -> List[str]:
        common_events = [
            "Um silêncio repentino e perturbador toma conta do ambiente.",
            "Você ouve um barulho metálico distante, como algo caindo.",
            "Uma rajada de vento traz consigo um cheiro estranho e adocicado.",
        ]
        type_specific_events = {
            "abrigo": [
                "O gerador falha por um instante, mergulhando tudo na escuridão antes de voltar.",
                "Alguém está cantando baixinho uma canção triste em um canto escuro.",
                "Uma discussão acalorada sobre o racionamento de comida pode ser ouvida de uma sala próxima.",
                "Você encontra um diário antigo com anotações sobre os primeiros dias do surto.",
            ],
            "ruina_urbana": [
                "Um bando de corvos grasna agourentamente de cima de um prédio em ruínas.",
                "O vento assobia sinistramente através das janelas quebradas de um arranha-céu esvaziado.",
                "Um barulho alto de algo desabando ecoa de um prédio vizinho, levantando uma nuvem de poeira.",
                "Você vê uma sombra se movendo rapidamente em um beco, desaparecendo antes que possa identificar.",
            ],
            "posto_avancado": [
                "Um sobrevivente está limpando sua arma meticulosamente, com um olhar determinado.",
                "A troca de guarda na barricada acontece, os novos sentinelas parecem tensos.",
                "Alguém conta uma história nostálgica sobre como era o mundo antes do apocalipse.",
                "Um alarme falso soa, causando um breve momento de pânico.",
            ],
            "zona_perigosa": [
                "Um gemido gutural e faminto ecoa de algum lugar próximo, fazendo seu sangue gelar.",
                "O cheiro de podridão e carne em decomposição se intensifica, quase o fazendo engasgar.",
                "Você vê sombras se movendo rapidamente no limite da sua visão, muito rápidas para serem humanas.",
                "O chão está coberto de uma substância viscosa e escura de origem desconhecida.",
            ],
            "natureza_selvagem": [
                "Um animal selvagem (não infectado, talvez um cervo ou coelho) cruza seu caminho e desaparece na mata.",
                "O silêncio da floresta é quase total, quebrado apenas pelo som do vento nas árvores e seus próprios passos.",
                "Você encontra rastros recentes no chão lamacento... definitivamente não são humanos.",
                "Uma revoada de pássaros assustados levanta voo de repente das árvores próximas.",
            ],
        }
        possible_events = common_events + type_specific_events.get(location_type, [])
        if not possible_events:
            return ["O ambiente parece estranhamente calmo... calmo demais."]
        num_events = random.randint(0, 2)  # 0 a 2 eventos
        if num_events == 0:
            return []
        return random.sample(possible_events, k=min(num_events, len(possible_events)))

    @staticmethod
    def _generate_location_npcs(location_type: str, game_state: GameState) -> List[str]:
        if random.random() < 0.4:  # 40% de chance de não haver NPCs
            return []
        npc_archetypes = {
            "abrigo": [
                "Velho Sobrevivente Cansado",
                "Médica de Campo Apavorada",
                "Engenheiro Habilidoso",
                "Criança Assustada",
            ],
            "ruina_urbana": [
                "Catador Solitário",
                "Saqueador Desesperado",
                "Vigia Paranoico",
            ],
            "posto_avancado": [
                "Líder Carismático do Posto",
                "Guarda Leal",
                "Comerciante Oportunista",
            ],
            "zona_perigosa": [],  # Zonas perigosas raramente têm NPCs amigáveis/vivos
            "natureza_selvagem": ["Caçador Recluso", "Eremita Misterioso"],
        }
        possible_archetypes = npc_archetypes.get(
            location_type, ["Sobrevivente Aleatório"]
        )
        if not possible_archetypes:
            return []

        num_npcs_to_generate = random.randint(1, min(2, len(possible_archetypes)))
        generated_npc_names: List[str] = []

        all_known_npc_names_lower = {
            name.lower() for name in game_state.known_npcs.keys()
        }

        attempts = 0
        while (
            len(generated_npc_names) < num_npcs_to_generate and attempts < 20
        ):  # Aumentar tentativas para mais chance
            attempts += 1
            potential_name_archetype = random.choice(possible_archetypes)
            # Para nomes únicos, pode-se adicionar um sufixo numérico ou aleatório se o arquétipo já existir.
            # Por simplicidade, se o arquétipo exato já é um NPC conhecido, tentamos outro.
            if potential_name_archetype.lower() in all_known_npc_names_lower:
                # Tentar gerar um nome ligeiramente diferente, ex: "Catador Solitário 2"
                # Ou simplesmente pular e tentar outro arquétipo se houver variedade.
                # Se a lista de arquétipos for pequena, isso pode resultar em menos NPCs.
                continue

            generated_npc_names.append(potential_name_archetype)
            # Adiciona à verificação local para esta sessão de geração para evitar duplicar o mesmo arquétipo nesta chamada.
            all_known_npc_names_lower.add(potential_name_archetype.lower())

            # Criar e adicionar o NPC ao game_state.known_npcs
            # O NPC é adicionado ao game_state aqui para que esteja disponível globalmente.
            # A lista retornada é apenas dos nomes dos NPCs *nesta* localização.
            new_npc_obj = NPC.from_dict(
                {
                    "name": potential_name_archetype,
                    "race": "Humano",
                    "profession": (
                        potential_name_archetype.split(" ")[-1]
                        if " " in potential_name_archetype
                        else "Sobrevivente"
                    ),
                    "personality": random.choice(
                        [
                            "Cauteloso",
                            "Desconfiado",
                            "Prestativo",
                            "Assustado",
                            "Hostil",
                            "Tagarela",
                        ]
                    ),
                    "level": random.randint(1, 5),
                    "knowledge": [],
                    "quests": [],
                    "current_mood": "Neutro",
                    "disposition": random.choice(
                        ["neutral", "friendly", "hostile", "wary", "scared"]
                    ),
                }
            )
            game_state.add_npc(potential_name_archetype, new_npc_obj)
            logger.info(
                f"Generated and added NPC: {potential_name_archetype} to known_npcs."
            )

        return generated_npc_names
