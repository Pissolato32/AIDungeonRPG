# filepath: c:\Users\rodri\Desktop\REPLIT RPG\ai\prompt_builder.py
"""
Module for constructing prompts for the AI model.
"""
from typing import Any, Dict, List

from core.game_state_model import GameState, MessageDict  # Assuming MessageDict is here
from core.models import Character  # Will use CharacterType where appropriate

from .game_ai_client import CharacterType  # Import the protocol

# Se CharacterType for um Protocolo, você pode importá-lo ou redefini-lo aqui
# from .game_ai_client import CharacterType # Se estiver definido em game_ai_client

# Para simplificar, vamos assumir que Character é a classe concreta por enquanto.
# Se você tiver um CharacterType Protocol, use-o.



class PromptBuilder:
    """
    Handles the construction of prompts to be sent to the AI model.
    """

    @staticmethod
    def build_system_prompt() -> str:
        """Builds the static system prompt."""
        return (
            "Você é o Mestre do Jogo em um RPG pós-apocalíptico.\n"
            "Regras:\n"
            "1. Nunca repita exatamente falas ou descrições anteriores.\n"
            "2. Se o jogador fizer a mesma pergunta, aprofunde ou forneça novas informações.\n"
            "3. Mantenha-se coerente com o histórico recente (últimos 3 turnos).\n"
            "4. Use vocabulário variado para enriquecer a narrativa."
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

        npcs_text = ", ".join(npcs_in_current_loc) if npcs_in_current_loc else "Nenhum"
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
        character: CharacterType,  # Changed to CharacterType
    ) -> str:  # Use Character or CharacterType
        """Builds the player character context part of the prompt."""
        return (
            "Personagem do jogador:\n"
            f"- Nome: {character.name}\n"
            f"- Nível: {character.level}\n"
            f"- HP: {character.attributes.get('current_hp', 0)}/{character.attributes.get('max_hp', 0)}\n\n"
        )

    @staticmethod
    def _build_combat_context(game_state: GameState, action: str, details: str) -> str:
        """Builds the combat context part of the prompt, if combat is active."""
        combat_context_str = ""
        if game_state.combat and game_state.combat.get("enemy"):
            enemy_data = game_state.combat.get("enemy")
            if isinstance(enemy_data, dict):  # Assuming enemy data is a dict
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
        character: CharacterType,  # Adicionado para contexto de combate
        game_state: GameState,  # Adicionado para known_npcs e contexto de combate
    ) -> str:
        """Builds the AI's task instructions based on the action type."""
        action_instructions = ""
        # Esta é a seção que você mais expandirá, movendo a lógica do _create_action_prompt original para cá.
        # Exemplo simplificado:
        if action.lower() == "interpret":
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
                action_instructions += (
                    f"Ação de Movimento do Jogador (interprete e execute): {details}\n"
                    f"Localização Atual do Jogador (antes do movimento): {current_location}\n\n"
                    "SUA TAREFA (para movimento interpretado):\n"
                    "1. DETERMINE O NOVO LOCAL: Baseado na 'Ação de Movimento do Jogador' e na 'Localização Atual do Jogador', determine para onde o jogador está tentando ir. Se for 'sair do abrigo', o novo local é claramente fora do abrigo. Se for uma direção, é um local adjacente. Se for um nome de local, é esse local.\n"
                    "2. NARRE A TRANSIÇÃO E O NOVO LOCAL: Sua `message` DEVE descrever o jogador saindo do local atual e chegando ao NOVO local. Descreva brevemente o que ele vê e sente ao chegar no NOVO local. É CRUCIAL que sua narrativa reflita a chegada ao NOVO local e NÃO um retorno ao local anterior ou qualquer confusão sobre a movimentação.\n"
                    "3. ATUALIZE OS CAMPOS JSON PARA O NOVO LOCAL: No seu JSON de resposta:\n"
                    "   - `current_detailed_location` DEVE ser o nome detalhado do NOVO local para onde o jogador se moveu.\n"
                    "   - `scene_description_update` DEVE ser a descrição do NOVO local.\n"
                    "   - `interpreted_action_type` deve ser 'move'.\n"
                    "   - `interpreted_action_details` deve conter informações sobre o movimento (ex: {'direction': 'saindo do abrigo', 'target_location_name': 'Corredor Externo'}).\n\n"
                )
            else:
                action_instructions += (
                    f"Ação textual do jogador (interprete a intenção): {details}\n\n"
                    "SUA TAREFA PRINCIPAL (quando a ação é 'interpret' e NÃO é explicitamente movimento):\n"
                    "1. INTERPRETE A INTENÇÃO: Analise a 'Ação textual do jogador' para determinar a intenção principal. Categorize-a como uma das seguintes: 'look', 'talk', 'vocal_action', 'search', 'use_item', 'attack', 'flee', 'rest', 'skill', 'craft', 'custom_complex'.\n"
                    "2. GERE A NARRATIVA: Com base na intenção interpretada, narre o resultado da ação como Mestre do Jogo. Aplique as 'Diretrizes Gerais para Resposta' e, se a intenção corresponder a uma das ações com 'SUB-DIRETRIZES PARA INTENÇÕES ESPECÍFICAS' abaixo, aplique essas sub-diretrizes também.\n"
                    "3. INCLUA INTERPRETAÇÃO NO JSON: No seu JSON de resposta, além dos campos padrão, inclua 'interpreted_action_type' (a categoria que você escolheu) e 'interpreted_action_details' (um dicionário com parâmetros relevantes).\n\n"
                )
        elif (
            "resolved" in action.lower()
            or "success" in action.lower()
            or "fail" in action.lower()
            or action.lower() == "attack"
        ):
            if (
                action.lower() == "attack"
                and game_state.combat
                and game_state.combat.get("enemy")
            ):
                enemy_combat_data = game_state.combat.get("enemy")
                if isinstance(enemy_combat_data, dict): # Check if enemy_combat_data is a dict
                    enemy_name = enemy_combat_data.get("name", "Inimigo")
                    enemy_hp = enemy_combat_data.get("health", 0)
                    enemy_max_hp = enemy_combat_data.get("max_health", enemy_hp)

                    action_instructions += (
                        # O system_prompt já define o papel do Mestre.
                        # O contexto do personagem e da cena já foram adicionados antes.
                        f"O jogador está em combate com {enemy_name}.\n"
                        f"Informações do Inimigo:\n"
                        f"- Nome: {enemy_name}\n"
                        f"- HP: {enemy_hp}/{enemy_max_hp}\n\n"
                        f"O jogador está realizando a ação de combate: '{details if details else action}'.\n\n"
                        "Narre o resultado desta ação de combate de forma vívida e brutal, enfatizando a luta pela sobrevivência. "
                        "Siga a INSTRUÇÃO DE FORMATAÇÃO DA RESPOSTA JSON abaixo.\n\n"
                    )
                else:
                    # Fallback if enemy data is not as expected or missing, though the outer if should catch missing enemy
                    action_instructions += "O jogador está em combate, mas os detalhes do inimigo não estão claros.\n"
            else:
                # Lógica para outras ações resolvidas ou resultados de ataque
                action_instructions += (
                    f"Resultado da Ação Mecânica do Jogador (baseado em regras/dados): {details}\n\n"
                    "SUA TAREFA PRINCIPAL (quando um resultado mecânico é fornecido):\n"
                    "1. NARRE O RESULTADO: Use o 'Resultado da Ação Mecânica do Jogador' como base para sua narrativa. Descreva vividamente o que aconteceu no mundo do jogo.\n"
                    "2. CONSEQUÊNCIAS IMEDIATAS: Descreva as consequências diretas e as reações do ambiente ou NPCs a este resultado mecânico.\n"
                    "3. ATUALIZE A CENA: Forneça uma `scene_description_update` que reflita quaisquer mudanças no ambiente devido à ação.\n"
                    "4. MANTENHA A COERÊNCIA: Siga as 'Diretrizes Gerais para Resposta'.\n"
                    "NÃO re-interprete a intenção original do jogador se um resultado mecânico claro foi fornecido; sua tarefa é narrar esse resultado e suas implicações.\n\n"
                )
        elif action.lower() == "narrate_roll_outcome":
            action_instructions += (
                f"Resultado Mecânico de um Teste Recente: {details}\n\n"
                "SUA TAREFA: Narre vividamente o que aconteceu no mundo do jogo com base neste resultado de teste. Descreva as consequências e reações. Siga as 'Diretrizes Gerais para Resposta'.\n\n"
            )
        else:  # Ações diretas
            action_instructions += f"Ação atual do jogador (direta): {action}"
            if details:
                action_instructions += f" (Detalhes: {details})"
            action_instructions += "\n\n"

        # Adicione as SUB-DIRETRIZES e DIRETRIZES GERAIS aqui
        # Exemplo:
        action_instructions += (
            "SUB-DIRETRIZES PARA INTENÇÕES ESPECÍFICAS (aplique se relevante para a intenção que você interpretou ou para a ação direta fornecida):\n"
            "INTENÇÃO 'search': Descreva o que o personagem encontra (ou não encontra) com base no ambiente e nos detalhes da busca. "
            "Seja criativo e considere o que faria sentido encontrar em um local como este. "
            "Pode ser algo útil, inútil, perigoso, ou apenas pistas sobre o que aconteceu.\n\n"
            "INTENÇÃO 'look': Se houver um alvo específico nos detalhes da ação do jogador, descreva em detalhes o que o personagem observa sobre esse alvo. "
            "Forneça informações visuais, pistas ou qualquer coisa relevante. Se for um olhar geral ao ambiente, reitere ou atualize a descrição da cena.\n\n"
            "INTENÇÃO 'move': Descreva a transição para o novo local ou a tentativa de movimento. "  # Esta parte pode ser redundante se a lógica de 'interpret' para movimento já cobrir. Avalie.
            "Se o movimento for para um local conhecido, reforce a descrição com novos detalhes ou mudanças. "
            "Se for uma tentativa de ir a um local desconhecido ou bloqueado, descreva o obstáculo ou a razão pela qual o movimento não é simples.\n\n"
        )

        # Bloco para 'talk', 'perguntas', 'vocal_action'
        talk_prompt_parts = []
        talk_prompt_parts.append("INTENÇÕES 'talk' (diálogo), PERGUNTAS, ou 'vocal_action' (ação vocal genérica):\n")
        # Se a ação do jogador for uma PERGUNTA e a intenção for 'talk':
        talk_prompt_parts.append("   Se a 'Ação textual do jogador' contiver um ponto de interrogação (?) OU começar com palavras como 'Quem', 'O quê', 'Onde', 'Quando', 'Por que', 'Como', 'Será que', 'Você acha que' E a intenção interpretada for 'talk':\n")
        talk_prompt_parts.append("     - Identifique o NPC mais apropriado para responder à pergunta com base no contexto e no conhecimento esperado do NPC (ex: uma médica sobre questões médicas, um engenheiro sobre reparos, um líder sobre planos).\n")
        talk_prompt_parts.append("     - A resposta do NPC DEVE ser uma tentativa direta de responder à pergunta do jogador. EVITE que o NPC faça a mesma pergunta de volta ao jogador ou a outros NPCs, a menos que seja uma pergunta retórica clara e intencional para provocar reflexão (e isso deve ser raro e justificado pela personalidade do NPC).\n")
        talk_prompt_parts.append("     - Se nenhum NPC presente puder responder, a narrativa pode indicar isso (ex: 'Ninguém parece saber a resposta.' ou 'A Médica de Campo balança a cabeça, incerta.' ou 'O Velho Sobrevivente dá de ombros, claramente sem saber.').\n")
        talk_prompt_parts.append("     - A resposta DEVE ser consistente com o papel, conhecimento e personalidade do NPC. Exemplo: Uma médica não perguntaria ao jogador sobre o prognóstico de um paciente que ela está tratando; ela daria sua avaliação ou expressaria incerteza se fosse o caso.\n")
        talk_prompt_parts.append("     - Se a pergunta for direcionada a um NPC específico (ex: 'Médica, ele vai ficar bem?'), a resposta deve vir primariamente daquele NPC.\n")
        talk_prompt_parts.append("   Senão, se a intenção for 'talk' (tentativa de conversa direta com um NPC específico, não sendo uma pergunta direta já tratada acima):\n")
        # Adaptado de prompt_manager.py
        talk_prompt_parts.append("     Você está controlando um NPC em uma conversa. Crie uma interação realista e envolvente que:\n")
        talk_prompt_parts.append("     1. Reflita a personalidade, o estado emocional (medo, desconfiança, esperança) e a atitude do NPC no contexto de um apocalipse zumbi.\n")
        talk_prompt_parts.append("     2. Use informações prévias se o jogador já interagiu com este NPC.\n")
        talk_prompt_parts.append("     3. Revele detalhes sobre o mundo devastado, perigos imediatos, rumores, necessidades de sobrevivência ou possíveis missões/trocas.\n")
        talk_prompt_parts.append("     4. Mantenha consistência com interações anteriores.\n")
        talk_prompt_parts.append("     5. Permita que o jogador faça escolhas significativas.\n")
        
        action_instructions += "".join(talk_prompt_parts)
        talk_prompt_parts = [] # Reset for next part of this logical block

        # Lógica Python para adicionar detalhes do NPC condicionalmente
        if details and details in game_state.known_npcs:
            npc_data = game_state.known_npcs[details]
            action_instructions += PromptBuilder._format_npc_details_for_prompt(details, npc_data)
        
        action_instructions += (
            f"\nO jogador está tentando conversar com '{details if details else 'um NPC próximo'}'. "
            "Crie um diálogo realista e interessante que desenvolva a narrativa, a tensão e o mundo pós-apocalíptico do jogo.\n"
        )

        # Continuação do bloco 'talk', 'perguntas', 'vocal_action'
        action_instructions += "   Senão, if a intenção for 'vocal_action' (ex: 'Gritar MUITO ALTO', 'Sussurrar', 'Chamar por ajuda', 'Cantar uma música triste') e NÃO uma tentativa de conversa direta com um NPC ou uma pergunta:\n"
        action_instructions += "     - Primeiro, RESPEITE a intensidade da ação vocal descrita pelo jogador. Se o jogador diz 'Gritar MUITO ALTO', o som É muito alto e perceptível. Não o atenue ou descreva como 'amortecido' arbitrariamente, a menos que o ambiente (ex: dentro de um cofre à prova de som que o jogador conhece) justifique explicitamente e o jogador já tenha essa informação contextual.\n"
        action_instructions += "     - Descreva o efeito físico imediato dessa ação no ambiente (ex: o som ecoa agudamente, poeira cai do teto, objetos próximos vibram).\n"
        action_instructions += "     - Em seguida, conecte IMEDIATAMENTE esta ação à diretriz geral '11. CONSEQUÊNCIAS DE RUÍDO'. As reações dos NPCs DEVEM refletir o perigo de atrair atenção indesejada (zumbis, saqueadores). Eles devem parecer visivelmente alarmados, podem repreender o jogador com urgência (ex: 'Você quer nos matar?! Fique quieto!'), gesticular freneticamente por silêncio, olhar nervosamente para as saídas, ou até mesmo se preparar para um possível ataque/invasão. Evite que os NPCs iniciem um diálogo casual ou façam perguntas simples como 'O que foi isso?'. Suas reações devem ser de medo, raiva pela imprudência, ou pânico.\n"
        action_instructions += "     - O foco da sua narrativa deve ser na tensão criada, no perigo iminente percebido, e na reação de alerta/pânico dos NPCs, não em iniciar uma nova conversa. A reação deve ser natural para sobreviventes experientes (ou apavorados) em um mundo hostil.\n"
        action_instructions += "   Senão, if a intenção for 'talk' mas sem detalhes específicos ou alvo claro (jogador apenas indicou querer falar de forma geral):\n"
        action_instructions += "     Descreva se algum NPC próximo toma a iniciativa de falar com o jogador, ou se o ambiente permanece em silêncio aguardando uma ação mais específica. Se houver NPCs, um deles pode perguntar 'Você disse alguma coisa?' ou 'Precisa de algo?'.\n"
        action_instructions += "   Se os detalhes para 'talk' ou 'vocal_action' forem vagos ou sem sentido, aplique a diretriz geral '9. AÇÕES OU DETALHES IMPRECISOS/IRRELEVANTES'.\n\n"
        
        # Outras INTENÇÕES
        action_instructions += "INTENÇÃO 'use_item': Descreva o resultado de usar o item especificado. Se for um consumível, descreva a sensação ou efeito. "
        action_instructions += "Se for uma ferramenta, descreva a ação e seu sucesso ou falha. "
        action_instructions += "Se for um item de quest, revele alguma informação ou consequência.\n\n"
        action_instructions += "INTENÇÃO 'attack': Se não houver combate ativo, descreva o jogador se preparando para o combate ou atacando o alvo especificado (ou o mais óbvio), iniciando a confrontação. Se o combate já estiver ativo, descreva o resultado do ataque contra o inimigo atual.\n\n"
        action_instructions += "INTENÇÃO 'flee': Descreva a tentativa de fuga. Foi bem-sucedida? Houve perigos ou obstáculos? "
        action_instructions += "A fuga levou o personagem a uma situação melhor ou pior? "
        action_instructions += "Mantenha a tensão e o realismo do apocalipse zumbi.\n\n"
        action_instructions += "INTENÇÃO 'rest': Descreva a tentativa de descanso. O local é seguro o suficiente? "
        action_instructions += "O personagem consegue realmente descansar ou é interrompido? Quais são os riscos? "
        action_instructions += "Descreva quaisquer efeitos de recuperação ou, ao contrário, a impossibilidade de descansar devido ao perigo.\n\n"
        action_instructions += "INTENÇÃO 'custom_complex' ou outras não listadas: Interprete esta ação no contexto do jogo de apocalipse zumbi. "
        action_instructions += "Descreva o resultado da ação do jogador de forma criativa e coerente com o ambiente e a situação. "
        action_instructions += "Considere as possíveis consequências, sucessos ou falhas.\n\n"

        action_instructions += (
            "Diretrizes Gerais para Resposta (aplique sempre...):\n"
            "1. **FOCO NA AÇÃO:** Sua resposta deve focar PRIMARIAMENTE no resultado direto e nas consequências imediatas da ação do jogador ('Ação atual do jogador').\n"
            if details and details in game_state.known_npcs:
                npc_data = game_state.known_npcs[details]
                action_instructions += PromptBuilder._format_npc_details_for_prompt(details, npc_data)
            action_instructions += (
                f"\nO jogador está tentando conversar com '{details if details else 'um NPC próximo'}'. "
                "Crie um diálogo realista e interessante que desenvolva a narrativa, a tensão e o mundo pós-apocalíptico do jogo.\n"
            )
            action_instructions += "   Senão, if a intenção for 'vocal_action' (ex: 'Gritar MUITO ALTO', 'Sussurrar', 'Chamar por ajuda', 'Cantar uma música triste') e NÃO uma tentativa de conversa direta com um NPC ou uma pergunta:\n"
            action_instructions += "     - Primeiro, RESPEITE a intensidade da ação vocal descrita pelo jogador. Se o jogador diz 'Gritar MUITO ALTO', o som É muito alto e perceptível. Não o atenue ou descreva como 'amortecido' arbitrariamente, a menos que o ambiente (ex: dentro de um cofre à prova de som que o jogador conhece) justifique explicitamente e o jogador já tenha essa informação contextual.\n"
            action_instructions += "     - Descreva o efeito físico imediato dessa ação no ambiente (ex: o som ecoa agudamente, poeira cai do teto, objetos próximos vibram).\n"
            action_instructions += "     - Em seguida, conecte IMEDIATAMENTE esta ação à diretriz geral '11. CONSEQUÊNCIAS DE RUÍDO'. As reações dos NPCs DEVEM refletir o perigo de atrair atenção indesejada (zumbis, saqueadores). Eles devem parecer visivelmente alarmados, podem repreender o jogador com urgência (ex: 'Você quer nos matar?! Fique quieto!'), gesticular freneticamente por silêncio, olhar nervosamente para as saídas, ou até mesmo se preparar para um possível ataque/invasão. Evite que os NPCs iniciem um diálogo casual ou façam perguntas simples como 'O que foi isso?'. Suas reações devem ser de medo, raiva pela imprudência, ou pânico.\n"
            action_instructions += "     - O foco da sua narrativa deve ser na tensão criada, no perigo iminente percebido, e na reação de alerta/pânico dos NPCs, não em iniciar uma nova conversa. A reação deve ser natural para sobreviventes experientes (ou apavorados) em um mundo hostil.\n"
            action_instructions += "   Senão, if a intenção for 'talk' mas sem detalhes específicos ou alvo claro (jogador apenas indicou querer falar de forma geral):\n"
            action_instructions += "     Descreva se algum NPC próximo toma a iniciativa de falar com o jogador, ou se o ambiente permanece em silêncio aguardando uma ação mais específica. Se houver NPCs, um deles pode perguntar 'Você disse alguma coisa?' ou 'Precisa de algo?'.\n"
            action_instructions += "   Se os detalhes para 'talk' ou 'vocal_action' forem vagos ou sem sentido, aplique a diretriz geral '9. AÇÕES OU DETALHES IMPRECISOS/IRRELEVANTES'.\n\n"
            action_instructions += "INTENÇÃO 'use_item': Descreva o resultado de usar o item especificado. Se for um consumível, descreva a sensação ou efeito. "
            action_instructions += "Se for uma ferramenta, descreva a ação e seu sucesso ou falha. "
            action_instructions += "Se for um item de quest, revele alguma informação ou consequência.\n\n"
            action_instructions += "INTENÇÃO 'attack': Se não houver combate ativo, descreva o jogador se preparando para o combate ou atacando o alvo especificado (ou o mais óbvio), iniciando a confrontação. Se o combate já estiver ativo, descreva o resultado do ataque contra o inimigo atual.\n\n"
            action_instructions += "INTENÇÃO 'flee': Descreva a tentativa de fuga. Foi bem-sucedida? Houve perigos ou obstáculos? "
            action_instructions += "A fuga levou o personagem a uma situação melhor ou pior? "
            action_instructions += "Mantenha a tensão e o realismo do apocalipse zumbi.\n\n"
            action_instructions += "INTENÇÃO 'rest': Descreva a tentativa de descanso. O local é seguro o suficiente? "
            action_instructions += "O personagem consegue realmente descansar ou é interrompido? Quais são os riscos? "
            action_instructions += "Descreva quaisquer efeitos de recuperação ou, ao contrário, a impossibilidade de descansar devido ao perigo.\n\n"
            action_instructions += "INTENÇÃO 'custom_complex' ou outras não listadas: Interprete esta ação no contexto do jogo de apocalipse zumbi. "
            action_instructions += "Descreva o resultado da ação do jogador de forma criativa e coerente com o ambiente e a situação. "
            action_instructions += "Considere as possíveis consequências, sucessos ou falhas.\n\n"
        )

        action_instructions += (
            "Diretrizes Gerais para Resposta (aplique sempre...):\n"
            "1. **FOCO NA AÇÃO:** Sua resposta deve focar PRIMARIAMENTE no resultado direto e nas consequências imediatas da ação do jogador ('Ação atual do jogador').\n"
            "2. **CONTEXTO DO HISTÓRICO:** Use o 'Histórico recente da conversa' para entender o foco atual do jogador e dar continuidade aos eventos recentes, especialmente para ações ambíguas (ex: 'consertar', 'investigar mais', 'usar item' sem especificar alvo).\n"
            "3. **PROGRESSÃO NARRATIVA:** Faça a narrativa progredir. Ações devem ter impacto. Se um inimigo é atacado, descreva o dano e a reação de forma crível (considere 'HP do Inimigo' se em combate). Evite situações onde o estado do inimigo se 'reseta' magicamente (ex: cura instantânea de um zumbi comum) a menos que seja uma habilidade especial e rara do inimigo.\n"
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

        action_instructions += (
            "INSTRUÇÃO DE FORMATAÇÃO DA RESPOSTA:\n"
            "RESPONDA SEMPRE E APENAS com uma string JSON válida...\n"
            "- `message`: (string) Sua descrição narrativa principal da cena e do resultado da ação do jogador (em pt-br).\n"
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
            '  "message": "Você solta um grito agudo que ecoa terrivelmente pelo abrigo! O Velho Sobrevivente Cansado se encolhe e sibila: \\"Cale a boca, imbecil! Quer que todos os mortos da cidade venham bater à nossa porta?!\\". A Médica de Campo empalidece, olhando para a entrada com puro terror.",\n'
            '  "current_detailed_location": "Abrigo Subterrâneo - Sala Principal",\n'
            '  "scene_description_update": "A sala principal do abrigo é fria e úmida. A tensão é palpável após o grito; os sobreviventes estão em alerta máximo.",\n'
            '  "success": true,\n'
            '  "interpreted_action_type": "vocal_action",\n'
            '  "interpreted_action_details": {"vocal_text": "Gritar muito alto!"},\n'
            '  "interactable_elements": ["Portão de Metal Reforçado", "Enfermaria Improvisada", "Gerador Barulhento"]\n'
            "}\n"
            "```\n"
        )
        return action_instructions

    @staticmethod
    def _format_npc_details_for_prompt(npc_name: str, npc_data: Dict[str, Any]) -> str:
        """
        Formats NPC details for inclusion in a prompt.
        (Adaptado de prompt_manager.py)
        """
        # No prompt_manager, npc_data era esperado como NPCDetails TypedDict.
        # Aqui, recebemos um Dict[str, Any] de game_state.known_npcs.
        # Ajuste os acessos conforme a estrutura real de npc_data.
        profession = npc_data.get("profession", "Profissão Desconhecida")
        personality = npc_data.get("personality", "Personalidade Variada")
        # Adicione mais detalhes conforme necessário e disponível em npc_data

        npc_info_str = f"\nDetalhes sobre {npc_name}:\n"
        npc_info_str += f"- Profissão: {profession}\n"
        npc_info_str += f"- Personalidade: {personality}\n"
        knowledge_list = npc_data.get("knowledge", [])
        if isinstance(knowledge_list, list) and knowledge_list:
            npc_info_str += f"- Conhecimento: {', '.join(knowledge_list)}\n"
        return npc_info_str

    @classmethod
    def build_user_prompt_content(
        cls,
        action: str,
        details: str,
        character: CharacterType,
        game_state: GameState,
    ) -> str:
        """
        Constructs the full user prompt content by assembling various context pieces.
        """
        user_prompt_parts = []

        # Intro
        user_prompt_parts.append(
            "Você é o Mestre de um RPG de apocalipse zumbi. "
            "Mantenha o tom narrativo e imersivo em suas respostas. "
            "Os NPCs devem agir de forma lógica e consistente com suas profissões e o bom senso no contexto de sobrevivência. "
            "RESPONDA SEMPRE EM PORTUGUÊS DO BRASIL (pt-br).\n\n"
        )

        # Scene Context
        user_prompt_parts.append(cls._build_scene_context(game_state))

        # Character Context
        user_prompt_parts.append(cls._build_character_context(character))

        # Combat Context (if any)
        user_prompt_parts.append(cls._build_combat_context(game_state, action, details))

        # Recent Messages
        user_prompt_parts.append(cls._build_recent_messages_context(game_state))

        # Action Specific Instructions and Task
        current_location_name = game_state.current_location or "Desconhecido"
        user_prompt_parts.append(
            cls._build_action_specific_instructions(action, details, current_location_name, character, game_state)
            )

        return "".join(user_prompt_parts)
