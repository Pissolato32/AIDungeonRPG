# filepath: c:\Users\rodri\Desktop\REPLIT RPG\ai\game_ai_client.py
"""Game AI client module.

This module handles AI model interactions for generating game content
and responses."""

import logging
from typing import Any, Dict, List, Optional, TypedDict, cast, Protocol

from core.game_state_model import GameState

logger = logging.getLogger(__name__)


class AIPrompt(TypedDict):
    """Type definition for AI prompt data."""

    role: str
    content: str


class AIResponse(TypedDict):
    """Type definition for AI response data."""

    success: bool
    message: str
    current_detailed_location: str
    scene_description_update: str
    details: Dict[str, Any]  # Detalhes gerais da IA ou do processamento
    error: Optional[str]
    interpreted_action_type: Optional[str]  # Novo: Ação interpretada pela IA
    interpreted_action_details: Optional[
        Dict[str, Any]
    ]  # Novo: Detalhes da ação interpretada
    interactable_elements: Optional[List[str]]  # Novo: Elementos interativos na cena


# Define Protocols for external dependencies
class AIModelClientType(Protocol):
    """Protocol for AI model clients that can generate text responses."""

    def generate_response(self, prompt_data: AIPrompt) -> str:
        """Generates a response from the AI model based on the prompt.

        Args:
            prompt_data: The prompt to send to the AI.

        Returns:
            The raw string response from the AI (e.g., a JSON string).
        """
        ...


class CharacterAttributes(TypedDict, total=False):
    """Expected structure for character attributes relevant to the AI.
    `total=False` allows other attributes to exist without being typed here."""

    current_hp: int
    max_hp: int


class CharacterType(Protocol):
    """Protocol for character objects passed to the AI client."""

    name: str
    level: int
    attributes: Dict[str, Any]  # Alterado para compatibilidade


