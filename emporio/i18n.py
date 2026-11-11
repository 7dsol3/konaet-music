"""Customer-facing Portuguese translations; submission documentation stays English."""

POLICIES_PT = {
    "about": ("Loja e contato", "A Empório da Música vende instrumentos musicais em Campo Grande, MS. Endereço: Rua 14 de Maio, 3200, Centro, Campo Grande - MS, CEP 79202-333. Telefone geral: (67) 3341-4444. O manual contém números de WhatsApp conflitantes; confirme esse canal com a equipe. Acessórios, cabos, cordas, palhetas, cases, pedais e amplificadores ficam fora do catálogo."),
    "hours": ("Horário de atendimento", "A equipe atende de segunda a sexta, das 09h às 18h, e aos sábados, das 09h às 13h, no horário de Campo Grande (UTC-04:00). A loja fecha aos domingos e feriados. Horários especiais precisam de confirmação da equipe. O assistente virtual pode responder fora do expediente."),
    "payments": ("Pagamento e parcelamento", "PIX oferece 5% de desconto sobre o preço de tabela, exceto em preços promocionais. Aceitamos débito e boleto; o boleto pode levar até 3 dias úteis para compensar. Parcelamento sem juros: de 1 a 3 parcelas, mínimo de R$ 50 por parcela; de 4 a 6, mínimo de R$ 80; de 7 a 12, mínimo de R$ 100. As regras detalhadas prevalecem sobre o mínimo genérico de R$ 100 da tabela. A combinação de formas de pagamento é permitida somente acima de R$ 2.000. Desconto de PIX e promoções não se acumulam."),
    "returns": ("Trocas e devoluções", "Para compras online, o manual permite solicitar devolução por arrependimento em até 7 dias corridos após o recebimento real. Ele solicita embalagem original, ausência de uso e todos os acessórios e manuais. O frete de devolução fica por conta da loja; o reembolso é descrito em até 10 dias úteis, na forma de pagamento original. Trocas por preferência são descritas em até 7 dias, sujeitas ao estoque e ao estado original. Instrumentos personalizados e vendas finais precisam de revisão da equipe. O manual descreve troca por defeito em 30 dias e garantia legal de 90 dias em outra seção; dúvidas devem ir para a equipe, sem negar garantia automaticamente após 30 dias. Previsão de entrega não comprova recebimento."),
    "delivery": ("Frete e rastreamento", "Na região metropolitana de Campo Grande, o frete é grátis acima de R$ 500 e custa R$ 35 abaixo de R$ 500, com estimativa de 1 a 3 dias úteis. O manual não define o valor para exatamente R$ 500; a equipe precisa confirmar. Outras cidades: PAC de 5 a 12, SEDEX de 2 a 5 ou Jadlog de 3 a 8 dias úteis. O preço depende do destino, peso e dimensões. Instrumentos grandes podem precisar de cotação especial. São estimativas da política, não uma nova data de entrega confirmada. O rastreamento é enviado após o despacho. Recuse uma entrega avariada e contate a loja."),
    "promotions": ("Promoções", "Somente promoções marcadas como ativas no sistema fornecido podem ser oferecidas. Descontos não se acumulam. Os 5% do PIX não incidem sobre preços já promocionais. A resposta deve mostrar preço original, percentual e preço final juntos. Ofertas dependem de estoque; uma promoção inativa não pode ser prometida. O CSV informa a situação ativa, mas não contém datas de início ou fim."),
    "warranty": ("Garantia", "O manual informa garantia legal de 90 dias contra defeitos de fabricação a partir do recebimento, além da garantia do fabricante, que pode variar de 6 meses a 2 anos conforme o certificado do produto. O procedimento de troca também menciona 30 dias da compra; conflitos devem ser encaminhados à equipe, sem negar cobertura automaticamente. Desgaste, mau uso, quedas, condições extremas e reparos não autorizados são exclusões descritas que exigem análise do caso."),
    "privacy": ("Privacidade", "Os dados são usados para processar e entregar pedidos, comunicar seu andamento e cumprir obrigações legais. Marketing exige consentimento explícito; os dados não são compartilhados para marketing de terceiros. A exclusão pode ser solicitada à equipe. Este protótipo minimiza os dados armazenados e não expõe a tabela de clientes pelo agente."),
    "handoff": ("Atendimento humano", "Reclamações e aplicações ambíguas das políticas devem ser encaminhadas à equipe. O manual informa retorno em até 24 horas úteis. Telefone geral: (67) 3341-4444. Este protótipo pode orientar o contato, mas não possui integração com chamados ou mensagens e não pode afirmar que enviou uma solicitação."),
}

