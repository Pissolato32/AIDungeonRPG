# filepath: c:\Users\rodri\Desktop\REPLIT RPG\ai\prompt_builder.py
"""
Module for constructing prompts for the AI model.
"""
from typing import List, Optional

from core.npc import NPC  # Importar a classe NPC
from core.models import Character  # Importar Character do models
from core.game_state_model import GameState, MessageDict


class PromptBuilder:
    """
    Handles the construction of prompts to be sent to the AI model.
    """

    @staticmethod
    def _format_npc_details_for_prompt(npc_name: str, npc_data: NPC) -> str:
        """
        Formats NPC details for inclusion in a prompt.
        (Adaptado de prompt_manager.py)
        """
        # Acessar atributos usando getattr para compatibilidade com objetos
        # e fornecer valores padrão, similar ao dict.get().
        profession = getattr(npc_data, "profession", "Profissão Desconhecida")
        personality = getattr(npc_data, "personality", "Personalidade Variada")

        # Formato mais conciso, incluindo profissão e personalidade no cabeçalho.
        npc_info_str = f"\nDetalhes sobre {npc_name} (Profissão: {profession}, Personalidade: {personality}):\n"
        knowledge_list = getattr(npc_data, "knowledge", [])
        if isinstance(knowledge_list, list) and knowledge_list:
            npc_info_str += f"- Conhecimento: {', '.join(knowledge_list)}\n"
        return npc_info_str

    @staticmethod
    def build_system_prompt() -> str:
        """Builds the static system prompt."""
        return (
            "Você é o Mestre de um jogo de RPG ambientado em um mundo pós-apocalíptico. "
            "Seu papel é narrar com riqueza de detalhes o ambiente, as consequências das ações do jogador, e interpretar os NPCs de forma viva, única e coerente. "
            "Nunca diga que o jogador 'não especificou'; aja com bom senso e mantenha a narrativa fluindo. "
            "Seja imersivo, criativo e mantenha o jogo andando. Se algo é ambíguo, improvise com lógica e drama. "
            "Suas respostas devem ser cinematográficas, envolventes e sempre progredir a narrativa."
        )

    @staticmethod
    def _build_scene_context(game_state: GameState) -> str:
        """Builds the scene context part of the prompt."""
        location = game_state.current_location or "Desconhecido"
        loc_data = game_state.discovered_locations.get(game_state.location_id, {})
        current_scene_description = loc_data.get(
            "description", game_state.scene_description
        )
        npcs_in_current_loc = loc_data.get("npcs", game_state.npcs_present)
        events_in_current_loc = loc_data.get("events", game_state.events)

        npc_descriptions = []
        for npc in npcs_in_current_loc:
            # npc_data agora será um objeto NPC ou None
            npc_data: Optional[NPC] = game_state.known_npcs.get(npc)

            if npc_data:  # Verifica se npc_data é um objeto NPC
                prof = getattr(npc_data, "profession", "Desconhecido")
                pers = getattr(npc_data, "personality", "Indefinido")
            else:  # Fallback se o NPC não for encontrado ou não for um objeto NPC
                prof = "Desconhecido"
                pers = "Indefinido"
            npc_descriptions.append(f"{npc} (Profissão: {prof}, Personalidade: {pers})")
        npcs_text = ", ".join(npc_descriptions) if npc_descriptions else "Nenhum"

        events_text = (
            ", ".join(events_in_current_loc) if events_in_current_loc else "Nenhum"
        )

        return (
            f"Local atual: {location}\n"
            f"Descrição da cena: {current_scene_description}\n"
            f"NPCs presentes: {npcs_text}\n"
            f"Eventos ativos: {events_text}\n\n"
        )

    @staticmethod
    def _build_character_context(
        character: Character,
    ) -> str:
        """Builds the player character context part of the prompt."""
        # Use direct attributes from Character dataclass
        current_hp = character.current_hp
        max_hp = character.max_hp
        current_hunger = character.current_hunger
        max_hunger = character.max_hunger
        current_thirst = character.current_thirst
        max_thirst = character.max_thirst

        health_status = "saudável"
        if max_hp > 0:
            hp_percentage = (current_hp / max_hp) * 100
            if hp_percentage >= 98:
                health_status = "saudável"
            elif hp_percentage >= 75:
                health_status = "levemente ferido(a)"
            elif hp_percentage >= 40:
                health_status = "ferido(a)"
            else:
                health_status = "gravemente ferido(a)"

        hunger_status = "saciado(a)"
        if max_hunger > 0:
            hunger_percentage = (current_hunger / max_hunger) * 100
            if hunger_percentage <= 25:
                hunger_status = "faminto(a)"
            elif hunger_percentage <= 50:
                hunger_status = "com fome"

        thirst_status = "hidratado(a)"
        if max_thirst > 0:
            thirst_percentage = (current_thirst / max_thirst) * 100
            if thirst_percentage <= 25:
                thirst_status = "desidratado(a)"
            elif thirst_percentage <= 50:
                thirst_status = "com sede"

        return (
            "Personagem do jogador:\n"
            f"- Nome: {character.name}\n"
            f"- Nível: {character.level}\n"
            f"- Saúde: {current_hp}/{max_hp} (Estado: {health_status})\n"
            f"- Fome: {current_hunger}/{max_hunger} (Estado: {hunger_status})\n"
            f"- Sede: {current_thirst}/{max_thirst} (Estado: {thirst_status})\n\n"
        )

    @staticmethod
    def _build_combat_context(game_state: GameState, action: str, details: str) -> str:
        """Builds the combat context part of the prompt, if combat is active."""
        combat_context_str = ""
        if game_state.combat and game_state.combat.get("enemy"):
            enemy_data = game_state.combat.get("enemy")
            if isinstance(enemy_data, dict):
                enemy_name = enemy_data.get("name", "Inimigo Desconhecido")
                enemy_health = enemy_data.get("health", 0)
                enemy_max_health = enemy_data.get("max_health", enemy_health)
                combat_context_str += (
                    "Informações do Combate Atual:\n"
                    f"- Inimigo: {enemy_name}\n"
                    f"- HP do Inimigo: {enemy_health}/{enemy_max_health}\n"
                )
                if (
                    action.lower() == "attack"
                    and details
                    and any(
                        kw in details.lower() for kw in ["acertou", "errou", "derrotou"]
                    )
                ):
                    combat_context_str += (
                        f"- Resultado do último ataque do jogador: {details}\n\n"
                    )
                else:
                    combat_context_str += "\n"
        return combat_context_str

    @staticmethod
    def _build_recent_messages_context(game_state: GameState) -> str:
        """Builds the recent messages context part of the prompt."""
        recent_messages_str = ""
        recent_messages: List[MessageDict] = (
            game_state.messages[-5:] if game_state.messages else []
        )
        if recent_messages:
            messages_text = "\n".join(
                [
                    f"- {msg.get('role', 'unknown')}: {msg.get('content', '')}"
                    for msg in recent_messages
                ]
            )
            recent_messages_str = (
                f"Histórico recente da conversa (para contexto):\n{messages_text}\n\n"
            )
        return recent_messages_str

    @staticmethod
    def _build_action_specific_instructions(
        action: str,
        details: str,
        current_location: str,
        character: Character,
        game_state: GameState,
    ) -> str:
        instruction_parts = []
        action_lower = action.lower()

        if action_lower == "interpret":
            instruction_parts.append(
                InstructionsBuilder._build_interpret_instructions(
                    details, current_location, character, game_state
                )
            )
        elif action_lower in {"attack", "resolved", "success", "fail"}:
            instruction_parts.append(
                InstructionsBuilder._build_combat_or_result_instructions(
                    action, details, game_state
                )
            )
        elif action_lower == "narrate_roll_outcome":
            instruction_parts.append(
                InstructionsBuilder._build_roll_outcome_instructions(details)
            )
        else:  # Ações diretas
            instruction_parts.append(
                InstructionsBuilder._build_direct_action_instructions(action, details)
            )

        instruction_parts.append(
            InstructionsBuilder._get_sub_intent_guidelines(
                details, game_state, character
            )
        )
        instruction_parts.append(InstructionsBuilder._get_general_response_guidelines())
        instruction_parts.append(InstructionsBuilder._get_json_format_instructions())

        return "".join(instruction_parts)

    @classmethod
    def build_user_prompt_content(
        cls,
        action: str,
        details: str,
        character: Character,
        game_state: GameState,
    ) -> str:
        """
        Constructs the full user prompt content by assembling various context pieces.
        """
        user_prompt_parts = []

        user_prompt_parts.append(
            "Você é o Mestre de um RPG de apocalipse zumbi. "
            "Mantenha o tom narrativo e imersivo em suas respostas. "
            "Os NPCs devem agir de forma lógica e consistente com suas profissões e o bom senso no contexto de sobrevivência. "
            "RESPONDA SEMPRE EM PORTUGUÊS DO BRASIL (pt-br).\n\n"
        )

        # Adiciona resumo da cena atual como reforço de cenário
        if game_state.scene_description:
            user_prompt_parts.append(
                f"Resumo do cenário atual: {game_state.scene_description}\n\n"
            )

        user_prompt_parts.append(cls._build_scene_context(game_state))
        user_prompt_parts.append(cls._build_character_context(character))
        user_prompt_parts.append(cls._build_combat_context(game_state, action, details))
        user_prompt_parts.append(cls._build_recent_messages_context(game_state))

        current_location_name = game_state.current_location or "Desconhecido"
        user_prompt_parts.append(
            cls._build_action_specific_instructions(
                action, details, current_location_name, character, game_state
            )
        )

        return "".join(user_prompt_parts)