class GameAIClient:
    """Client for handling AI model interactions in the game."""

    def __init__(self, ai_client: Optional[AIModelClientType] = None) -> None:
        """Initialize the Game AI Client."""
        self.ai_client = ai_client

    @staticmethod
    def _create_action_prompt(
        action: str, details: str, character: CharacterType, game_state: GameState
    ) -> AIPrompt:
        """Create a formatted prompt for the AI model.

        Args:
            action: Type of action being performed
            details: Additional action details
            character: Player character data
            game_state: Current game state

        Returns:
            Formatted prompt for the AI model
        """
        location = game_state.current_location or "Desconhecido"  # Traduzido
        recent_messages = game_state.messages[-5:] if game_state.messages else []

        # Tenta obter dados da localização atual de discovered_locations
        # Se não encontrar, usa os valores de game_state diretamente
        loc_data = game_state.discovered_locations.get(
            game_state.location_id, {}  # type: ignore
        )  # Usa location_id
        current_scene_description = loc_data.get(
            "description", game_state.scene_description  # type: ignore
        )
        npcs_in_current_loc = loc_data.get("npcs", game_state.npcs_present)
        events_in_current_loc = loc_data.get("events", game_state.events)

        state_dict = {
            "current_location": location,  # Este é o nome amigável
            "scene_description": current_scene_description,
            "npcs_present": npcs_in_current_loc,
            "events": events_in_current_loc,
            "messages": recent_messages,
        }

        prompt = (
            "Você é o Mestre de um RPG de apocalipse zumbi. "
            "Mantenha o tom narrativo e imersivo em suas respostas. "
            "Os NPCs devem agir de forma lógica e consistente com suas profissões e o bom senso no contexto de sobrevivência. "
            "RESPONDA SEMPRE EM PORTUGUÊS DO BRASIL (pt-br).\n\n"
        )

        prompt += (
            f"Local atual: {state_dict['current_location']}\n"
            f"Descrição da cena: {state_dict['scene_description']}\n"
        )

        npcs = state_dict["npcs_present"]
        npcs_text = ", ".join(npcs) if npcs else "Nenhum"
        prompt += f"NPCs presentes: {npcs_text}\n"

        events = state_dict["events"]
        events_text = ", ".join(events) if events else "Nenhum"
        prompt += f"Eventos ativos: {events_text}\n\n"

        prompt += (
            "Personagem do jogador:\n"
            f"- Nome: {character.name}\n"
            f"- Nível: {character.level}\n"
            # Acessando HP de attributes, que é um dicionário
            f"- HP: {character.attributes.get('current_hp', 0)}/{character.attributes.get('max_hp', 0)}\n\n"
        )

        if (
            hasattr(game_state, "combat")
            and game_state.combat
            and game_state.combat.get("enemy")
        ):
            enemy_data = game_state.combat.get("enemy")
            # Assuming enemy_data is a dictionary, consistent with combat_system.py
            # The comment "# enemy_data é um objeto Enemy" might be misleading if
            # game_state.combat stores enemy data as dicts.
            if isinstance(enemy_data, dict):
                enemy_name = enemy_data.get("name", "Inimigo Desconhecido")
                enemy_health = enemy_data.get("health", 0)
                # Assuming "max_health" might not always be present in enemy dicts
                enemy_max_health = enemy_data.get(
                    "max_health", enemy_data.get("health", 0)
                )
                prompt += (
                    "Informações do Combate Atual:\n"
                    f"- Inimigo: {enemy_name}\n"
                    f"- HP do Inimigo: {enemy_health}/{enemy_max_health}\n"
                )
                if (  # Se a ação é 'attack' e 'details' contém um resultado de ataque
                    action.lower() == "attack"
                    and details
                    and (
                        "acertou" in details.lower()
                        or "errou" in details.lower()
                        or "derrotou" in details.lower()
                    )
                ):  # Adiciona o resultado do último ataque do jogador ao prompt
                    prompt += f"- Resultado do último ataque do jogador: {details}\n\n"
                else:  # Adiciona uma nova linha se não houver resultado de ataque para adicionar
                    prompt += "\n"

        if recent_messages:
            messages_text = "\n".join([f"- {msg}" for msg in recent_messages])
            prompt += (
                f"Histórico recente da conversa (para contexto):\n{messages_text}\n\n"
            )
        # Lógica principal para interpretação de ação ou ação direta
        # Assumindo que 'interpret' será o novo 'action' padrão vindo do GameEngine para entrada de texto livre
        if (
            action.lower() == "interpret" or action.lower() == "custom"
        ):  # Unificando 'custom' para ser interpretativo
            prompt += (
                f"Ação textual do jogador (interprete a intenção): {details}\n\n"
                "SUA TAREFA PRINCIPAL:\n"
                "1. INTERPRETE A INTENÇÃO: Analise a 'Ação textual do jogador' para determinar a intenção principal. Categorize-a como uma das seguintes: 'move', 'look', 'talk' (tentativa de diálogo), 'vocal_action' (para gritos, canções, etc., que não são diálogos diretos), 'search', 'use_item', 'attack', 'flee', 'rest', 'skill', 'craft', 'custom_complex' (para ações complexas ou não listadas que exigem narração criativa).\n"
                "2. GERE A NARRATIVA: Com base na intenção interpretada, narre o resultado da ação como Mestre do Jogo. Aplique as 'Diretrizes Gerais para Resposta' e, se a intenção corresponder a uma das ações com 'SUB-DIRETRIZES PARA INTENÇÕES ESPECÍFICAS' abaixo, aplique essas sub-diretrizes também.\n"
                "3. INCLUA INTERPRETAÇÃO NO JSON: No seu JSON de resposta, além dos campos padrão, inclua 'interpreted_action_type' (a categoria que você escolheu) e 'interpreted_action_details' (um dicionário com parâmetros relevantes, ex: {'direction': 'norte'} para 'move', {'target_npc': 'NomeDoNPC'} para 'talk', {'item_name': 'Bandagem'} para 'use_item', {'vocal_text': 'Gritar muito alto'} para 'vocal_action').\n\n"
            )
        else:  # Mantém a lógica antiga para ações diretas, se necessário, ou pode ser removido gradualmente
            prompt += f"Ação atual do jogador (direta): {action}"
            if details:
                prompt += f" (Detalhes: {details})"
            prompt += "\n\n"

        prompt += "SUB-DIRETRIZES PARA INTENÇÕES ESPECÍFICAS (aplique se relevante para a intenção que você interpretou ou para a ação direta fornecida):\n"

        prompt += (
            "INTENÇÃO 'search': Descreva o que o personagem encontra (ou não encontra) com base no ambiente e nos detalhes da busca. "
            "Seja criativo e considere o que faria sentido encontrar em um local como este. "
            "Pode ser algo útil, inútil, perigoso, ou apenas pistas sobre o que aconteceu.\n\n"
        )
        prompt += (
            "INTENÇÃO 'look': Se houver um alvo específico nos detalhes da ação do jogador, descreva em detalhes o que o personagem observa sobre esse alvo. "
            "Forneça informações visuais, pistas ou qualquer coisa relevante. Se for um olhar geral ao ambiente, reitere ou atualize a descrição da cena.\n\n"
        )
        prompt += (
            "INTENÇÃO 'move': Descreva a transição para o novo local ou a tentativa de movimento. "
            "Se o movimento for para um local conhecido, reforce a descrição com novos detalhes ou mudanças. "
            "Se for uma tentativa de ir a um local desconhecido ou bloqueado, descreva o obstáculo ou a razão pela qual o movimento não é simples.\n\n"
        )
        prompt += (
            "INTENÇÕES 'talk' (diálogo) ou 'vocal_action' (ação vocal genérica):\n"
            "   Se a intenção for 'talk' (tentativa de conversa direta com um NPC específico):\n"
            "     Gere a resposta ou o início do diálogo do NPC alvo. Considere a personalidade do NPC, sua profissão, o estado atual do mundo e o que ele poderia querer ou saber. A resposta do NPC deve ser útil ou, pelo menos, crível. A conversa deve parecer natural e pode revelar informações, missões ou perigos.\n"
            "   Se a intenção for 'vocal_action' (ex: 'Gritar MUITO ALTO', 'Sussurrar', 'Chamar por ajuda', 'Cantar uma música triste') e NÃO uma tentativa de conversa direta com um NPC:\n"
            "     - Primeiro, RESPEITE a intensidade da ação vocal descrita pelo jogador. Se o jogador diz 'Gritar MUITO ALTO', o som É muito alto e perceptível. Não o atenue ou descreva como 'amortecido' arbitrariamente, a menos que o ambiente (ex: dentro de um cofre à prova de som que o jogador conhece) justifique explicitamente e o jogador já tenha essa informação contextual.\n"
            "     - Descreva o efeito físico imediato dessa ação no ambiente (ex: o som ecoa agudamente, poeira cai do teto, objetos próximos vibram).\n"
            "     - Em seguida, conecte IMEDIATAMENTE esta ação à diretriz geral '11. CONSEQUÊNCIAS DE RUÍDO'. As reações dos NPCs DEVEM refletir o perigo de atrair atenção indesejada (zumbis, saqueadores). Eles devem parecer visivelmente alarmados, podem repreender o jogador com urgência (ex: 'Você quer nos matar?! Fique quieto!'), gesticular freneticamente por silêncio, olhar nervosamente para as saídas, ou até mesmo se preparar para um possível ataque/invasão. Evite que os NPCs iniciem um diálogo casual ou façam perguntas simples como 'O que foi isso?'. Suas reações devem ser de medo, raiva pela imprudência, ou pânico.\n"
            "     - O foco da sua narrativa deve ser na tensão criada, no perigo iminente percebido, e na reação de alerta/pânico dos NPCs, não em iniciar uma nova conversa. A reação deve ser natural para sobreviventes experientes (ou apavorados) em um mundo hostil.\n"
            "   Se a intenção for 'talk' mas sem detalhes ou alvo claro (jogador apenas indicou querer falar):\n"
            "     Descreva se algum NPC próximo toma a iniciativa de falar com o jogador, ou se o ambiente permanece em silêncio aguardando uma ação mais específica. Se houver NPCs, um deles pode perguntar 'Você disse alguma coisa?' ou 'Precisa de algo?'.\n"
            "   Se os detalhes para 'talk' ou 'vocal_action' forem vagos ou sem sentido, aplique a diretriz geral '9. AÇÕES OU DETALHES IMPRECISOS/IRRELEVANTES'.\n\n"
        )
        prompt += (
            "INTENÇÃO 'use_item': Descreva o resultado de usar o item especificado. Se for um consumível, descreva a sensação ou efeito. "
            "Se for uma ferramenta, descreva a ação e seu sucesso ou falha. "
            "Se for um item de quest, revele alguma informação ou consequência.\n\n"
        )
        prompt += "INTENÇÃO 'attack': Se não houver combate ativo, descreva o jogador se preparando para o combate ou atacando o alvo especificado (ou o mais óbvio), iniciando a confrontação. Se o combate já estiver ativo, descreva o resultado do ataque contra o inimigo atual.\n\n"
        prompt += (
            "INTENÇÃO 'flee': Descreva a tentativa de fuga. Foi bem-sucedida? Houve perigos ou obstáculos? "
            "A fuga levou o personagem a uma situação melhor ou pior? "
            "Mantenha a tensão e o realismo do apocalipse zumbi.\n\n"
        )
        prompt += (
            "INTENÇÃO 'rest': Descreva a tentativa de descanso. O local é seguro o suficiente? "
            "O personagem consegue realmente descansar ou é interrompido? Quais são os riscos? "
            "Descreva quaisquer efeitos de recuperação ou, ao contrário, a impossibilidade de descansar devido ao perigo.\n\n"
        )
        prompt += (
            "INTENÇÃO 'custom_complex' ou outras não listadas: Interprete esta ação no contexto do jogo de apocalipse zumbi. "
            "Descreva o resultado da ação do jogador de forma criativa e coerente com o ambiente e a situação. "
            "Considere as possíveis consequências, sucessos ou falhas.\n\n"
        )

        prompt += (
            "Diretrizes Gerais para Resposta (aplique sempre, independentemente da intenção interpretada):\n"
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
            "12. **ELEMENTOS INTERATIVOS:** Ao descrever uma `current_detailed_location` e sua `scene_description_update`, identifique de 2 a 4 elementos, objetos ou pequenas áreas de interesse chave DENTRO dessa sub-localização específica. Liste os nomes desses elementos no campo `interactable_elements` da sua resposta JSON. Estes são itens que o jogador poderia querer examinar mais de perto ou interagir. Mantenha os nomes concisos e diretos (ex: 'Mesa de Operações', 'Armário de Remédios', 'Cama de Paciente').\n"
            "INSTRUÇÃO DE FORMATAÇÃO DA RESPOSTA:\n"
            "RESPONDA SEMPRE E APENAS com uma string JSON válida contendo os seguintes campos, E TODO O TEXTO GERADO DEVE ESTAR EM PORTUGUÊS DO BRASIL (pt-br):\n"
            "- `message`: (string) Sua descrição narrativa principal da cena e do resultado da ação do jogador (em pt-br).\n"
            "- `current_detailed_location`: (string) O nome detalhado da localização atual do jogador, incluindo a sub-área específica dentro do local principal (ex: 'Abrigo Subterrâneo - Sala Principal', 'Floresta Sombria - Clareira Escondida'). Se o jogador se mover para um novo local principal (ex: de 'Floresta' para 'Abrigo Subterrâneo'), determine um ponto de entrada lógico para este novo local principal (ex: 'Pátio de Entrada', 'Corredor de Acesso', 'Garagem Empoeirada') e use-o como a sub-área em `current_detailed_location` (ex: 'Abrigo Subterrâneo - Pátio de Entrada'). (em pt-br)\n"
            "- `scene_description_update`: (string) Uma nova descrição concisa para a cena/sub-área atual (o `current_detailed_location`), focando nos elementos estáticos e ambientais importantes que o jogador perceberia. (em pt-br)\n"
            "- `success`: (boolean) Sempre `true` se você puder gerar uma resposta narrativa. Use `false` apenas em caso de um erro interno seu ao processar o pedido (o que deve ser raro).\n\n"
            "- `interpreted_action_type`: (string, opcional mas PREFERÍVEL) A categoria da intenção que você interpretou (ex: 'move', 'talk', 'vocal_action', 'search', 'custom_complex').\n"
            "- `interpreted_action_details`: (object, opcional mas PREFERÍVEL) Um dicionário com parâmetros relevantes para a ação interpretada (ex: {'direction': 'norte'}, {'target_npc': 'NomeDoNPC'}, {'item_name': 'Bandagem', 'vocal_text': 'Gritar muito alto'}).\n\n"
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

        return AIPrompt(role="user", content=prompt)

    def process_action(
        self, action: str, details: str, character: CharacterType, game_state: GameState
    ) -> AIResponse:
        """Process a player action using AI.

        Args:
            action: Type of action being performed
            details: Additional action details
            character: Player character data
            game_state: Current game state

        Returns:
            AI response containing action results
        """
        logger.info(f"GameAIClient process_action called for: {action} - {details}")
        if not self.ai_client:
            logger.error(
                "AI client (e.g., GroqClient) not initialized in GameAIClient."
            )
            return AIResponse(
                success=False,
                message="Erro de configuração: O cliente de IA não está disponível.",
                error="No AI client available",
                # Ensure all required fields of AIResponse are present
                current_detailed_location=game_state.current_location
                or "Indisponível (Erro de Config.)",
                scene_description_update=game_state.scene_description
                or "Indisponível (Erro de Config.)",
                details={},
                interpreted_action_type=None,
                interpreted_action_details=None,
                interactable_elements=None,
            )

        try:
            prompt_data = self._create_action_prompt(
                action, details, character, game_state
            )
            logger.debug(
                f"Generated AI Prompt (first 500 chars): {prompt_data['content'][:500]}"
            )

            response_from_ai_service = self.ai_client.generate_response(prompt_data)
            logger.debug(
                f"Raw response from AI service type: {type(response_from_ai_service)}, content: {str(response_from_ai_service)[:500]}"
            )

            from .response_processor import process_ai_response

            parsed_ai_dict = process_ai_response(response_from_ai_service)
            logger.info(f"Parsed AI response dictionary: {parsed_ai_dict}")

            if not isinstance(parsed_ai_dict, dict):
                logger.error(
                    f"process_ai_response did not return a dict: {parsed_ai_dict}"
                )
                return AIResponse(
                    success=False,
                    message="Falha interna ao processar a resposta da IA.",
                    error="Formato de resposta inesperado do processador.",
                    current_detailed_location=game_state.current_location
                    or "Localização Indefinida",
                    scene_description_update=game_state.scene_description
                    or "A cena permanece como antes.",
                    details={},
                    interpreted_action_type=None,
                    interpreted_action_details=None,
                    interactable_elements=None,
                )

            # Extrair valores do parsed_ai_dict, preparando para fallbacks
            is_successful = parsed_ai_dict.get("success", False)
            ai_message_val = parsed_ai_dict.get("message")  # Pode ser str ou None
            ai_error_val = parsed_ai_dict.get("error")  # Pode ser str ou None
            ai_current_loc_val = parsed_ai_dict.get(
                "current_detailed_location"
            )  # Pode ser str ou None
            ai_scene_update_val = parsed_ai_dict.get(
                "scene_description_update"
            )  # Pode ser str ou None

            # Determinar final_message garantindo que seja sempre uma string
            if is_successful:
                final_message_str = (
                    ai_message_val
                    or "A ação foi processada, mas a IA não forneceu uma narrativa detalhada."
                )
            else:
                # Se não for bem-sucedido, a mensagem deve refletir o erro.
                # Priorizar a mensagem da IA, depois o detalhe do erro da IA, depois um fallback.
                final_message_str = (
                    ai_message_val
                    or ai_error_val
                    or "Falha ao processar a resposta da IA."
                )

            # Garantir que current_detailed_location seja sempre uma string
            final_current_detailed_location_str = (
                ai_current_loc_val
                or game_state.current_location
                or "Localização Indefinida"
            )

            # Garantir que scene_description_update seja sempre uma string
            final_scene_description_update_str = (
                ai_scene_update_val
                or game_state.scene_description
                or "A cena permanece como antes."
            )

            # Garantir que details seja um dict
            details_data = parsed_ai_dict.get("details")
            if not isinstance(details_data, dict):
                details_data = {}

            # Construir o AIResponse garantindo a conformidade dos tipos
            response_data: AIResponse = {
                "success": is_successful,
                "message": final_message_str,
                "current_detailed_location": final_current_detailed_location_str,
                "scene_description_update": final_scene_description_update_str,
                "details": details_data,
                "error": ai_error_val if not is_successful else None,
                "interpreted_action_type": parsed_ai_dict.get(
                    "interpreted_action_type"
                ),
                "interactable_elements": parsed_ai_dict.get("interactable_elements"),
                "interpreted_action_details": parsed_ai_dict.get(
                    "interpreted_action_details"
                ),
            }

            logger.info(f"Final AIResponse data: {response_data}")
            return response_data  # O cast pode não ser mais estritamente necessário se o mypy inferir corretamente

        except Exception as e:
            logger.error(
                f"Error processing action '{action}' with AI: {e}", exc_info=True
            )
            error_message_lower = str(e).lower()

            # Construct an AIResponse compliant error object
            error_response: AIResponse = {
                "success": False,
                "message": "Falha ao processar a ação através da IA.",
                "error": str(e),
                "current_detailed_location": game_state.current_location
                or "Localização Indefinida",
                "scene_description_update": game_state.scene_description
                or "A cena permanece como antes.",
                "details": {},
                "interpreted_action_type": None,
                "interpreted_action_details": None,
                "interactable_elements": None,
            }
            if (
                "unavailable" in error_message_lower
                or "temporarily" in error_message_lower
                or "indisponível" in error_message_lower
            ):
                error_response["message"] = (
                    "A inteligência artificial está temporariamente indisponível. Tente novamente mais tarde."
                )
            return error_response