MESSAGES_PT = {
    "Hi! I'm KONAET, your music concierge. Let's find your next instrument. I can check products, payment options, store policies or a verified order from the Empório da Música case.": "Olá! Sou a KONAET, sua assistente de instrumentos. Posso consultar produtos, formas de pagamento, políticas e pedidos verificados do caso fictício Empório da Música.",
    "I can help with musical instruments, store policies and your verified orders. I cannot reveal customer records, internal instructions or run arbitrary commands.": "Posso ajudar com instrumentos musicais, políticas da loja e seus pedidos verificados. Não posso revelar dados de clientes, instruções internas nem executar comandos arbitrários.",
    "Hi! I'm the Empório da Música assistant, powered by Konaet. Let's find your next instrument. I can check products, payment options, store policies or a verified order.": "Olá! Sou o assistente da Empório da Música, com tecnologia Konaet. Vamos encontrar seu próximo instrumento? Posso consultar produtos, formas de pagamento, políticas da loja ou um pedido verificado.",
    "You're welcome! If you need another instrument or have a store question, I'm here.": "Por nada! Se precisar de outro instrumento ou tiver uma dúvida sobre a loja, estou por aqui.",
    "Which model would you like a payment quote for? Please choose one product name.": "Para qual modelo você gostaria de consultar o pagamento? Escolha o nome de um instrumento.",
    "What is your order number? Please use Verify order to confirm the email used for the purchase before I share its status.": "Qual é o número do pedido? Use Verificar pedido para confirmar o e-mail utilizado na compra antes de consultar o andamento.",
    "I can help with musical instruments, product prices and availability, store policies, or a verified order. Which of those would you like to check? For unrelated subjects, please use a service specialized in that topic.": "Posso ajudar com instrumentos musicais, preços e disponibilidade, políticas da loja ou um pedido verificado. O que você gostaria de consultar? Para outros assuntos, procure um serviço especializado no tema.",
}