class InstructionsBuilder:
    """
    Helper class to build specific parts of AI instructions.
    """

    @staticmethod
    def _build_interpret_instructions(
        details: str,
        current_location: str,
        character: Character,
        game_state: GameState,
    ) -> str:
        """Builds the AI's task instructions based on the action type."""
        action_instructions_parts = []
        # A verificação if action.lower() == "interpret" foi removida pois este método só é chamado nesse contexto.
        details_lower = details.lower() if isinstance(details, str) else ""
        movement_keywords = [
            "sair",
            "entrar",
            "ir para",
            "mover para",
            "seguir para",
            "voltar para",
            "norte",
            "sul",
            "leste",
            "oeste",
            "corredor",
            "exterior",
        ]
        is_movement_intent = any(
            keyword in details_lower for keyword in movement_keywords
        )

        if is_movement_intent:
            action_instructions_parts.append(
                f"Ação de Movimento do Jogador (interprete e execute): {details}\n"
                f"Localização Atual do Jogador (APÓS o movimento, definida pelo sistema): {current_location}\n\n"
                "SUA TAREFA (para movimento interpretado):\n"
                "1. NARRE A CHEGADA E O NOVO LOCAL: A 'Localização Atual do Jogador' já foi atualizada pelo sistema para o local onde o jogador chegou. Sua `message` DEVE descrever o jogador chegando a este local e o que ele vê e sente. É CRUCIAL que sua narrativa reflita a chegada ao local fornecido e NÃO um retorno ao local anterior ou qualquer confusão sobre a movimentação.\n"
                "2. ATUALIZE OS CAMPOS JSON PARA O NOVO LOCAL: No seu JSON de resposta:\n"
                "3. ATUALIZE OS CAMPOS JSON PARA O NOVO LOCAL: No seu JSON de resposta:\n"
                "   - `current_detailed_location` DEVE ser o nome detalhado do NOVO local para onde o jogador se moveu.\n"
                "   - `scene_description_update` DEVE ser a descrição do NOVO local.\n"
                "   - `interpreted_action_type` deve ser 'move'.\n"
                "   - `interpreted_action_details` deve conter informações sobre o movimento (ex: {'direction': 'saindo do abrigo', 'target_location_name': 'Corredor Externo'}).\n\n"
            )
        else:
            action_instructions_parts.append(
                f"Ação textual do jogador (interprete a intenção): {details}\n\n"
                "SUA TAREFA PRINCIPAL (quando a ação é 'interpret' e NÃO é explicitamente movimento):\n"
                "1. INTERPRETE A INTENÇÃO: Analise a 'Ação textual do jogador' para determinar a intenção principal. Categorize-a como uma das seguintes: 'look', 'talk', 'vocal_action', 'search', 'use_item', 'attack', 'flee', 'rest', 'skill', 'craft', 'custom_complex'.\n"
                "2. GERE A NARRATIVA: Com base na intenção interpretada, narre o resultado da ação como Mestre do Jogo. Aplique as 'Diretrizes Gerais para Resposta' e, se a intenção corresponder a uma das ações com 'SUB-DIRETRIZES PARA INTENÇÕES ESPECÍFICAS' abaixo, aplique essas sub-diretrizes também.\n"
                "3. INCLUA INTERPRETAÇÃO NO JSON: No seu JSON de resposta, além dos campos padrão, inclua 'interpreted_action_type' (a categoria que você escolheu) e 'interpreted_action_details' (um dicionário com parâmetros relevantes).\n\n"
            )
        return "".join(action_instructions_parts)

    @staticmethod
    def _build_combat_or_result_instructions(
        action: str, details: str, game_state: GameState
    ) -> str:
        action_instructions_parts = []
        if (
            action.lower() == "attack"
            and game_state.combat
            and game_state.combat.get("enemy")
        ):
            enemy_combat_data = game_state.combat.get("enemy")
            if isinstance(
                enemy_combat_data, dict
            ):  # Check if enemy_combat_data is a dict
                enemy_name = enemy_combat_data.get("name", "Inimigo")
                enemy_hp = enemy_combat_data.get("health", 0)
                enemy_max_hp = enemy_combat_data.get("max_health", enemy_hp)

                action_instructions_parts.append(
                    f"O jogador está em combate com {enemy_name}.\n"
                    f"Informações do Inimigo:\n"
                    f"- Nome: {enemy_name}\n"
                    f"- HP: {enemy_hp}/{enemy_max_hp}\n\n"
                    f"O jogador está realizando a ação de combate: '{details if details else action}'.\n\n"
                    "Narre o resultado desta ação de combate de forma vívida e brutal, enfatizando a luta pela sobrevivência. "
                    "Siga a INSTRUÇÃO DE FORMATAÇÃO DA RESPOSTA JSON abaixo.\n\n"
                )
            else:
                action_instructions_parts.append(
                    "O jogador está em combate, mas os detalhes do inimigo não estão claros.\n"
                )
        else:  # Lógica para outras ações resolvidas (resolved, success, fail)
            action_instructions_parts.append(
                f"Resultado da Ação Mecânica do Jogador (baseado em regras/dados): {details}\n\n"
                "SUA TAREFA PRINCIPAL (quando um resultado mecânico é fornecido):\n"
                "1. NARRE O RESULTADO: Use o 'Resultado da Ação Mecânica do Jogador' como base para sua narrativa. Descreva vividamente o que aconteceu no mundo do jogo.\n"
                "2. CONSEQUÊNCIAS IMEDIATAS: Descreva as consequências diretas e as reações do ambiente ou NPCs a este resultado mecânico.\n"
                "3. ATUALIZE A CENA: Forneça uma `scene_description_update` que reflita quaisquer mudanças no ambiente devido à ação.\n"
                "4. MANTENHA A COERÊNCIA: Siga as 'Diretrizes Gerais para Resposta'.\n"
                "NÃO re-interprete a intenção original do jogador se um resultado mecânico claro foi fornecido; sua tarefa é narrar esse resultado e suas implicações.\n\n"
            )
        return "".join(action_instructions_parts)

    @staticmethod
    def _build_roll_outcome_instructions(details: str) -> str:
        return (
            f"Resultado Mecânico de um Teste Recente: {details}\n\n"
            "SUA TAREFA: Narre vividamente o que aconteceu no mundo do jogo com base neste resultado de teste. Descreva as consequências e reações. Siga as 'Diretrizes Gerais para Resposta'.\n\n"
        )

    @staticmethod
    def _build_direct_action_instructions(action: str, details: str) -> str:
        instruction_parts = []
        instruction_parts.append(f"Ação atual do jogador (direta): {action}")
        if details:
            instruction_parts.append(f" (Detalhes: {details})")
        instruction_parts.append("\n\n")
        return "".join(instruction_parts)

    @staticmethod
    def _get_sub_intent_guidelines(
        details: str, game_state: GameState, character: Character
    ) -> str:
        sub_intent_parts = [
            "SUB-DIRETRIZES PARA INTENÇÕES ESPECÍFICAS (aplique se relevante para a intenção que você interpretou ou para a ação direta fornecida):\n"
            "INTENÇÃO 'search': Descreva o que **o jogador (personagem)** encontra (ou não encontra) com base no ambiente e nos detalhes da busca. "
            "Seja criativo e considere o que faria sentido **ele** encontrar em um local como este. "
            "Pode ser algo útil, inútil, perigoso, ou apenas pistas sobre o que aconteceu que **ele** descobre.\n\n"
            "INTENÇÃO 'look': Se houver um alvo específico nos detalhes da ação do jogador, descreva em detalhes o que **o jogador (personagem)** observa sobre esse alvo. "
            "Forneça informações visuais, pistas ou qualquer coisa relevante que **ele** perceba. Se for um olhar geral ao ambiente, descreva o que **o jogador** nota ou como **ele** percebe a cena atualizada.\n\n"
            "INTENÇÃO 'move': Descreva a transição para o novo local ou a tentativa de movimento. "
            "Se o movimento for para um local conhecido, reforce a descrição com novos detalhes ou mudanças. "
            "Se for uma tentativa de ir a um local desconhecido ou bloqueado, descreva o obstáculo ou a razão pela qual o movimento não é simples.\n\n"
        ]

        talk_prompt_parts = []
        talk_prompt_parts.append(
            "INTENÇÕES 'talk' (diálogo), PERGUNTAS, ou 'vocal_action' (ação vocal genérica):\n"
        )
        talk_prompt_parts.append(
            "   Se a 'Ação textual do jogador' contiver um ponto de interrogação (?) OU começar com palavras como 'Quem', 'O quê', 'Onde', 'Quando', 'Por que', 'Como', 'Será que', 'Você acha que' E a intenção interpretada for 'talk':\n"
        )
        talk_prompt_parts.append(
            "     - Identifique o NPC mais apropriado para responder à pergunta com base no contexto da conversa, no histórico recente (especialmente as últimas falas) e no conhecimento esperado do NPC.\n"
        )
        talk_prompt_parts.append(
            "     - A resposta do NPC DEVE ser uma tentativa direta e FOCADA de responder à pergunta do jogador, considerando o TÓPICO IMEDIATAMENTE ANTERIOR da conversa. Se a pergunta do jogador for uma continuação de um diálogo, a resposta DEVE ser sobre esse problema específico. **CRÍTICO: EVITE REPETIR informações que o NPC já forneceu sobre esse tópico nas últimas interações.** Se o jogador perguntar novamente sobre algo já dito, o NPC deve adicionar um novo detalhe, expressar impaciência (se condizente com a personalidade), perguntar por que o jogador está perguntando de novo, ou sutilmente indicar que já respondeu, em vez de simplesmente repetir a informação palavra por palavra. EVITE que o NPC mude de assunto abruptamente ou responda de forma genérica se a pergunta for específica e contextualizada pela conversa anterior. EVITE que o NPC faça a mesma pergunta de volta ao jogador ou a outros NPCs, a menos que seja uma pergunta retórica clara e intencional para provocar reflexão (e isso deve ser raro e justificado pela personalidade do NPC).\n"
        )
        talk_prompt_parts.append(
            "     - Se nenhum NPC presente puder responder, a narrativa pode indicar isso (ex: 'Ninguém parece saber a resposta.' ou 'A Médica de Campo balança a cabeça, incerta.' ou 'O Velho Sobrevivente dá de ombros, claramente sem saber.').\n"
        )
        talk_prompt_parts.append(
            "     - A resposta DEVE ser consistente com o papel, conhecimento e personalidade do NPC. Exemplo: Uma médica não perguntaria ao jogador sobre o prognóstico de um paciente que ela está tratando; ela daria sua avaliação ou expressaria incerteza se fosse o caso.\n"
        )
        talk_prompt_parts.append(
            "     - Se a pergunta for direcionada a um NPC específico (ex: 'Médica, ele vai ficar bem?'), a resposta deve vir primariamente daquele NPC.\n"
        )
        talk_prompt_parts.append(
            "   Senão, se a intenção for 'talk' (tentativa de conversa direta com um NPC específico, não sendo uma pergunta direta já tratada acima):\n"
        )
        talk_prompt_parts.append(
            "     Você está controlando um NPC em uma conversa. Crie uma interação realista, **progressiva** e envolvente que:\n"
        )
        talk_prompt_parts.append(
            "     1. Reflita a personalidade, o estado emocional (medo, desconfiança, esperança) e a atitude do NPC no contexto de um apocalipse zumbi.\n"
        )
        talk_prompt_parts.append(
            "     2. Use informações prévias se o jogador já interagiu com este NPC.\n"
        )
        talk_prompt_parts.append(  # MODIFICADO
            "     3. Revele detalhes **NOVOS ou adicionais** sobre o mundo devastado, perigos imediatos, rumores, necessidades de sobrevivência ou possíveis missões/trocas. **CRÍTICO: EVITE REPETIR informações que este NPC já deu ao jogador nas últimas interações, a menos que o jogador peça explicitamente por um lembrete ou a repetição sirva a um propósito narrativo claro (ex: ênfase devido à gravidade, ou se o NPC for senil). Se o jogador insistir em um tópico já coberto, o NPC pode mostrar sinais de impaciência ou confusão.**\n"
        )
        talk_prompt_parts.append(
            "     4. Mantenha consistência com interações anteriores.\n"
        )
        talk_prompt_parts.append(
            "     5. Permita que o jogador faça escolhas significativas.\n"
        )

        if details and isinstance(details, str) and details in game_state.known_npcs:
            npc_data = game_state.known_npcs[details]
            talk_prompt_parts.append(
                PromptBuilder._format_npc_details_for_prompt(details, npc_data)
            )

        talk_prompt_parts.append(
            f"\nO jogador está tentando conversar com '{details if details else 'um NPC próximo'}'. "
            "Crie um diálogo realista e interessante que desenvolva a narrativa, a tensão e o mundo pós-apocalíptico do jogo.\n"
        )

        talk_prompt_parts.append(
            "   Senão, if a intenção for 'vocal_action' (ex: 'Gritar MUITO ALTO', 'Sussurrar', 'Chamar por ajuda', 'Cantar uma música triste') e NÃO uma tentativa de conversa direta com um NPC ou uma pergunta:\n"
        )
        talk_prompt_parts.append(
            "     - Primeiro, RESPEITE a intensidade da ação vocal descrita pelo jogador. Se o jogador diz 'Gritar MUITO ALTO', o som É muito alto e perceptível. Não o atenue ou descreva como 'amortecido' arbitrariamente, a menos que o ambiente (ex: dentro de um cofre à prova de som que o jogador conhece) justifique explicitamente e o jogador já tenha essa informação contextual.\n"
        )
        talk_prompt_parts.append(
            "     - Descreva o efeito físico imediato dessa ação no ambiente (ex: o som ecoa agudamente, poeira cai do teto, objetos próximos vibram).\n"
        )
        talk_prompt_parts.append(
            "     - Em seguida, conecte IMEDIATAMENTE esta ação à diretriz geral '11. CONSEQUÊNCIAS DE RUÍDO'. As reações dos NPCs DEVEM refletir o perigo de atrair atenção indesejada (zumbis, saqueadores). Eles devem parecer visivelmente alarmados, podem repreender o jogador com urgência (ex: 'Você quer nos matar?! Fique quieto!'), gesticular freneticamente por silêncio, olhar nervosamente para as saídas, ou até mesmo se preparar para um possível ataque/invasão. Evite que os NPCs iniciem um diálogo casual ou façam perguntas simples como 'O que foi isso?'. Suas reações devem ser de medo, raiva pela imprudência, ou pânico.\n"
        )
        talk_prompt_parts.append(
            "     - O foco da sua narrativa deve ser na tensão criada, no perigo iminente percebido, e na reação de alerta/pânico dos NPCs, não em iniciar uma nova conversa. A reação deve ser natural para sobreviventes experientes (ou apavorados) em um mundo hostil.\n"
        )
        talk_prompt_parts.append(
            "   Senão, if a intenção for 'talk' mas sem detalhes específicos ou alvo claro (jogador apenas indicou querer falar de forma geral):\n"
        )
        talk_prompt_parts.append(
            "     Descreva se algum NPC próximo toma a iniciativa de falar com o jogador, ou se o ambiente permanece em silêncio aguardando uma ação mais específica. Se houver NPCs, um deles pode perguntar 'Você disse alguma coisa?' ou 'Precisa de algo?'.\n"
        )
        talk_prompt_parts.append(
            "   Se os detalhes para 'talk' ou 'vocal_action' forem vagos ou sem sentido, aplique a diretriz geral '9. AÇÕES OU DETALHES IMPRECISOS/IRRELEVANTES'.\n\n"
        )

        sub_intent_parts.append("".join(talk_prompt_parts))

        sub_intent_parts.append(
            "INTENÇÃO 'use_item': Descreva o resultado de usar o item especificado. Se for um consumível, descreva a sensação ou efeito. "
            "Se for uma ferramenta, descreva a ação e seu sucesso ou falha. "
            "Se for um item de quest, revele alguma informação ou consequência.\n\n"
            "   - Se o item for uma FERRAMENTA ou ARMA (ex: 'Pé de Cabra', 'Faca'), e a ação for simplesmente 'usar [nome do item]', "
            "     interprete como EQUIPAR o item, se aplicável, ou prepará-lo para uso. "
            "     NÃO assuma que o jogador está tentando se curar com uma ferramenta, a menos que a descrição do item explicitamente diga que ele tem propriedades curativas. "
            "     A narrativa deve focar na ação de equipar ou preparar a ferramenta.\n\n"
            "INTENÇÃO 'attack': Se não houver combate ativo, descreva o jogador se preparando para o combate ou atacando o alvo especificado (ou o mais óbvio), iniciando a confrontação. Se o combate já estiver ativo, descreva o resultado do ataque contra o inimigo atual.\n\n"
            "INTENÇÃO 'flee': Descreva a tentativa de fuga. Foi bem-sucedida? Houve perigos ou obstáculos? "
            "A fuga levou o personagem a uma situação melhor ou pior? "
            "Mantenha a tensão e o realismo do apocalipse zumbi.\n\n"
            "INTENÇÃO 'rest': Descreva a tentativa de descanso. O local é seguro o suficiente? "
            "O personagem consegue realmente descansar ou é interrompido? Quais são os riscos? "
            "Descreva quaisquer efeitos de recuperação ou, ao contrário, a impossibilidade de descansar devido ao perigo.\n\n"
            "INTENÇÃO 'custom_complex' ou outras não listadas: Interprete esta ação no contexto do jogo de apocalipse zumbi. "
            "Descreva o resultado da ação do jogador de forma criativa e coerente com o ambiente e a situação. "
            "Considere as possíveis consequências, sucessos ou falhas.\n\n"
        )
        return "".join(sub_intent_parts)

    @staticmethod
    def _get_general_response_guidelines() -> str:
        return (
            "Diretrizes Gerais para Resposta (aplique sempre...):\n"
            "1. **FOCO NA AÇÃO DO JOGADOR:** Sua resposta deve focar PRIMARIAMENTE no resultado direto e nas consequências imediatas da ação do jogador ('Ação atual do jogador'). **Ao descrever o que o jogador faz ou percebe como resultado direto de sua ação, narre do ponto de vista do jogador (ex: 'Você percebe que...', 'Você encontra...', 'Você consegue...').** NPCs podem reagir ou comentar *depois* que a ação do jogador e sua percepção inicial forem descritas.\n"
            "2. **PROGRESSÃO E CONTEXTO DA CONVERSA, ESTADO DO PERSONAGEM:**\n"  # MODIFICADO
            "   - Use o 'Histórico recente da conversa', especialmente a ÚLTIMA INTERAÇÃO DO JOGADOR E AS ÚLTIMAS FALAS DOS NPCs, para entender o foco atual e o tópico da conversa. A resposta do NPC deve ser uma continuação lógica e direta disso, **ADICIONANDO NOVAS INFORMAÇÕES OU PERSPECTIVAS, OU REAGINDO DE FORMA DIFERENTE SE O JOGADOR REPETIR UMA AÇÃO/PERGUNTA.** Evite que NPCs mudem de assunto abruptamente ou **REPITAM EXATAMENTE o que já foi dito por eles mesmos ou por outros NPCs nas últimas interações, a menos que seja para dar ênfase ou se o jogador pedir para repetir.**\n"
            "   - **CRUCIAL: CONSIDERE O ESTADO ATUAL DO PERSONAGEM (Saúde, Fome, Sede, etc., fornecidos no prompt).** Sua narrativa e as reações dos NPCs DEVEM ser consistentes com esses status. Não descreva o personagem como 'gravemente ferido' se a Saúde estiver alta. NPCs não devem oferecer cura se o personagem estiver saudável, ou comida se estiver saciado, a menos que seja parte de um engano ou uma situação muito específica justificada pela narrativa.\n\n"
            "3. **PROGRESSÃO NARRATIVA:** Faça a narrativa progredir. Ações devem ter impacto. Se um inimigo é atacado, descreva o dano e a reação de forma crível. Evite situações onde o estado do inimigo se 'reseta' magicamente a menos que seja uma habilidade especial.\n\n"
            "4. **EVITE REPETIÇÃO ATMOSFÉRICA:** Evite repetir excessivamente descrições atmosféricas (como o estado do ar, cheiros, ou a luz piscando) a menos que tenham mudado significativamente devido à ação do jogador ou a um novo evento importante. Mencione-os brevemente se relevante para a ação atual, mas não os torne o foco principal repetidamente.\n"
            "5. **CONSISTÊNCIA E TOM:** Mantenha a consistência com o mundo pós-apocalíptico, a descrição do local, os NPCs presentes e o tom de um RPG de apocalipse zumbi (perigo, escassez, desconfiança, mas com lampejos de esperança ou mistério).\n"
            "   Os NPCs devem usar ferramentas e conhecimentos apropriados à sua profissão e à situação. Por exemplo, uma médica não usaria um termômetro para verificar a potabilidade da água, mas poderia procurar por kits de teste de contaminação ou ferver a água.\n"
            "6. **ESPECIFICIDADE:** Evite respostas genéricas. Seja específico sobre o que é (ou não é) encontrado, visto ou o resultado da ação.\n"
            "7. **DETALHES SENSORIAIS COM MODERAÇÃO:** Use detalhes sensoriais (visão, audição, olfato, tato) para aumentar a imersão, mas apenas quando adicionarem valor à descrição da ação ou mudança de estado, não como preenchimento.\n"
            "8. **INTERPRETAÇÃO DE AÇÕES VAGAS:** Se a ação do jogador for vaga, interprete-a da forma mais interessante para a narrativa, usando o contexto do histórico recente e as informações de combate (se houver) como guia principal.\n"
            "9. **AÇÕES OU DETALHES IMPRECISOS/IRRELEVANTES:** Se a 'Ação atual do jogador' ou os 'Detalhes' fornecidos pelo jogador parecerem não fazer sentido no contexto do jogo, forem frases aleatórias, comentários fora de personagem, ou não especificarem claramente um alvo ou intenção quando necessário (ex: 'usar item' sem dizer qual item, 'mover' sem direção clara), sua 'message' deve refletir que o Mestre (você) não compreendeu a intenção do jogador ou que a ação não teve um efeito prático no ambiente. Não tente criar uma narrativa para ações sem sentido ou vagas demais. Você pode responder com algo como 'Não entendi o que você quis dizer com isso.' ou 'Isso não parece ter nenhum efeito aqui.'\n"
            "10. **ENVOLVIMENTO DE NPCs:** Descreva a reação ou envolvimento de outros NPCs presentes *apenas se a ação do jogador os afetar diretamente, se eles teriam uma reação natural e imediata ao resultado da ação do jogador, ou se o jogador interagir diretamente com eles*. Caso contrário, mantenha o foco narrativo no jogador e no ambiente imediato da ação.\n"
            "11. **CONSEQUÊNCIAS DE RUÍDO:** Em um mundo pós-apocalíptico, barulhos altos (gritos, tiros, explosões, máquinas barulhentas) são inerentemente perigosos, pois podem atrair zumbis ou sobreviventes hostis. Suas descrições e as reações dos NPCs a ações barulhentas DEVEM refletir essa tensão e perigo. NPCs podem ficar visivelmente alarmados, repreender o jogador por fazer barulho desnecessário, sugerir silêncio, ou até mesmo tomar medidas defensivas. A narrativa pode sutilmente sugerir o risco de atenção indesejada (ex: 'um silêncio tenso se segue ao seu grito, quebrado apenas pelo som distante de algo se arrastando').\n"
            "\n"
            "12. **SUGESTÃO DE TESTES (ROLAGENS DE DADOS):** Se a 'Ação textual do jogador' (quando a ação é 'interpret') descrever uma tentativa que claramente envolve risco, desafio físico, social ou mental que não é automaticamente resolvido (ex: tentar arrombar uma porta trancada, escalar uma parede difícil, persuadir um guarda cético, decifrar um texto antigo), você DEVE incluir um objeto `suggested_roll` no seu JSON de resposta. Este objeto deve conter:\n"
            "    - `description`: (string) Uma breve descrição da ação que requer o teste (ex: 'Arrombar a porta do cofre', 'Persuadir o guarda a deixá-lo passar').\n"
            "    - `attribute`: (string) O atributo principal para o teste (ex: 'strength', 'dexterity', 'charisma', 'intelligence', 'wisdom').\n"
            "    - `skill`: (string, opcional) Uma perícia específica, se aplicável (ex: 'acrobatics', 'stealth', 'persuasion', 'investigation'). Se nenhuma perícia específica se aplicar, use `null` ou omita.\n"
            "    - `dc`: (integer) A Classe de Dificuldade (CD) sugerida para o teste. Use seu julgamento: Fácil (10-12), Médio (13-15), Difícil (16-18), Muito Difícil (19-20+).\n"
            "    - `reasoning`: (string, opcional) Uma breve justificativa para a CD sugerida (ex: 'A porta parece reforçada', 'O guarda é notoriamente teimoso').\n"
            "   Se você sugerir um `suggested_roll`, sua `message` principal deve descrever o jogador iniciando a tentativa, mas SEM o resultado final, pois o resultado dependerá da rolagem de dados que será feita pelo sistema do jogo. Ex: 'Você se prepara para tentar arrombar a porta do cofre. Parece bem resistente...'\n"
            "   NÃO sugira rolagens para ações triviais ou que já são cobertas por mecânicas simples (como um 'look' básico ou um 'move' para uma área adjacente aberta).\n\n"
            "13. **ELEMENTOS INTERATIVOS:** Ao descrever uma `current_detailed_location` e sua `scene_description_update`, identifique de 2 a 4 elementos, objetos ou pequenas áreas de interesse chave DENTRO dessa sub-localização específica. Liste os nomes desses elementos no campo `interactable_elements` da sua resposta JSON. Estes são itens que o jogador poderia querer examinar mais de perto ou interagir. Mantenha os nomes concisos e diretos (ex: 'Mesa de Operações', 'Armário de Remédios', 'Cama de Paciente').\n"
        )

    @staticmethod
    def _get_json_format_instructions() -> str:
        return (
            "INSTRUÇÃO DE FORMATAÇÃO DA RESPOSTA:\n"
            "RESPONDA SEMPRE E APENAS com uma string JSON válida, SEM QUALQUER TEXTO ADICIONAL ANTES OU DEPOIS DO JSON (incluindo markdown como ```json ou ```).\n"
            "- `message`: (string) Sua descrição narrativa principal da cena e do resultado da ação do jogador (em pt-br). Integre a percepção de novos `interactable_elements` de forma natural na narrativa, se possível, além de listá-los no campo apropriado.\n"
            "- `current_detailed_location`: (string) O nome detalhado da localização atual do jogador, incluindo a sub-área específica dentro do local principal (ex: 'Abrigo Subterrâneo - Sala Principal', 'Floresta Sombria - Clareira Escondida'). Se o jogador se mover para um novo local principal (ex: de 'Floresta' para 'Abrigo Subterrâneo'), determine um ponto de entrada lógico para este novo local principal (ex: 'Pátio de Entrada', 'Corredor de Acesso', 'Garagem Empoeirada') e use-o como a sub-área em `current_detailed_location` (ex: 'Abrigo Subterrâneo - Pátio de Entrada'). (em pt-br)\n"
            "- `scene_description_update`: (string) Uma nova descrição concisa para a cena/sub-área atual (o `current_detailed_location`), focando nos elementos estáticos e ambientais importantes que o jogador perceberia. (em pt-br)\n"
            "- `success`: (boolean) Sempre `true` se você puder gerar uma resposta narrativa. Use `false` apenas em caso de um erro interno seu ao processar o pedido (o que deve ser raro).\n\n"
            "- `interpreted_action_type`: (string, opcional mas PREFERÍVEL) A categoria da intenção que você interpretou (ex: 'move', 'talk', 'vocal_action', 'search', 'custom_complex').\n"
            "- `interpreted_action_details`: (object, opcional mas PREFERÍVEL) Um dicionário com parâmetros relevantes para a ação interpretada (ex: {'direction': 'norte'}, {'target_npc': 'NomeDoNPC'}, {'item_name': 'Bandagem', 'vocal_text': 'Gritar muito alto'}).\n\n"
            "- `suggested_roll`: (object, opcional) Se a ação do jogador ('interpret') justificar um teste, inclua este objeto com os campos `description`, `attribute`, `skill` (opcional), `dc`, `reasoning` (opcional).\n\n"
            "- `interactable_elements`: (list[string], opcional) Uma lista de 2-4 nomes de elementos ou sub-áreas chave dentro da `current_detailed_location` com os quais o jogador pode interagir (ex: ['Mesa de Operações', 'Armário de Remédios', 'Cama de Paciente']). Mantenha os nomes concisos e diretos.\n\n"
            "Exemplo de JSON de resposta para uma ação textual 'Gritar muito alto!' no 'Abrigo Subterrâneo - Sala Principal':\n"
            "```json\n"
            "{\n"
            '  "message": "Você solta um grito agudo que ecoa terrivelmente pelo abrigo! O Velho Sobrevivente Cansado se encolhe e sibila: \\"Cale a boca, imbecil! Quer que todos os mortos da cidade venham bater à nossa porta?!\\". A Médica de Campo empalidece, olhando para a entrada com puro terror. Ao seu redor, você nota o Portão de Metal Reforçado, uma Enfermaria Improvisada e o Gerador Barulhento.",\n'
            '  "current_detailed_location": "Abrigo Subterrâneo - Sala Principal",\n'
            '  "scene_description_update": "A sala principal do abrigo é fria e úmida. A tensão é palpável após o grito; os sobreviventes estão em alerta máximo.",\n'
            '  "success": true,\n'
            '  "interpreted_action_type": "vocal_action",\n'
            '  "interpreted_action_details": {"vocal_text": "Gritar muito alto!"},\n'
            '  "interactable_elements": ["Portão de Metal Reforçado", "Enfermaria Improvisada", "Gerador Barulhento"]\n'
            "}\n"
            "```\n"
        )
