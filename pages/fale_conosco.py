import streamlit as st
import re
from utils.common import enviar_email

def render_fale_conosco():
    """
    Renderiza a página de formulário de contato "Fale Conosco".
    """
    # Adicionando um estilo para a borda arredondada do formulário
    st.markdown(
        """
        <style>
        div[data-testid="stForm"] {
            border: 1px solid #e6e6e6;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            background: #ffffff;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("✉️ Fale Conosco")
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #f0f4f8 0%, #d9e2eb 100%); border-radius: 12px; padding: 20px; border-left: 4px solid #228B22; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 20px;">
            <p style="font-family: 'Segoe UI', Roboto, sans-serif; color: #2c3e50; font-size: 16px; line-height: 1.6; margin: 0;">
                Preencha o formulário abaixo para entrar em contato com o Comitê de Bacia. Seus dados e a sua mensagem são muito importantes para nós.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form(key="contact_form", clear_on_submit=True):
        st.subheader("1. Dados Pessoais/Institucionais")
        
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome Completo (obrigatório)")
            email = st.text_input("E-mail (obrigatório)")
        with col2:
            telefone = st.text_input("Telefone/Celular (opcional)", help="Ex: (85) 91234-5678")
            cpf_cnpj = st.text_input("CPF/CNPJ (opcional)", help="Para demandas institucionais.")
        
        cidade_estado = st.text_input("Cidade/Estado (obrigatório)")

        # Validação simples de e-mail
        email_valido = False
        if email:
            if re.match(r"[^@]+@[^@]+\.[^@]+", email):
                email_valido = True
            else:
                st.error("Por favor, insira um e-mail válido.")

        st.markdown("---")
        st.subheader("2. Tipo de Contato")
        tipo_contato = st.radio(
            "Selecione o motivo do contato (obrigatório)",
            ("Solicitação de informação", "Denúncia/reclamação ambiental",
             "Sugestão para a gestão da bacia", "Proposta de parceria/projeto",
             "Imprensa/assessoria de comunicação", "Outro"),
            key="tipo_contato"
        )
        outro_contato = st.text_input("Especifique o tipo de contato:", key="outro_contato_field") if tipo_contato == "Outro" else ""

        st.markdown("---")
        st.subheader("3. Mensagem")
        assunto = st.text_input("Assunto (obrigatório)", help="Ex: 'Poluição no Rio X'")
        descricao = st.text_area("Descrição detalhada (obrigatório)", max_chars=2000, height=200)

        st.markdown("---")
        st.subheader("4. Anexos (opcional)")
        anexos = st.file_uploader(
            "Envie documentos ou imagens relevantes",
            type=["pdf", "jpg", "jpeg", "png"],
            accept_multiple_files=True
        )

        st.markdown("---")
        st.subheader("5. Canal de Resposta Preferencial")
        canal_resposta = st.radio(
            "Por onde você prefere ser contatado?",
            ("E-mail", "Telefone", "Correio físico"),
            key="canal_resposta"
        )

        st.markdown("---")
        st.subheader("6. Autorizações")
        lgpd_consentimento = st.checkbox(
            "Concordo com o tratamento dos dados pessoais conforme a LGPD.",
            help="[Clique aqui para ler nossa política de privacidade.](https://www.cbhbanabuiu.com.br/politica-de-privacidade)",
            key="lgpd_consentimento"
        )
        receber_informativos = st.checkbox(
            "Desejo receber informativos sobre o Comitê (opcional)",
            key="receber_informativos"
        )

        submit_button = st.form_submit_button("Enviar Mensagem")

    if submit_button:
        if not nome or not email or not cidade_estado or not assunto or not descricao or not lgpd_consentimento or not email_valido:
            st.error("Por favor, preencha todos os campos obrigatórios e aceite os termos da LGPD.")
        else:
            dados_formulario = {
                "nome": nome,
                "email": email,
                "telefone": telefone,
                "cpf_cnpj": cpf_cnpj,
                "cidade_estado": cidade_estado,
                "tipo_contato": tipo_contato,
                "outro_contato": outro_contato,
                "assunto": assunto,
                "descricao": descricao,
                "canal_resposta": canal_resposta,
                "lgpd_consentimento": lgpd_consentimento,
                "receber_informativos": receber_informativos
            }
            
            # Substitua pelo e-mail de destino correto
            email_destino = "o_email_que_recebera@comite.org.br"
            
            if enviar_email(dados_formulario, email_destino):
                st.success("Sua mensagem foi enviada com sucesso! Agradecemos o seu contato.")
            else:
                st.error("Houve um problema ao enviar sua mensagem. Por favor, tente novamente mais tarde.")
