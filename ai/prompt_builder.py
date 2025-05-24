# filepath: c:\Users\rodri\Desktop\REPLIT RPG\ai\prompt_builder.py
"""
Módulo para construir prompts para o modelo de IA.
"""
from ai.game_ai_client import GameAIClient
from ai.schemas import AIResponsePydantic
from typing import TypedDict, NotRequired, List, Optional, Dict  # Adicionado Dict
from core.npc import NPC  # Importar a classe NPC
from core.models import Character  # Importar Character do models
from core.game_state_model import GameState, MessageDict


class PromptBuilder:
    """
    Gerencia a construção dos prompts a serem enviados ao modelo de IA.
    """

    @staticmethod
    def _format_npc_details_for_prompt(npc_name: str, npc_data: NPC) -> str:
        """
        Formata os detalhes do NPC para inclusão no prompt.
        (Adaptado de prompt_manager.py)
        """
        # Acesso direto aos atributos do objeto NPC
        profession = (
            npc_data.profession if npc_data.profession else "Profissão Desconhecida"
        )
        personality = (
            npc_data.personality if npc_data.personality else "Personalidade Variada"
        )

        # Formato mais conciso, incluindo profissão e personalidade no cabeçalho.
        npc_info_str = f"\nDetalhes sobre {npc_name} (Profissão: {profession}, Personalidade: {personality}):\n"

        if npc_data.knowledge:
            npc_info_str += f"- Conhecimento: {', '.join(npc_data.knowledge)}\n"
        return npc_info_str

    @staticmethod
    def build_system_prompt() -> str:
        """Constrói o prompt estático do sistema."""
        return (
            "Você é o Mestre de um jogo de RPG ambientado em um mundo pós-apocalíptico. "
            "Seu papel é narrar com riqueza de detalhes o ambiente, as consequências das ações do jogador, e interpretar os NPCs de forma viva, única e coerente. "
            "Nunca diga que o jogador 'não especificou'; aja com bom senso e interprete a intenção do jogador para manter a narrativa fluindo. "  # noqa
            "Seja imersivo e criativo. Se algo for ambíguo, improvise com lógica e drama, mantendo o jogo em andamento. "
            "RESPONDA SEMPRE EM PORTUGUÊS DO BRASIL (pt-br).\n\n"
            "REGRAS IMPORTANTES PARA VOCÊ (O MESTRE):\n"
            "- NUNCA CONTRADIGA FATOS JÁ ESTABELECIDOS (presentes no resumo ou histórico recente).\n"
            "- MANTENHA SEMPRE O TOM SOMBRIO E DETALHADO de um apocalipse zumbi.\n"
            "- USE NO MÁXIMO 2-3 PARÁGRAFOS CURTOS para descrever cenas ou resultados de ações, a menos que uma grande revelação ou um novo local esteja sendo introduzido.\n"
            "- Suas respostas devem ser cinematográficas, envolventes e sempre progredir a narrativa.\n"
            "- FOCO NA AÇÃO ATUAL: Concentre-se na ação mais recente do jogador. Evite se desviar para elementos de interações passadas, a menos que explicitamente referenciados pelo jogador na ação atual.\n"
            "- EVITE REPETIÇÕES: Não repita informações que você ou NPCs já forneceram recentemente, a menos que o jogador peça ou seja para dar ênfase crítica.\n"
            "- FORMATO JSON: Sua resposta DEVE ser um JSON válido conforme as instruções detalhadas fornecidas abaixo."
        )

    @staticmethod
    def _build_scene_context(game_state: GameState) -> str:
        """Constrói a parte do prompt referente ao contexto da cena."""
        location = game_state.current_location or "Desconhecido"
        # Usando .get() com um dicionário vazio como padrão para robustez
        loc_data = game_state.discovered_locations.get(game_state.location_id, {})
        current_scene_description = loc_data.get(
            "description", game_state.scene_description
        )
        # Prioriza 'npcs' de loc_data, fallback para game_state.npcs_present
        npcs_in_current_loc_names = loc_data.get("npcs", game_state.npcs_present)
        # Prioriza 'events' de loc_data, fallback para game_state.events
        events_in_current_loc = loc_data.get("events", game_state.events)

        npc_descriptions = []
        for npc_name_in_scene in npcs_in_current_loc_names:
            npc_data: Optional[NPC] = game_state.known_npcs.get(npc_name_in_scene)

            if npc_data:
                prof = npc_data.profession if npc_data.profession else "Desconhecido"
                pers = npc_data.personality if npc_data.personality else "Indefinido"
                npc_descriptions.append(
                    f"{npc_data.name} (Profissão: {prof}, Personalidade: {pers})"
                )
            else:
                # Se os dados do NPC não forem encontrados, usa o nome diretamente da lista
                npc_descriptions.append(
                    f"{npc_name_in_scene} (Profissão: Desconhecido, Personalidade: Indefinido)"
                )

        npcs_text = ", ".join(npc_descriptions) if npc_descriptions else "Nenhum"
        events_text = (
            ", ".join(events_in_current_loc) if events_in_current_loc else "Nenhum"
        )

        return (
            f"CENA ATUAL:\n"
            f"- Local: {location}\n"
            f"- Descrição: {current_scene_description}\n"
            f"- NPCs Presentes: {npcs_text}\n"
            f"- Eventos Ativos: {events_text}\n\n"
        )

    @staticmethod
    def _build_character_context(character: Character) -> str:
        """Constrói a parte do prompt referente ao contexto do personagem jogador."""
        current_hp = character.stats.current_hp
        max_hp = character.stats.max_hp
        current_hunger = character.survival_stats.hunger
        max_hunger = 100  # Baseado no padrão de SurvivalStats
        current_thirst = character.survival_stats.thirst
        max_thirst = 100  # Baseado no padrão de SurvivalStats

        def _get_status(
            current: int,
            max_val: int,
            depleted_percent: int,
            mid_percent: int,
            depleted_str: str,
            mid_str: str,
            healthy_str: str,
            undefined_str: str,
        ) -> str:
            """Função auxiliar para determinar o status com base na porcentagem."""
            if max_val > 0:
                percentage = (current / max_val) * 100
                if percentage <= depleted_percent:
                    return depleted_str
                elif percentage <= mid_percent:
                    return mid_str
                else:
                    return healthy_str
            return undefined_str

        health_status = _get_status(
            current_hp,
            max_hp,
            40,
            75,
            "gravemente ferido(a)",
            "ferido(a)",
            "saudável",
            "estado de saúde indefinido",
        )
        # Caso especial para HP <= 0
        if current_hp <= 0:
            health_status = "incapacitado(a) ou morto(a)"

        hunger_status = _get_status(
            current_hunger,
            max_hunger,
            25,
            50,
            "faminto(a)",
            "com fome",
            "saciado(a)",
            "estado de fome indefinido",
        )
        thirst_status = _get_status(
            current_thirst,
            max_thirst,
            25,
            50,
            "desidratado(a)",
            "com sede",
            "hidratado(a)",
            "estado de sede indefinido",
        )

        return (
            "SOBRE O PERSONAGEM DO JOGADOR:\n"
            f"- Nome: {character.name}\n"
            f"- Nível: {character.level}\n"
            f"- Saúde: {current_hp}/{max_hp} (Estado: {health_status})\n"
            f"- Fome: {current_hunger}/{max_hunger} (Estado: {hunger_status})\n"
            f"- Sede: {current_thirst}/{max_thirst} (Estado: {thirst_status})\n\n"
        )

    @staticmethod
    def _build_combat_context(game_state: GameState, action: str, details: str) -> str:
        """Constrói a parte do prompt referente ao contexto de combate, se o combate estiver ativo."""
        combat_context_str = ""
        # Verifica se o combate está ativo e se existe uma instância de inimigo
        if game_state.combat and game_state.combat.get("active"):
            # Acessa 'enemy' de forma segura usando .get()
            enemy_instance = game_state.combat.get("enemy")

            if enemy_instance:  # Verifica se o inimigo foi realmente retornado
                enemy_name = enemy_instance.name
                enemy_health = enemy_instance.current_hp
                enemy_max_health = enemy_instance.max_hp

                combat_context_str += (
                    "INFORMAÇÕES DO COMBATE ATUAL:\n"
                    f"- Inimigo: {enemy_name}\n"
                    f"- HP do Inimigo: {enemy_health}/{enemy_max_health}\n"
                )
                # Adiciona o resultado específico do ataque, se aplicável
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
        """Constrói a parte do prompt referente ao histórico de mensagens recentes."""
        recent_messages_str = ""
        # Pega as últimas 5 mensagens, garantindo que game_state.messages não seja None
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
            recent_messages_str = f"HISTÓRICO RECENTE DA CONVERSA (ÚLTIMAS {len(recent_messages)} INTERAÇÕES):\n{messages_text}\n\n"
        return recent_messages_str

    @staticmethod
    def _build_action_specific_instructions(
        action: str,
        details: str,
        current_location: str,
        character: Character,
        game_state: GameState,
    ) -> str:
        """Constrói as instruções específicas da ação com base na ação do jogador."""
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
        else:  # Ações diretas como 'look', 'search', 'use_item'
            instruction_parts.append(
                InstructionsBuilder._build_direct_action_instructions(action, details)
            )

        # Estas diretrizes são geralmente aplicáveis a todos os tipos de ação
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
        Constrói o conteúdo completo do prompt do usuário, reunindo várias partes do contexto.
        """
        user_prompt_parts = []

        user_prompt_parts.append(
            "INSTRUÇÕES GERAIS PARA O MESTRE (VOCÊ):\n"
            "Mantenha o tom narrativo e imersivo em todas as respostas. "
            "Os NPCs devem agir de forma lógica e consistente com suas profissões e o bom senso no contexto de sobrevivência. "
            "RESPONDA SEMPRE EM PORTUGUÊS DO BRASIL (pt-br).\n\n"
        )

        if game_state.scene_description:
            user_prompt_parts.append(
                f"Resumo do cenário atual: {game_state.scene_description}\n\n"
            )

        # Adicionar resumo da memória longa, se existir
        if game_state.summary:
            user_prompt_parts.append(
                f"RESUMO DOS EVENTOS IMPORTANTES ATÉ AGORA:\n{game_state.summary}\n\n"
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

    @classmethod
    def build_summary_generation_prompt(
        cls, game_state: GameState
    ) -> List[Dict[str, str]]:
        """
        Constrói o prompt para a IA gerar um resumo da memória de longo prazo e eventos recentes.
        """
        info_to_summarize_parts = []
        if game_state.long_term_memory:
            info_to_summarize_parts.append("Fatos Chave Conhecidos:")
            for key, value in game_state.long_term_memory.items():
                info_to_summarize_parts.append(
                    f"- {key.replace('_', ' ').capitalize()}: {value}"
                )

        if game_state.messages:
            info_to_summarize_parts.append(
                "\nEventos Recentes Importantes (últimas 5-10 interações):"
            )
            relevant_messages = [
                f"{msg['role']}: {msg['content']}"
                for msg in game_state.messages[-10:]
                if msg["role"] in ["assistant", "system"]
                or "user" in msg["role"].lower()
            ]
            info_to_summarize_parts.extend(relevant_messages)

        summary_prompt_user_content = (
            "Com base nos seguintes fatos e eventos recentes do jogo de RPG de apocalipse zumbi, "
            "gere um resumo CONCISO (1 a 3 frases curtas) dos acontecimentos mais importantes e do estado atual do jogador/mundo. "
            "Este resumo será usado para dar contexto ao Mestre de Jogo (IA) nas próximas interações. "
            "Foque em informações que afetam a progressão da história ou decisões futuras.\n\n"
            "INFORMAÇÕES PARA RESUMIR:\n"
            + "\n".join(info_to_summarize_parts)
            + "\n\nRESUMO CONCISO (1-3 frases):"
        )

        summary_system_prompt = (
            "Você é um assistente especializado em resumir informações de jogos de RPG "
            "de forma concisa para fornecer contexto a uma IA Mestre de Jogo. "
            "Sua resposta deve ser APENAS o texto do resumo, sem introduções ou frases adicionais."
        )
        return [
            {"role": "system", "content": summary_system_prompt},
            {"role": "user", "content": summary_prompt_user_content},
        ]


class InstructionsBuilder:
    """
    Classe auxiliar para construir partes específicas das instruções da IA.
    Esta classe é projetada especificamente para fornecer instruções detalhadas
    à IA com base na ação interpretada e no estado do jogo.
    """

    @staticmethod
    def _build_interpret_instructions(
        details: str,
        current_location: str,
        character: Character,
        game_state: GameState,
    ) -> str:
        """
        Constrói as instruções para a IA quando a ação do jogador precisa
        de interpretação (tipo de ação 'interpret').
        """
        action_instructions_parts = []
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
            "subir",
            "descer",
            "passar",
            "avançar",
            "recuar",
            "entrar em",
            "sair de",
            "caminhar para",  # Adicionado mais termos de movimento comuns
        ]
        is_movement_intent = any(
            keyword in details_lower for keyword in movement_keywords
        )

        if is_movement_intent:
            action_instructions_parts.append(
                f"AÇÃO DO JOGADOR (MOVIMENTO): {details}\n"
                f"Localização Atual do Jogador (APÓS o movimento, já definida pelo sistema): {current_location}\n\n"
                "SUA TAREFA (PARA MOVIMENTO INTERPRETADO):\n"
                "1. NARRE A CHEGADA E O NOVO LOCAL: A 'Localização Atual do Jogador' já foi atualizada pelo sistema para o local onde o jogador chegou. Sua `message` DEVE descrever o jogador chegando a este local e o que ele vê, ouve e sente. É CRUCIAL que sua narrativa reflita a chegada ao local fornecido e NÃO um retorno ao local anterior ou qualquer confusão sobre a movimentação.\n"
                "2. ATUALIZE OS CAMPOS JSON PARA O NOVO LOCAL (no seu JSON de resposta):\n"
                "   - `current_detailed_location`: DEVE ser o nome detalhado do NOVO local para onde o jogador se moveu (geralmente o mesmo que 'Localização Atual do Jogador' acima).\n"
                "   - `scene_description_update`: DEVE ser a descrição detalhada e atmosférica do NOVO local.\n"
                "   - `interpreted_action_type`: DEVE ser 'move'.\n"
                "   - `interpreted_action_details`: DEVE conter informações sobre o movimento (ex: {'direction': 'norte', 'target_location_name': 'Corredor Externo'}).\n"
                "   - `interactable_elements`: Liste 2-4 elementos interativos chave no NOVO local.\n\n"
            )
        else:
            action_instructions_parts.append(
                f"AÇÃO DO JOGADOR (TEXTUAL, NÃO MOVIMENTO DIRETO): {details}\n\n"
                "SUA TAREFA PRINCIPAL (quando a ação é 'interpret' e NÃO é explicitamente movimento):\n"
                "1. INTERPRETE A INTENÇÃO: Analise a 'Ação textual do jogador' para determinar a intenção principal, mesmo que contenha pequenos erros de digitação (ex: 'segur' em vez de 'segurar', 'abrri' em vez de 'abrir'). Foque nos verbos e objetos principais da frase completa do jogador. Categorize-a como uma das seguintes: 'look', 'talk', 'vocal_action', 'search', 'use_item', 'attack', 'flee', 'rest', 'skill', 'craft', 'custom_complex'.\n"
                "2. GERE A NARRATIVA: Com base na intenção interpretada, narre o resultado da ação como Mestre do Jogo. Sua narrativa DEVE focar nos elementos e ações mencionados DIRETAMENTE na 'Ação textual do jogador' para esta rodada. Evite trazer elementos de descrições de cena anteriores ou elementos interativos que não foram explicitamente mencionados pelo jogador nesta ação específica. Aplique as 'Diretrizes Gerais para Resposta' e, se a intenção corresponder a uma das ações com 'SUB-DIRETRIZES PARA INTENÇÕES ESPECÍFICAS' abaixo, aplique essas sub-diretrizes também.\n"
                "3. INCLUA INTERPRETAÇÃO NO JSON: No seu JSON de resposta, além dos campos padrão, inclua 'interpreted_action_type' (a categoria que você escolheu) e 'interpreted_action_details' (um dicionário com parâmetros relevantes).\n\n"
            )
        return "".join(action_instructions_parts)

    @staticmethod
    def _build_combat_or_result_instructions(
        action: str, details: str, game_state: GameState
    ) -> str:
        """
        Constrói instruções para a IA quando uma ação de combate ou uma ação mecânica
        resolvida (sucesso/falha) é fornecida.
        """
        action_instructions_parts = []
        # Verifica se o combate está ativo e se existe uma instância de inimigo
        if (
            action.lower() == "attack"
            and game_state.combat
            and game_state.combat.get("active")
        ):
            # Acessa 'enemy' de forma segura usando .get()
            enemy_instance = game_state.combat.get("enemy")

            if enemy_instance:  # Verifica se o inimigo foi realmente retornado
                enemy_name = enemy_instance.name
                enemy_hp = enemy_instance.current_hp
                enemy_max_hp = enemy_instance.max_hp

                action_instructions_parts.append(
                    f"AÇÃO DO JOGADOR (COMBATE):\n"
                    f"O jogador está em combate com {enemy_name} (HP: {enemy_hp}/{enemy_max_hp}).\n"
                    f"Ação de combate do jogador: '{details if details else action}'.\n\n"
                    "SUA TAREFA (PARA AÇÃO DE COMBATE):\n"
                    "1. NARRE O RESULTADO: Descreva vividamente o resultado desta ação de combate, enfatizando a luta pela sobrevivência. A mecânica do dano/acerto já foi resolvida pelo sistema; sua função é narrar.\n"
                    "2. ATUALIZE A CENA: Se o combate causar mudanças visíveis no ambiente, atualize `scene_description_update`.\n"
                    "3. SIGA O JSON: Formate sua resposta conforme as 'INSTRUÇÕES DE FORMATAÇÃO JSON'.\n\n"
                )
            else:  # Inimigo não definido, mas ação é 'attack'
                action_instructions_parts.append(
                    f"AÇÃO DO JOGADOR (TENTATIVA DE ATAQUE FORA DE COMBATE FORMAL): {details if details else action}\n\n"
                    "SUA TAREFA: Narre a tentativa de ataque do jogador. Se um alvo for especificado, descreva o início do confronto. Se nenhum alvo claro, descreva o jogador se preparando ou procurando um alvo. Siga as 'Diretrizes Gerais para Resposta' e o formato JSON.\n\n"
                )
        else:  # Lógica para outras ações resolvidas (resolved, success, fail) que não são 'attack'
            action_instructions_parts.append(
                f"RESULTADO DE AÇÃO MECÂNICA DO JOGADOR (baseado em regras/dados): {details}\n\n"
                "SUA TAREFA (QUANDO UM RESULTADO MECÂNICO É FORNECIDO):\n"
                "1. NARRE O RESULTADO: Use o 'Resultado da Ação Mecânica do Jogador' como base para sua narrativa. Descreva vividamente o que aconteceu no mundo do jogo.\n"
                "2. CONSEQUÊNCIAS IMEDIATAS: Descreva as consequências diretas e as reações do ambiente ou NPCs a este resultado mecânico.\n"
                "3. ATUALIZE A CENA: Forneça uma `scene_description_update` que reflita quaisquer mudanças no ambiente devido à ação.\n"
                "4. MANTENHA A COERÊNCIA: Siga as 'Diretrizes Gerais para Resposta' e o formato JSON.\n"
                "NÃO re-interprete a intenção original do jogador se um resultado mecânico claro foi fornecido; sua tarefa é narrar esse resultado e suas implicações.\n\n"
            )
        return "".join(action_instructions_parts)

    @staticmethod
    def _build_roll_outcome_instructions(details: str) -> str:
        """
        Constrói instruções para narrar o resultado de uma rolagem de dados/teste de habilidade.
        """
        return (
            f"RESULTADO DE TESTE DE HABILIDADE/ATRIBUTO (ROLAGEM DE DADOS): {details}\n\n"
            "SUA TAREFA: Narre vividamente o que aconteceu no mundo do jogo com base neste resultado de teste. Descreva as consequências e reações. Siga as 'Diretrizes Gerais para Resposta' e o formato JSON.\n\n"
        )

    @staticmethod
    def _build_direct_action_instructions(action: str, details: str) -> str:
        """
        Constrói instruções para ações diretas (ex: 'look', 'search') já
        interpretadas pelo sistema.
        """
        instruction_parts = [
            f"AÇÃO DIRETA DO JOGADOR (JÁ INTERPRETADA PELO SISTEMA): {action}"
        ]
        if details:
            instruction_parts.append(f" (Alvo/Detalhes: {details})")
        instruction_parts.append(
            "\n\nSUA TAREFA: Narre o resultado desta ação direta. Siga as 'Diretrizes Gerais para Resposta', as 'SUB-DIRETRIZES PARA INTENÇÕES ESPECÍFICAS' (se aplicável ao tipo de ação) e o formato JSON.\n\n"
        )
        return "".join(instruction_parts)

    @staticmethod
    def _get_sub_intent_guidelines(
        details: str, game_state: GameState, character: Character
    ) -> str:
        """
        Fornece diretrizes específicas para intenções interpretadas comuns.
        """
        sub_intent_parts = [
            "SUB-DIRETRIZES PARA INTENÇÕES ESPECÍFICAS (APLIQUE SE RELEVANTE PARA A AÇÃO ATUAL):\n"
            "  'search': Descreva o que o jogador encontra (ou não) com base no ambiente e nos detalhes da busca. Seja criativo. Pode ser algo útil, inútil, perigoso, ou pistas.\n"
            "  'look': Se houver um alvo específico, descreva o que o jogador observa sobre esse alvo. Forneça informações visuais, pistas. Se for um olhar geral, descreva o que o jogador nota na cena atualizada.\n"
        ]

        # Instruções consolidadas para 'talk' e 'vocal_action'
        talk_prompt_parts = []
        talk_prompt_parts.append(
            "  'talk' (DIÁLOGO/PERGUNTAS) ou 'vocal_action' (AÇÃO VOCAL GENÉRICA):\n"
            "    - Se a AÇÃO DO JOGADOR for uma PERGUNTA (contém '?' ou começa com palavras interrogativas como 'Quem', 'O quê', 'Onde', etc.):\n"
            "      - Identifique o NPC mais apropriado para responder.\n"
            "      - Sua `message` **DEVE** conter a **RESPOSTA DO NPC** à pergunta do jogador. **NÃO narre o jogador fazendo a pergunta novamente. NÃO faça o NPC fazer a mesma pergunta de volta.** O JOGADOR FEZ A PERGUNTA, O NPC (ou o Mestre) RESPONDE.\n"
            "      - A resposta do NPC deve ser direta e relevante ao tópico. **EVITE REPETIR informações já dadas recentemente por esse NPC.** Se o jogador insistir, o NPC pode adicionar detalhes, mostrar impaciência ou indicar que já respondeu.\n"
            "      - Se nenhum NPC puder responder, a narrativa deve indicar isso (ex: 'Ninguém parece saber.').\n"
            "      - A resposta **DEVE** ser consistente com o papel, conhecimento e personalidade do NPC.\n"
            "      - Se a pergunta for direcionada a um NPC específico (ex: 'Médica, ele vai ficar bem?'), a resposta deve vir primariamente daquele NPC.\n"
            "    - Senão, se a AÇÃO DO JOGADOR for uma TENTATIVA DE CONVERSA DIRETA com um NPC (não uma pergunta específica):\n"
            "      - Você está controlando o NPC. O JOGADOR iniciou a conversa ou fez uma afirmação. Crie uma interação realista e progressiva que reflita a personalidade e o estado emocional do NPC no contexto do apocalipse zumbi.\n"
            "      - Revele **NOVOS** detalhes sobre o mundo, perigos, necessidades ou missões. **EVITE REPETIR informações que este NPC já deu**, a menos que o jogador peça ou sirva a um propósito narrativo claro.\n"
        )

        # Adicionar detalhes do NPC alvo se a ação for 'talk' ou se 'details' contiver um nome de NPC conhecido
        extracted_npc_name: Optional[str] = None
        if isinstance(details, str) and details.strip():
            details_lower = details.lower()
            # Iterar sobre os NPCs conhecidos para encontrar uma correspondência de nome
            for npc_obj_known in game_state.known_npcs.values():
                if not isinstance(npc_obj_known, NPC) or not hasattr(
                    npc_obj_known, "name"
                ):
                    continue
                if npc_obj_known.name.lower() in details_lower:
                    extracted_npc_name = npc_obj_known.name  # Usar o nome canônico
                    break

        if extracted_npc_name:
            npc_data_obj_for_prompt: Optional[NPC] = None
            for (
                npc_obj_iter
            ) in (
                game_state.known_npcs.values()
            ):  # Iterar sobre os valores (objetos NPC)
                if npc_obj_iter.name == extracted_npc_name:
                    npc_data_obj_for_prompt = npc_obj_iter
                    break
            if npc_data_obj_for_prompt:
                talk_prompt_parts.append(
                    PromptBuilder._format_npc_details_for_prompt(
                        extracted_npc_name, npc_data_obj_for_prompt
                    )
                )

        talk_prompt_parts.append(
            "    - Senão, se a AÇÃO DO JOGADOR for uma 'vocal_action' (ex: 'Gritar', 'Sussurrar', 'Chamar por ajuda') e NÃO uma conversa ou pergunta direta:\n"
        )

        talk_prompt_parts.append(
            "    - Senão, se a AÇÃO DO JOGADOR for uma 'vocal_action' (ex: 'Gritar', 'Sussurrar', 'Chamar por ajuda') e NÃO uma conversa ou pergunta direta:\n"
            "      - **RESPEITE a intensidade da ação vocal.** Um grito ALTO é ALTO.\n"
            "      - Descreva o efeito físico imediato no ambiente (eco, poeira caindo).\n"
            "      - **CONECTE IMEDIATAMENTE à diretriz 'CONSEQUÊNCIAS DE RUÍDO'.** NPCs devem reagir com alarme/medo/raiva pela imprudência, não com diálogo casual. O foco é na tensão e perigo.\n"
            "    - Senão, se a AÇÃO DO JOGADOR for 'talk' mas sem alvo claro (jogador apenas indicou querer falar):\n"
            "      - Descreva se algum NPC próximo toma a iniciativa ou se o ambiente permanece em silêncio. Um NPC pode perguntar 'Você disse algo?'.\n"
            "    - Se os detalhes para 'talk' ou 'vocal_action' forem vagos, aplique a diretriz 'AÇÕES IMPRECISAS'.\n"
        )
        sub_intent_parts.append("".join(talk_prompt_parts))

        sub_intent_parts.append(
            "  'use_item': Descreva o resultado de usar o item. Se consumível, o efeito. Se ferramenta, a ação e resultado. Se item de quest, revele informação/consequência.\n"
            "    - Se o item for FERRAMENTA/ARMA (ex: 'Pé de Cabra') e a ação for 'usar [item]', interprete como EQUIPAR ou preparar para uso. NÃO assuma cura com ferramenta, a menos que o item diga.\n"
            "  'attack': Se não houver combate ativo, descreva o jogador se preparando ou atacando o alvo, iniciando o confronto. Se combate ativo, descreva o resultado do ataque (mecânica já resolvida).\n"
            "  'flee': Descreva a tentativa de fuga (mecânica já resolvida). Foi bem-sucedida? Perigos? Mantenha a tensão.\n"
            "  'rest': Descreva a tentativa de descanso (mecânica já resolvida). Local seguro? Interrupções? Efeitos de recuperação ou impossibilidade.\n"
            "  'skill': Descreva o uso da habilidade (mecânica já resolvida). Efeitos visuais, sonoros, impacto no alvo ou no personagem.\n"
            "  'craft': Descreva a tentativa de criação (mecânica já resolvida). Sucesso ou falha, o item resultante.\n"
            "  'custom_complex' ou outras não listadas: Interprete no contexto do apocalipse zumbi. Descreva o resultado de forma criativa e coerente.\n\n"
        )
        return "".join(sub_intent_parts)

    @staticmethod
    def _get_general_response_guidelines() -> str:
        """
        Fornece diretrizes gerais para a criação das respostas da IA.
        """
        return (
            "DIRETRIZES GERAIS PARA RESPOSTA (APLIQUE SEMPRE):\n"
            "1. **FOCO NA AÇÃO DO JOGADOR**: Sua resposta deve focar PRIMARIAMENTE no resultado direto e consequências imediatas da AÇÃO ATUAL do jogador. Ao descrever o que o jogador faz ou percebe, narre do ponto de vista DELE (ex: 'Você percebe...', 'Você encontra...'). NPCs reagem DEPOIS. Se a ação mencionar um item/alvo, foque nisso. Evite desviar para elementos não mencionados na ação atual.\n"
            "2. **PROGRESSÃO E CONTEXTO**:\n"
            "   - Use o 'HISTÓRICO RECENTE DA CONVERSA' para entender o foco. Respostas de NPCs devem ser continuações lógicas, **ADICIONANDO NOVAS INFORMAÇÕES** ou reagindo diferente a repetições. **EVITE que NPCs mudem de assunto abruptamente ou REPITAM EXATAMENTE o que já disseram recentemente**, a menos que para dar ênfase ou se o jogador pedir.\n"
            "   - **CRUCIAL: CONSIDERE O ESTADO ATUAL DO PERSONAGEM** (Saúde, Fome, Sede). Sua narrativa e reações de NPCs **DEVEM** ser consistentes. Não descreva o personagem como 'gravemente ferido' se a Saúde estiver alta. NPCs não devem oferecer cura se saudável, ou comida se saciado, a menos que seja um engano ou situação específica.\n"
            "3. PROGRESSÃO NARRATIVA: Faça a história progredir. Ações devem ter impacto. Evite que o estado de inimigos se 'resete' magicamente.\n"
            "4. EVITE REPETIÇÃO ATMOSFÉRICA: Não repita excessivamente descrições atmosféricas (ar, cheiros, luz) a menos que mudem significativamente devido à ação do jogador ou novo evento. Mencione brevemente se relevante, mas não como foco principal repetidamente.\n"
            "5. CONSISTÊNCIA E TOM: Mantenha consistência com o mundo pós-apocalíptico, local, NPCs e tom (perigo, escassez, desconfiança, lampejos de esperança/mistério). NPCs devem usar ferramentas/conhecimentos de sua profissão.\n"
            "6. ESPECIFICIDADE: Evite respostas genéricas. Seja específico sobre o que é (ou não) encontrado, visto ou o resultado.\n"
            "7. DETALHES SENSORIAIS COM MODERAÇÃO: Use para imersão, mas apenas se adicionarem valor, não como preenchimento.\n"
            "8. AÇÕES VAGAS: Se a ação do jogador for vaga, interprete da forma mais interessante para a narrativa, usando o contexto.\n"
            "9. **AÇÕES IMPRECISAS/IRRELEVANTES**: Se a ação não fizer sentido, for aleatória, comentário fora de personagem, ou sem alvo/intenção clara (ex: 'usar item' sem dizer qual), sua `message` deve refletir que o Mestre (você) não compreendeu ou que a ação não teve efeito. Ex: 'Não entendi o que você quis dizer.' ou 'Isso não parece ter efeito aqui.' **NÃO tente criar uma narrativa para ações sem sentido ou vagas demais.**\n"
            "10. ENVOLVIMENTO DE NPCs: Descreva a reação de NPCs *apenas se a ação do jogador os afetar diretamente, se tiverem uma reação natural e imediata, ou se o jogador interagir com eles*. Caso contrário, foco no jogador e ambiente da ação.\n"
            "11. **CONSEQUÊNCIAS DE RUÍDO**: Barulhos altos (gritos, tiros) são **PERIGOSOS** (atraem zumbis/hostis). Suas descrições e reações de NPCs **DEVEM** refletir essa tensão. NPCs podem ficar alarmados, repreender o jogador, sugerir silêncio, tomar medidas defensivas. A narrativa pode sugerir o risco (ex: 'um silêncio tenso se segue ao seu grito...').\n"
            "12. SUGESTÃO DE TESTES (ROLAGENS DE DADOS): Se a 'AÇÃO DO JOGADOR' (quando 'interpret') descrever uma tentativa com risco/desafio (arrombar porta, escalar, persuadir guarda), VOCÊ DEVE incluir um objeto `suggested_roll` no JSON. Campos: `description` (string: 'Arrombar a porta'), `attribute` (string: 'strength'), `skill` (string opcional: 'stealth', ou null), `dc` (int: Fácil 10-12, Médio 13-15, Difícil 16-18, Muito Difícil 19+), `reasoning` (string opcional: 'A porta parece reforçada'). Se sugerir `suggested_roll`, sua `message` descreve o jogador iniciando a tentativa, SEM o resultado final (que dependerá da rolagem). Ex: 'Você se prepara para arrombar a porta... Parece resistente.' NÃO sugira rolagens para ações triviais.\n"
            "13. ELEMENTOS INTERATIVOS: Ao descrever `current_detailed_location` e `scene_description_update`, identifique 2-4 elementos/objetos/áreas de interesse chave DENTRO dessa sub-localização. Liste os nomes em `interactable_elements` no JSON. Nomes concisos (ex: 'Mesa de Operações', 'Armário de Remédios').\n"
        )

    @staticmethod
    def _get_json_format_instructions() -> str:
        """
        Fornece instruções para o formato de resposta JSON obrigatório.
        """
        return (
            "INSTRUÇÕES DE FORMATAÇÃO DA RESPOSTA (JSON OBRIGATÓRIO):\n"
            "RESPONDA SEMPRE E APENAS com uma string JSON válida, SEM QUALQUER TEXTO ADICIONAL ANTES OU DEPOIS DO JSON (incluindo markdown como ```json ou ```).\n"
            "CAMPOS OBRIGATÓRIOS NO JSON:\n"
            "- `success`: (boolean) `true` se você puder gerar uma resposta narrativa. `false` apenas em caso de erro interno seu (raro).\n"
            "- `message`: (string, pt-br) Sua descrição narrativa principal da cena e do resultado da ação do jogador. Integre a percepção de novos `interactable_elements` naturalmente, se possível.\n"
            "- `current_detailed_location`: (string, pt-br) O nome detalhado da localização ATUAL do jogador (ex: 'Abrigo Subterrâneo - Sala Principal'). Se o jogador se mover para um novo local principal (ex: de 'Floresta' para 'Abrigo'), determine um ponto de entrada lógico (ex: 'Pátio de Entrada') e use-o como sub-área (ex: 'Abrigo Subterrâneo - Pátio de Entrada').\n"
            "- `scene_description_update`: (string, pt-br) Uma NOVA descrição CONCISA para a cena/sub-área ATUAL (`current_detailed_location`), focando nos elementos estáticos e ambientais importantes.\n"
            "CAMPOS OPCIONAIS (MAS ALTAMENTE RECOMENDADOS QUANDO APLICÁVEL):\n"
            "- `interpreted_action_type`: (string) A categoria da intenção que você interpretou da 'AÇÃO DO JOGADOR' (ex: 'move', 'talk', 'search').\n"
            "- `interpreted_action_details`: (object) Dicionário com parâmetros relevantes para a ação interpretada (ex: {'direction': 'norte'}, {'target_npc': 'NomeDoNPC'}).\n"
            "- `suggested_roll`: (object) Se a ação do jogador justificar um teste, inclua este objeto com: `description` (string), `attribute` (string), `skill` (string ou null), `dc` (int), `reasoning` (string, opcional).\n"
            "- `interactable_elements`: (list[string]) Lista de 2-4 nomes de elementos/sub-áreas chave DENTRO da `current_detailed_location` com os quais o jogador pode interagir (ex: ['Mesa de Operações', 'Armário de Remédios']). Nomes concisos.\n"
            "- `error`: (string, opcional) Se `success` for `false`, uma breve descrição do erro.\n"
            "- `details`: (object, opcional) Detalhes adicionais específicos da IA, se houver.\n\n"
            '- `new_facts`: (object, opcional) Um dicionário de fatos chave que foram estabelecidos ou descobertos nesta interação (ex: {"npc_revelou_segredo_X": true, "item_Y_obtido": "Espada Lendária", "local_Z_descoberto": "Caverna Escura"}). Use chaves descritivas e valores booleanos, strings ou números. Estes fatos ajudarão a construir a memória de longo prazo.\n\n'
            "EXEMPLO DE JSON DE RESPOSTA PARA AÇÃO DE BUSCA bem-sucedida:\n"
            "EXEMPLO DE JSON DE RESPOSTA PARA AÇÃO 'Gritar muito alto!' no 'Abrigo Subterrâneo - Sala Principal':\n"
            "```json\n"
            "{\n"
            '  "success": true,\n'
            '  "message": "Você solta um grito agudo que ecoa terrivelmente pelo abrigo! O Velho Sobrevivente Cansado se encolhe e sibila: \\"Cale a boca, imbecil! Quer que todos os mortos da cidade venham bater à nossa porta?!\\". A Médica de Campo empalidece, olhando para a entrada com puro terror. Ao seu redor, você nota o Portão de Metal Reforçado, uma Enfermaria Improvisada e o Gerador Barulhento.",\n'
            '  "current_detailed_location": "Abrigo Subterrâneo - Sala Principal",\n'
            '  "scene_description_update": "A sala principal do abrigo é fria e úmida. A tensão é palpável após o grito; os sobreviventes estão em alerta máximo.",\n'
            '  "interpreted_action_type": "vocal_action",\n'
            '  "interpreted_action_details": {"vocal_text": "Gritar muito alto!"},\n'
            '  "interactable_elements": ["Portão de Metal Reforçado", "Enfermaria Improvisada", "Gerador Barulhento"]\n'
            "}\n```\n\n"
            "EXEMPLO DE JSON DE RESPOSTA PARA AÇÃO 'Procurar por comida no Depósito':\n"
            "```json\n"
            "{\n"
            '  "success": true,\n'
            '  "message": "Você vasculha as prateleiras empoeiradas do depósito. Entre caixas rasgadas e latas enferrujadas, você encontra uma barra de proteína intacta e uma pequena garrafa de água ainda selada.",\n'
            '  "current_detailed_location": "Depósito do Abrigo",\n'
            '  "scene_description_update": "O depósito continua frio e com cheiro de mofo, mas agora uma prateleira parece um pouco mais remexida.",\n'
            '  "interpreted_action_type": "search",\n'
            '  "interpreted_action_details": {"target": "comida"},\n'
            '  "interactable_elements": ["Prateleiras Vazias", "Caixa de Ferramentas Antigas", "Ratos Escondidos"],\n'
            '  "new_facts": {"item_encontrado_barra_proteina": 1, "item_encontrado_agua_pequena": 1}\n'
            "}\n```\n"
        )