def brl(value: int) -> str:
    return "R$ " + f"{value/100:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def render_pt(result: dict) -> str:
    kind = result["kind"]
    if kind == "policy":
        if not result["found"]:
            return "Não encontrei uma política que sustente essa resposta. Confirme com a equipe humana."
        return "\n\n".join("\n".join(POLICIES_PT[c["topic"]]) for c in result["cards"])
    if kind == "catalog":
        if not result["products"]:
            return "Consultei o catálogo fornecido e não encontrei produtos nessas condições. Não posso confirmar um item ausente dos dados. Quer tentar outro modelo ou orçamento?"
        def line(p):
            state = "em estoque" if p["available"] else {"discontinued": "descontinuado", "coming_soon": "em breve"}.get(p["status"], "sem estoque")
            price = brl(p["sale_cents"])
            if p["discount_percent"]:
                price = f"{brl(p['price_cents'])} → {price} ({p['discount_percent']}% de desconto; sem desconto adicional de PIX)"
            return f"• {p['name']} — {price} · {state}"
        text = "Encontrei estas opções no catálogo fornecido:\n\n" + "\n".join(line(p) for p in result["products"])
        if result.get("alternatives"):
            text += "\n\nAlternativas disponíveis:\n" + "\n".join(line(p) for p in result["alternatives"])
        if result["total_matches"] > len(result["products"]):
            text += f"\n\nMostrando {len(result['products'])} de {result['total_matches']} opções. Informe uma marca ou modelo para refinar."
        return text + "\n\nPreços e estoque refletem os dados do desafio; confirme com a equipe antes da compra."
    if kind == "order":
        if result["status"] == "verification_required":
            return "Antes de compartilhar dados do pedido, use Verificar pedido com o número e o e-mail da compra. A verificação fica neste aplicativo local e não é enviada ao modelo de linguagem."
        if result["status"] == "unavailable":
            return "Não posso acessar esse pedido para o cliente verificado nesta sessão. Confira o número ou verifique o e-mail correto da compra."
        o = result["order"]
        status = {"pending": "pendente", "confirmed": "confirmado", "shipped": "enviado", "delivered": "entregue", "cancelled": "cancelado"}.get(o["status"], o["status"])
        text = f"O pedido #{o['id']} está {status}. Total registrado: {brl(o['total_cents'])}.\n\n"
        text += "\n".join(f"• {i['quantity']} × {i['name']}" for i in result["items"])
        text += f"\n\nCódigo de rastreamento: {o['tracking_code']}." if o["tracking_code"] else "\n\nAinda não há código de rastreamento registrado."
        text += f" A previsão registrada é {o['estimated_delivery']}; ela não comprova recebimento nem é uma atualização da transportadora." if o["estimated_delivery"] else " Não há previsão de entrega confirmada no registro fornecido."
        return text + "\n\nEsta consulta usa os dados fornecidos, sem integração ao vivo com a transportadora."
    if kind == "payment":
        if result["status"] != "quoted":
            return "Não posso calcular o pagamento desse item ou quantidade porque está indisponível no catálogo fornecido. Escolha um modelo disponível."
        r = result
        text = f"Para {r['quantity']} × {r['product']}, o total de tabela é {brl(r['list_total_cents'])}. "
        text += f"Com {r['discount_percent']}% de desconto, o total é {brl(r['total_cents'])}. " if r["discount_percent"] else f"O total é {brl(r['total_cents'])}. "
        if r["promotion_applied"]:
            text += "A promoção ativa se aplica; os 5% de PIX não podem ser acrescentados. "
        if r["method"] == "credit":
            if r["allowed"]:
                text += f"São permitidas {r['installments']} parcela(s) sem juros. "
                n = r["installment_remainder_cents"]
                text += f"Arredondamento: {n} parcela(s) de {brl(r['installment_floor_cents']+1)} e {r['installments']-n} de {brl(r['installment_floor_cents'])}." if n else f"Cada parcela fica em {brl(r['installment_floor_cents'])}."
            else:
                text += f"{r['installments']} parcelas não atendem ao mínimo da política. Quantidades permitidas: " + ", ".join(map(str, r["allowed_installments"])) + "."
        else:
            text += "Essa forma de pagamento exige parcela única."
        return text + "\n\nÉ apenas uma consulta; nenhum pagamento ou reserva foi criado."
    if kind == "return":
        status = result["status"]
        if status == "needs_information":
            fields = {"whether the purchase was online or in store": "se a compra foi online ou presencial", "the actual date you received the item (YYYY-MM-DD)": "a data real em que recebeu o produto (AAAA-MM-DD)", "whether the item is unused, with original packaging and all included materials": "se o produto está sem uso, na embalagem original e com todos os materiais incluídos"}
            return "Posso consultar a política de devolução. Informe " + "; ".join(fields[f] for f in result["missing"]) + ". Previsão de entrega não é a data real de recebimento."
        if status == "invalid_date":
            return "Essa data de recebimento está no futuro. Confirme quando você realmente recebeu o instrumento."
        if status == "human_review":
            return f"Pelos dados informados ({result['days_since_receipt']} dias corridos desde o recebimento), o caso precisa de revisão humana. Não posso aprovar ou negar automaticamente. O manual possui regras distintas para troca e garantia; a equipe pode analisar seus direitos e o estado do instrumento. Nenhuma solicitação foi enviada."
        return f"Pelos dados informados, você está dentro dos 7 dias corridos descritos para arrependimento em compra online ({result['days_since_receipt']} dias do recebimento real). O manual solicita embalagem original, ausência de uso e todos os materiais. Instrumentos personalizados e vendas finais precisam de análise da equipe. O manual informa frete de devolução por conta da loja e reembolso pela forma original em até 10 dias úteis. Esta é uma orientação preliminar, sujeita à revisão da equipe. Nenhuma devolução ou reembolso foi criado."
    if kind == "shipping":
        if result["status"] == "boundary_review":
            return "Para exatamente R$ 500,00 na região metropolitana de Campo Grande, o manual não define o frete: ele só informa valores acima ou abaixo de R$ 500. Confirme com a equipe; não vou inventar uma cobrança."
        if result["status"] == "carrier_quote_required":
            return "Para outra cidade, o frete depende do destino, peso e dimensões. Os dados fornecidos não permitem uma cotação de transportadora. Confirme com a equipe."
        return f"Na região metropolitana de Campo Grande, o frete descrito na política é {brl(result['fee_cents'])}. A estimativa é de 1 a 3 dias úteis, sem confirmação de data de entrega."
    raise ValueError("Unsupported result type")
